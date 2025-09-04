import os
import math
import json
import time
import datetime as dt
from typing import Dict, Any, Optional, Tuple

import requests

GRAMS_PER_TROY_OUNCE = 31.1034768

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    )
}

# ---------- HTTP helpers ----------

def _request_with_retries(method: str, url: str, *, max_retries: int = 5, backoff_base: float = 0.6,
                          expected_json: bool = True, **kwargs):
    headers = kwargs.pop("headers", {}) or {}
    headers = {**DEFAULT_HEADERS, **headers}
    for attempt in range(max_retries):
        resp = requests.request(method, url, headers=headers, timeout=25, **kwargs)
        if resp.status_code < 400:
            if expected_json:
                return resp.json()
            return resp.text
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
            ra = resp.headers.get("Retry-After")
            delay = float(ra) if ra and ra.isdigit() else backoff_base * (2 ** attempt)
            time.sleep(delay)
            continue
        resp.raise_for_status()

def http_get_json(url, params=None, headers=None):
    return _request_with_retries("GET", url, params=params, headers=headers)

def http_post_json(url, payload, headers=None):
    return _request_with_retries("POST", url, json=payload, headers=headers)

def send_telegram_message(token: str, chat_id: str, text: str, parse_mode: Optional[str] = None):
    api = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
        payload["disable_web_page_preview"] = True
    r = requests.post(api, json=payload, headers=DEFAULT_HEADERS, timeout=25)
    if not r.ok:
        raise RuntimeError(f"Telegram send failed: {r.status_code} {r.text}")

# ---------- Helpers for instrument matching ----------

def _norm(s: str) -> str:
    if s is None:
        return ""
    t = s.upper()
    t = t.replace("(T+D)", "TD").replace("T+D", "TD").replace("(TD)", "TD").replace("+", "")
    for ch in [" ", "_", "-", ".", "/", "\\"]:
        t = t.replace(ch, "")
    return t

def _row_text(row: Dict[str, Any]) -> str:
    return _norm(" ".join(str(v) for v in (row or {}).values() if v is not None))

def _match_instrument_row(row: Dict[str, Any], target: str) -> bool:
    txt = _row_text(row)
    tgt = _norm(target)
    if tgt == "AU9999":
        return "AU9999" in txt or "AU99.99" in txt
    if tgt in {"AUTD"}:
        return "AUTD" in txt or "AUT+D" in txt
    return tgt in txt

def _display_label(instr: str) -> str:
    u = (instr or "").upper()
    if u in {"AUTD"}:
        return "Au+TD"
    if u in {"AU9999"}:
        return "Au9999"
    return instr

# ---------- Step 1: SGE ----------

def fetch_sge_from_xwteam(instrument: str = "AU9999", mode: str = "SP") -> float:
    url = "https://free.xwteam.cn/api/gold/trade"
    data = http_get_json(url)
    sh = (data.get("data") or {}).get("SH") or []
    row = next((item for item in sh if _match_instrument_row(item, instrument)), None)
    if not row:
        raise RuntimeError(f"Instrument {instrument} not found in SH list")
    bp, sp = float(row.get("BP") or "nan"), float(row.get("SP") or "nan")
    if mode == "MID" and not math.isnan(bp) and not math.isnan(sp):
        return (bp + sp) / 2
    if mode == "BP" and not math.isnan(bp):
        return bp
    return sp if not math.isnan(sp) else bp

def resolve_sge_price_and_label() -> Tuple[float, str]:
    src = (os.environ.get("SGE_SOURCE") or "XWTEAM").upper()
    mode = (os.environ.get("SGE_PRICE_MODE") or "SP").upper()
    instr = os.environ.get("SGE_INSTRUMENT") or "AU9999"
    label = os.environ.get("SGE_INSTRUMENT_LABEL") or _display_label(instr)
    if src == "XWTEAM":
        return fetch_sge_from_xwteam(instr, mode), label
    raise RuntimeError("Only XWTEAM supported here")

