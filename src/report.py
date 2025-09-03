import os
import math
import json
import time
import datetime as dt
from typing import Dict, Any, Optional

import requests

GRAMS_PER_TROY_OUNCE = 31.1034768

# A simple browsery UA helps with some public endpoints
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    )
}

# -------- HTTP helpers with retries --------

def _request_with_retries(
    method: str,
    url: str,
    *,
    max_retries: int = 5,
    backoff_base: float = 0.6,
    expected_json: bool = True,
    **kwargs
):
    """HTTP request with basic exponential backoff on 429/5xx."""
    headers = kwargs.pop("headers", {}) or {}
    headers = {**DEFAULT_HEADERS, **headers}
    for attempt in range(max_retries):
        resp = requests.request(method, url, headers=headers, timeout=20, **kwargs)
        if resp.status_code < 400:
            if expected_json:
                try:
                    return resp.json()
                except Exception as e:
                    raise RuntimeError(f"Non-JSON response from {url}: {resp.text[:200]}") from e
            return resp.text

        # Retry on throttling or server errors
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
            # honor Retry-After if present
            ra = resp.headers.get("Retry-After")
            if ra and ra.isdigit():
                delay = float(ra)
            else:
                delay = backoff_base * (2 ** attempt)  # 0.6, 1.2, 2.4, ...
            time.sleep(delay)
            continue

        # Unrecoverable (or out of retries)
        resp.raise_for_status()

