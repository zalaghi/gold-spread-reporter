import os


now_utc = now_utc or dt.datetime.utcnow()
ts = now_utc.strftime("%Y-%m-%d %H:%M UTC")


if parse_mode.upper() == "HTML":
return (
f"<b>Gold Spread (SGE vs CME)</b>
"
f"<b>Time:</b> {ts}


"
f"<b>1) SGE (Au9999):</b> {sge_cny_per_g:,.2f} CNY/g
"
f"<b>2) USD→CNY:</b> {usd_to_cny:,.6f}
"
f"<b>3) SGE → USD/oz:</b> {usd_per_oz_from_sge:,.2f} USD/oz
"
f"<b>4) CME Gold Futures:</b> {cme_usd_per_oz:,.2f} USD/oz
"
f"<b>Δ (4 − 3):</b> {diff:,.2f} USD/oz"
)
else:
lines = [
"Gold Spread (SGE vs CME)",
f"Time: {ts}",
"",
f"1) SGE (Au9999): {sge_cny_per_g:,.2f} CNY/g",
f"2) USD→CNY: {usd_to_cny:,.6f}",
f"3) SGE → USD/oz: {usd_per_oz_from_sge:,.2f} USD/oz",
f"4) CME Gold Futures: {cme_usd_per_oz:,.2f} USD/oz",
f"Δ (4 − 3): {diff:,.2f} USD/oz",
]
return "
".join(lines)




def main() -> None:
token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()


fx_source = (os.environ.get("FX_SOURCE") or "TRADINGVIEW").upper()
yf_symbol = (os.environ.get("YF_FUT_SYMBOL") or "GC=F").strip()
parse_mode = (os.environ.get("TELEGRAM_PARSE_MODE") or "TEXT").upper()


if not token or not chat_id:
raise SystemExit("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required.")


# Fetch data
sge_cny_per_g = resolve_sge_price()
usd_to_cny = fetch_usd_cny_rate(fx_source)
cme_usd_per_oz = fetch_cme_gold_futures_usd_per_oz(yf_symbol)


# Build and send
msg = build_summary(sge_cny_per_g, usd_to_cny, cme_usd_per_oz, parse_mode=parse_mode)
send_telegram_message(token, chat_id, msg, parse_mode=(parse_mode if parse_mode in {"HTML", "MARKDOWN"} else None))




def main_old():
# deprecated entrypoint kept for clarity — not used
main()


if __name__ == "__main__":
main()
# Inputs
token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
jisu_key = os.environ.get("JISUAPI_KEY", "").strip()


fx_source = (os.environ.get("FX_SOURCE") or "TRADINGVIEW").upper()
yf_symbol = (os.environ.get("YF_FUT_SYMBOL") or "GC=F").strip()
parse_mode = (os.environ.get("TELEGRAM_PARSE_MODE") or "TEXT").upper()


if not token or not chat_id:
raise SystemExit("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required.")


# Fetch data
sge_cny_per_g = fetch_sge_au9999_cny_per_gram(jisu_key)
usd_to_cny = fetch_usd_cny_rate(fx_source)
cme_usd_per_oz = fetch_cme_gold_futures_usd_per_oz(yf_symbol)


# Build and send
msg = build_summary(sge_cny_per_g, usd_to_cny, cme_usd_per_oz, parse_mode=parse_mode)
send_telegram_message(token, chat_id, msg, parse_mode=(parse_mode if parse_mode in {"HTML", "MARKDOWN"} else None))




if __name__ == "__main__":
main()