# ---------- Step 2: FX ----------

def fetch_usd_cny_from_exchangerate_host_live() -> float:
    key = os.environ.get("EXCHANGERATE_KEY", "").strip()
    if not key:
        raise RuntimeError("EXCHANGERATE_KEY missing")
    url = "https://api.exchangerate.host/live"
    data = http_get_json(url, params={"access_key": key, "currencies": "USD,CNY", "format": 1})
    if data.get("success") is False:
        raise RuntimeError(f"FX API error: {data.get('error')}")
    if "quotes" in data and "USDCNY" in data["quotes"]:
        return float(data["quotes"]["USDCNY"])
    raise RuntimeError(f"Unexpected FX payload: {data}")

def fetch_usd_cny_rate() -> float:
    return fetch_usd_cny_from_exchangerate_host_live()

# ---------- Step 4: Reference Gold ----------

def _tv_scan_close(market: str, ticker: str) -> float:
    url = f"https://scanner.tradingview.com/{market}/scan"
    columns = ["close", "pricescale", "minmov", "fractional", "currency", "name"]
    payload = {"symbols": {"tickers": [ticker]}, "columns": columns}
    data = http_post_json(url, payload)
    items = data.get("data") or []
    if not items:
        raise RuntimeError(f"TradingView returned no data for {ticker}")
    values = items[0].get("d") or []
    return float(values[0])

def fetch_reference_gold_usd_per_oz(ref_source: Optional[str] = None) -> float:
    src = (ref_source or os.environ.get("REF_SOURCE") or "FUTURES").upper()
    if src == "TV_SPOT":
        return _tv_scan_close("forex", os.environ.get("TV_SPOT_TICKER") or "OANDA:XAUUSD")
    return _tv_scan_close("futures", os.environ.get("TV_FUT_TICKER") or "COMEX:GC1!")

# ---------- Summary ----------

def build_summary(sge_cny_per_g: float, sge_label: str, cny_to_usd: float,
                  ref_usd_per_oz: float, ref_label: str, parse_mode: str = "TEXT") -> str:
    usd_per_oz_from_sge = (sge_cny_per_g * GRAMS_PER_TROY_OUNCE) * cny_to_usd
    diff = usd_per_oz_from_sge - ref_usd_per_oz
    diff_str = f"{diff:+,.2f}"
    ts = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"Gold Spread (SGE vs {ref_label})\n"
        f"Time: {ts}\n\n"
        f"SGE ({sge_label}): {sge_cny_per_g:,.2f} CNY/g\n"
        f"CNY→USD: {cny_to_usd:,.6f}\n"
        f"SGE → USD/oz: {usd_per_oz_from_sge:,.2f} USD/oz\n"
        f"{ref_label}: {ref_usd_per_oz:,.2f} USD/oz\n"
        f"Result: {diff_str} USD/oz"
    )

# ---------- Main ----------

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    ref_source = (os.environ.get("REF_SOURCE") or "FUTURES").upper()
    parse_mode = (os.environ.get("TELEGRAM_PARSE_MODE") or "TEXT").upper()
    if not token or not chat_id:
        raise SystemExit("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID required")

    sge_cny_per_g, sge_label = resolve_sge_price_and_label()
    usd_to_cny = fetch_usd_cny_rate()
    cny_to_usd = 1 / usd_to_cny
    ref_usd_per_oz = fetch_reference_gold_usd_per_oz(ref_source)
    ref_label = "Spot Gold (TradingView)" if ref_source == "TV_SPOT" else "CME Gold Futures"

    msg = build_summary(sge_cny_per_g, sge_label, cny_to_usd, ref_usd_per_oz, ref_label, parse_mode)
    send_telegram_message(token, chat_id, msg,
                          parse_mode=(parse_mode if parse_mode in {"HTML", "MARKDOWN"} else None))

if __name__ == "__main__":
    main()