def http_get_json(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    return _request_with_retries("GET", url, params=params, headers=headers, expected_json=True)

def http_post_json(url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    return _request_with_retries("POST", url, json=payload, headers=headers, expected_json=True)

def send_telegram_message(token: str, chat_id: str, text: str, parse_mode: Optional[str] = None) -> None:
    api = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
        payload["disable_web_page_preview"] = True
    r = requests.post(api, json=payload, headers=DEFAULT_HEADERS, timeout=20)
    if not r.ok:
        raise RuntimeError(f"Telegram send failed: {r.status_code} {r.text}")

# -------- Data Fetchers --------

def fetch_sge_au9999_from_xwteam(mode: str = "SP") -> float:
    """
    Fetch SGE Au9999 price (CNY/gram) from a free aggregator:
    https://free.xwteam.cn/api/gold/trade
    Uses data.SH where Symbol == 'SH_Au9999'.
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

    def _to_float(x):
        try:
            return float(x)
        except Exception:
            return float('nan')

    bp = _to_float(row.get("BP"))
    sp = _to_float(row.get("SP"))

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
    payload = {"symbols": {"tickers": [ticker], "query": {"types": []}}, "columns": columns}
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

def _fetch_yahoo_quote_with_retry(symbol: str) -> Optional[float]:
    """Try Yahoo quote with retries. Return None on failure."""
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    try:
        data = http_get_json(url, params={"symbols": symbol})
        result = (data.get("quoteResponse", {}).get("result") or [{}])[0]
        price = result.get("regularMarketPrice") or result.get("bid") or result.get("ask")
        return float(price) if price is not None else None
    except Exception:
        return None

def _fetch_tradingview_futures_close(ticker: str = "COMEX:GC1!") -> float:
    """
    Fallback: TradingView futures screener for front/continuous gold.
    Common tickers: COMEX:GC1!  or  CME:GC1!
    """
    url = "https://scanner.tradingview.com/futures/scan"
    columns = ["close", "pricescale", "minmov", "fractional", "currency", "name"]
    payload = {"symbols": {"tickers": [ticker], "query": {"types": []}}, "columns": columns}
    data = http_post_json(url, payload)
    items = data.get("data") or []
    if not items:
        raise RuntimeError(f"TradingView futures scan returned no data for {ticker}: {data}")
    values = items[0].get("d") or []
    mapping = {c: values[i] if i < len(values) else None for i, c in enumerate(columns)}
    close = mapping.get("close")
    if close is None:
        raise RuntimeError(f"TradingView futures close missing in response: {mapping}")
    return float(close)

def _fetch_tradingview_spot_close(ticker: str = "OANDA:XAUUSD") -> float:
    """
    TradingView spot gold via the forex screener (e.g., OANDA:XAUUSD).
    """
    url = "https://scanner.tradingview.com/forex/scan"
    columns = ["close", "pricescale", "minmov", "fractional", "currency", "name"]
    payload = {"symbols": {"tickers": [ticker], "query": {"types": []}}, "columns": columns}
    data = http_post_json(url, payload)
    items = data.get("data") or []
    if not items:
        raise RuntimeError(f"TradingView forex scan returned no data for {ticker}: {data}")
    values = items[0].get("d") or []
    mapping = {c: values[i] if i < len(values) else None for i, c in enumerate(columns)}
    close = mapping.get("close")
    if close is None:
        raise RuntimeError(f"TradingView spot close missing in response: {mapping}")
    return float(close)

def fetch_reference_gold_usd_per_oz(
    yf_symbol: str = "GC=F",
    ref_source: Optional[str] = None
) -> float:
    """
    Get the reference gold price (USD/oz) used in Step 4.

    Modes:
      - FUTURES (default): Yahoo GC=F with fallback to TV futures (COMEX:GC1!)
      - TV_SPOT: TradingView spot price via forex screener (e.g., OANDA:XAUUSD)
    """
    src = (ref_source or os.environ.get("REF_SOURCE") or "FUTURES").upper()

    if src == "TV_SPOT":
        tv_spot = os.environ.get("TV_SPOT_TICKER") or "OANDA:XAUUSD"
        return _fetch_tradingview_spot_close(tv_spot)

    # FUTURES (existing behavior)
    price = _fetch_yahoo_quote_with_retry(yf_symbol)
    if price is not None:
        return float(price)
    tv_ticker = os.environ.get("TV_FUT_TICKER") or "COMEX:GC1!"
    return _fetch_tradingview_futures_close(tv_ticker)

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

def build_summary(
    sge_cny_per_g: float,
    cny_to_usd: float,
    ref_usd_per_oz: float,
    now_utc: Optional[dt.datetime] = None,
    parse_mode: str = "TEXT",
    ref_label: str = "CME Gold Futures",
) -> str:
    # Step 3: SGE converted to USD/oz
    usd_per_oz_from_sge = (sge_cny_per_g * GRAMS_PER_TROY_OUNCE) * cny_to_usd

    # Difference = (3 − 4)
    diff = usd_per_oz_from_sge - ref_usd_per_oz
    if diff > 0:
        diff_str = f"+{abs(diff):,.2f}"
    elif diff < 0:
        diff_str = f"-{abs(diff):,.2f}"
    else:
        diff_str = f"{diff:,.2f}"

    now_utc = now_utc or dt.datetime.utcnow()
    ts = now_utc.strftime("%Y-%m-%d %H:%M UTC")

    if parse_mode.upper() == "HTML":
        return f"""
<b>Gold Spread (SGE vs {ref_label})</b>
<b>Time:</b> {ts}

<b>SGE (Au9999):</b> {sge_cny_per_g:,.2f} CNY/g
<b>CNY→USD:</b> {cny_to_usd:,.6f}
<b>SGE → USD/oz:</b> {usd_per_oz_from_sge:,.2f} USD/oz
<b>{ref_label}:</b> {ref_usd_per_oz:,.2f} USD/oz
<b>Result:</b> {diff_str} USD/oz
""".strip()
    else:
        return "\n".join([
            f"Gold Spread (SGE vs {ref_label})",
            f"Time: {ts}",
            "",
            f"SGE (Au9999): {sge_cny_per_g:,.2f} CNY/g",
            f"CNY→USD: {cny_to_usd:,.6f}",
            f"SGE → USD/oz: {usd_per_oz_from_sge:,.2f} USD/oz",
            f"{ref_label}: {ref_usd_per_oz:,.2f} USD/oz",
            f"Result: {diff_str} USD/oz",
        ])

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    fx_source = (os.environ.get("FX_SOURCE") or "TRADINGVIEW").upper()
    yf_symbol = (os.environ.get("YF_FUT_SYMBOL") or "GC=F").strip()
    parse_mode = (os.environ.get("TELEGRAM_PARSE_MODE") or "TEXT").upper()
    ref_source = (os.environ.get("REF_SOURCE") or "FUTURES").upper()

    if not token or not chat_id:
        raise SystemExit("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required.")

    # SGE price (CNY/g)
    sge_cny_per_g = resolve_sge_price()

    # FX: fetch USD→CNY then invert to CNY→USD for display and math
    usd_to_cny = fetch_usd_cny_rate(fx_source)
    cny_to_usd = 1.0 / float(usd_to_cny)

    # Reference gold (USD/oz): Futures (default) or TV spot
    ref_usd_per_oz = fetch_reference_gold_usd_per_oz(yf_symbol=yf_symbol, ref_source=ref_source)
    ref_label = "Spot Gold (TradingView)" if ref_source == "TV_SPOT" else "CME Gold Futures"

    # Build and send
    msg = build_summary(sge_cny_per_g, cny_to_usd, ref_usd_per_oz, parse_mode=parse_mode, ref_label=ref_label)
    send_telegram_message(
        token, chat_id, msg,
        parse_mode=(parse_mode if parse_mode in {"HTML", "MARKDOWN"} else None)
    )

if __name__ == "__main__":
    main()
