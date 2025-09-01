import os
import math
import json
import datetime as dt
from typing import Dict, Any, Optional

import requests

GRAMS_PER_TROY_OUNCE = 31.1034768

# -------- Utilities --------

def http_get_json(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    r = requests.get(url, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    try:
        return r.json()
    except Exception as e:
        raise RuntimeError(f"Non-JSON response from {url}: {r.text[:200]}") from e

def http_post_json(url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    r = requests.post(url, json=payload, headers=headers, timeout=20)
    r.raise_for_status()
    try:
        return r.json()
    except Exception as e:
        raise RuntimeError(f"Non-JSON response from {url}: {r.text[:200]}") from e

def send_telegram_message(token: str, chat_id: str, text: str, parse_mode: Optional[str] = None) -> None:
    api = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
        payload["disable_web_page_preview"] = True
    r = requests.post(api, json=payload, timeout=20)
    if not r.ok:
        raise RuntimeError(f"Telegram send failed: {r.status_code} {r.text}")

# -------- Data Fetchers --------

def fetch_sge_au9999_from_xwteam(mode: str = "SP") -> float:
    """
    Fetch SGE Au9999 price (CNY/gram) from a free aggregator:
    https://free.xwteam.cn/api/gold/trade
    Returns fields under data.SH where Symbol == 'SH_Au9999'.
    mode: 'SP' (sell), 'BP' (buy), or 'MID' = (SP+BP)/2.
    """
    url = "https://free.xwteam.cn/api/gold/trade"
    data = http_get_json(url)
    payload = (data or {}).get("data") or {}
    sh = payload.get("SH") or []
    row = None
    for item in sh:
        if (item.get("Symbol") or "").upper() == "SH_AU9999":
            row = item
            break
    if not row:
        raise RuntimeError(f"Could not find SH_Au9999 in response: {str(data)[:300]}")

    bp = row.get("BP")
    sp = row.get("SP")

    def _to_float(x):
        try:
            return float(x)
        except Exception:
            return float('nan')

    bp = _to_float(bp)
    sp = _to_float(sp)

    mode = (mode or "SP").upper()
    if mode == "MID" and not math.isnan(bp) and not math.isnan(sp):
        return (bp + sp) / 2.0
    if mode == "BP" and not math.isnan(bp):
        return bp
    if not math.isnan(sp):
        return sp
    if not math.isnan(bp):
        return bp
    raise RuntimeError(f"Neither SP nor BP available in row: {row}")

def fetch_sge_au9999_from_jisu(appkey: str) -> float:
    """Optional fallback: JisuAPI Au9999 in CNY/gram (requires key)."""
    if not appkey:
        raise ValueError("JISUAPI_KEY is required for JISU source.")
    url = "https://api.jisuapi.com/gold/shgold"
    data = http_get_json(url, params={"appkey": appkey})
    result = data.get("result") or data.get("data") or {}
    items = result.get("list") or result.get("result") or result.get("items") or []
    if not items:
        items = data.get("list", [])
    if not items:
        raise RuntimeError(f"No SGE items found in response: {json.dumps(data)[:400]}")
    preferred = None
    for row in items:
        t = (row.get("type") or row.get("code") or "").upper()
        if t in {"AU9999", "AU99.99", "AU_9999", "AU_99_99"}:
            preferred = row
            break
    if preferred is None:
        for row in items:
            name = (row.get("typename") or row.get("name") or "").lower()
            if "au9999" in name or "au 99.99" in name or "99.99" in name:
                preferred = row
                break
    if preferred is None:
        preferred = items[0]
    price_str = str(preferred.get("price") or preferred.get("new_price") or preferred.get("latest") or "")
    return float(price_str)

def fetch_usd_cny_from_tradingview(ticker: str = "FX_IDC:USDCNY") -> float:
    """
    Fetch USD->CNY via TradingView's public screener endpoint.
    This endpoint is undocumented and may change.
    """
    url = "https://scanner.tradingview.com/forex/scan"
    columns = ["close", "pricescale", "minmov", "fractional", "currency", "name"]
    payload = {
        "symbols": {"tickers": [ticker], "query": {"types": []}},
        "columns": columns,
    }
    data = http_post_json(url, payload)
    items = data.get("data") or []
    if not items:
        raise RuntimeError(f"TradingView scan returned no data for {ticker}: {data}")
    values = items[0].get("d") or []
    mapping = {c: values[i] if i < len(values) else None for i, c in enumerate(columns)}
    close = mapping.get("close")
    if close is None:
        raise RuntimeError(f"TradingView close missing in response: {mapping}")
    return float(close)

def fetch_usd_cny_rate(source: str = "TRADINGVIEW") -> float:
    """
    Get USD->CNY. Preferred: TradingView screener (undocumented).
    Alternatives: exchangerate.host or Yahoo.
    """
    s = (source or os.environ.get("FX_SOURCE") or "TRADINGVIEW").upper()
    if s == "TRADINGVIEW":
        ticker = os.environ.get("TV_FX_TICKER") or "FX_IDC:USDCNY"
        return fetch_usd_cny_from_tradingview(ticker)
    if s == "YAHOO":
        url = "https://query1.finance.yahoo.com/v7/finance/quote"
        data = http_get_json(url, params={"symbols": "USDCNY=X"})
        result = (data.get("quoteResponse", {}).get("result") or [{}])[0]
        rate = result.get("regularMarketPrice") or result.get("bid") or result.get("ask")
        if not rate:
            raise RuntimeError(f"Yahoo USDCNY=X missing price in {json.dumps(result)[:200]}")
        return float(rate)
    else:
        url = "https://api.exchangerate.host/latest"
        data = http_get_json(url, params={"base": "USD", "symbols": "CNY"})
        rate = (data.get("rates") or {}).get("CNY")
        if not rate:
            raise RuntimeError(f"exchangerate.host missing CNY in {json.dumps(data)[:200]}")
        return float(rate)

def fetch_cme_gold_futures_usd_per_oz(yf_symbol: str = "GC=F") -> float:
    """
    Use Yahoo Finance quote endpoint to get COMEX/CME Gold futures (nearest contract / continuous).
    """
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    data = http_get_json(url, params={"symbols": yf_symbol})
    result = (data.get("quoteResponse", {}).get("result") or [{}])[0]
    price = result.get("regularMarketPrice") or result.get("bid") or result.get("ask")
    if not price:
        raise RuntimeError(f"Yahoo {yf_symbol} missing price in {json.dumps(result)[:200]}")
    return float(price)

# -------- Business Logic --------

def resolve_sge_price() -> float:
    src = (os.environ.get("SGE_SOURCE") or "XWTEAM").upper()
    mode = (os.environ.get("SGE_PRICE_MODE") or "SP").upper()
    if src == "XWTEAM":
        return fetch_sge_au9999_from_xwteam(mode)
    elif src == "JISU":
        key = os.environ.get("JISUAPI_KEY", "").strip()
        return fetch_sge_au9999_from_jisu(key)
    else:
        return fetch_sge_au9999_from_xwteam(mode)

def build_summary(sge_cny_per_g: float, usd_to_cny: float, cme_usd_per_oz: float, now_utc: Optional[dt.datetime] = None, parse_mode: str = "TEXT") -> str:
    usd_per_oz_from_sge = (sge_cny_per_g * GRAMS_PER_TROY_OUNCE) / usd_to_cny
    diff = cme_usd_per_oz - usd_per_oz_from_sge
    now_utc = now_utc or dt.datetime.utcnow()
    ts = now_utc.strftime("%Y-%m-%d %H:%M UTC")

    if parse_mode.upper() == "HTML":
        return f"""
<b>Gold Spread (SGE vs CME)</b>
<b>Time:</b> {ts}

<b>1) SGE (Au9999):</b> {sge_cny_per_g:,.2f} CNY/g
<b>2) USD→CNY:</b> {usd_to_cny:,.6f}
<b>3) SGE → USD/oz:</b> {usd_per_oz_from_sge:,.2f} USD/oz
<b>4) CME Gold Futures:</b> {cme_usd_per_oz:,.2f} USD/oz
<b>Δ (4 − 3):</b> {diff:,.2f} USD/oz
""".strip()
    else:
        return "\n".join([
            "Gold Spread (SGE vs CME)",
            f"Time: {ts}",
            "",
            f"1) SGE (Au9999): {sge_cny_per_g:,.2f} CNY/g",
            f"2) USD→CNY: {usd_to_cny:,.6f}",
            f"3) SGE → USD/oz: {usd_per_oz_from_sge:,.2f} USD/oz",
            f"4) CME Gold Futures: {cme_usd_per_oz:,.2f} USD/oz",
            f"Δ (4 − 3): {diff:,.2f} USD/oz",
        ])

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    fx_source = (os.environ.get("FX_SOURCE") or "TRADINGVIEW").upper()
    yf_symbol = (os.environ.get("YF_FUT_SYMBOL") or "GC=F").strip()
    parse_mode = (os.environ.get("TELEGRAM_PARSE_MODE") or "TEXT").upper()

    if not token or not chat_id:
        raise SystemExit("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required.")

    sge_cny_per_g = resolve_sge_price()
    usd_to_cny = fetch_usd_cny_rate(fx_source)
    cme_usd_per_oz = fetch_cme_gold_futures_usd_per_oz(yf_symbol)

    msg = build_summary(sge_cny_per_g, usd_to_cny, cme_usd_per_oz, parse_mode=parse_mode)
    send_telegram_message(token, chat_id, msg, parse_mode=(parse_mode if parse_mode in {"HTML", "MARKDOWN"} else None))

if __name__ == "__main__":
    main()
