# Gold Spread Reporter (SGE → USD/oz vs CME Futures)

This GitHub Action posts a clean **Telegram** summary comparing:

1. **SGE** (Shanghai Gold Exchange) *Au9999* price (CNY/gram)
2. **CNY→USD** FX rate  
3. The **converted** SGE price (USD per troy ounce)
4. **CME/COMEX gold futures** price (USD/oz)

It also includes the **difference**: **(Step 4 − Step 3)** in USD/oz.

---

## Data sources

- **SGE price (Au9999)**  
  - Default: a **free aggregator** (no account): `https://free.xwteam.cn/api/gold/trade`  
    - We read `data.SH[Symbol=SH_Au9999]` and use **SP** (sell) by default  
  - Optional fallback: **JisuAPI** `gold/shgold` (requires key; only if you explicitly choose it)

- **CNY→USD FX**  
  - Default: **TradingView** screener (undocumented, no key) using ticker `FX_IDC:USDCNY` (inverted)  
  - Fallbacks: **exchangerate.host** (open) or **Yahoo Finance** (`USDCNY=X`)

- **CME/COMEX gold futures**  
  - Primary: **Yahoo Finance** (`GC=F`)  
  - Fallback: **TradingView** futures screener (e.g., `COMEX:GC1!`)

---

## Setup

### 1) Create a Telegram bot & get chat ID
- In Telegram → **@BotFather** → `/newbot` → follow prompts → copy **bot token**
- Add the bot to your **channel/group** (or chat with it 1:1)
- Open: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` and grab the **chat.id**  
  (Negative IDs are groups/channels)

### 2) Add **secrets** (Repo → Settings → Secrets and variables → **Actions**)
- **Required:**
  - `TELEGRAM_BOT_TOKEN` = your bot token
  - `TELEGRAM_CHAT_ID` = numeric chat ID
- **Optional:**
  - `JISUAPI_KEY` = only if you set `SGE_SOURCE=JISU`

### 3) Add **variables** (Repo → Settings → Secrets and variables → **Variables**)

- `SGE_SOURCE` = `XWTEAM` *(default)* or `JISU`  
- `SGE_PRICE_MODE` = `SP` *(default)* | `BP` | `MID`  
- `FX_SOURCE` = `TRADINGVIEW` *(default)* | `EXCHANGERATE_HOST` | `YAHOO`  
- `TV_FX_TICKER` = `FX_IDC:USDCNY` *(default)*  
- `YF_FUT_SYMBOL` = `GC=F` *(default)*  
- `TV_FUT_TICKER` = `COMEX:GC1!` *(default)*  
- `TELEGRAM_PARSE_MODE` = `HTML` *(recommended)* or `Markdown`

---

## Variables — full reference

### `SGE_SOURCE`
- `XWTEAM` *(default)* — free aggregator; no login/key.  
- `JISU` — uses JisuAPI (requires `JISUAPI_KEY` secret).

### `SGE_PRICE_MODE`
- `SP` *(default)* — Sell Price (ask). Slightly higher.  
- `BP` — Buy Price (bid). Slightly lower.  
- `MID` — Midpoint between SP and BP.

### `FX_SOURCE`
- `TRADINGVIEW` *(default)* — uses TradingView’s `FX_IDC:USDCNY`, then inverted to get CNY→USD.  
- `EXCHANGERATE_HOST` — public REST API.  
- `YAHOO` — Yahoo Finance `USDCNY=X`.

### `TV_FX_TICKER`
- Default: `FX_IDC:USDCNY`  
- Example: `FX_IDC:USDCNH` for offshore CNH.

### `YF_FUT_SYMBOL`
- Default: `GC=F`  
- Example: `GCZ25.CMX` for December 2025.

### `TV_FUT_TICKER`
- Default: `COMEX:GC1!`  
- Example: `CME:GC1!`

### `TELEGRAM_PARSE_MODE`
- `HTML` *(recommended)* — bold labels, clean layout.  
- `Markdown` — alternate format.  
- unset = plain text.

---

## Schedule

The workflow runs **weekdays at 09:00 Europe/Madrid** (`07:00 UTC`).  
You can run manually from **Actions → Run workflow**.

---

## Example message

```
Gold Spread (SGE vs CME)
Time: 2025-09-01 07:00 UTC

1) SGE (Au9999): 794.36 CNY/g
2) CNY→USD: 0.140200
3) SGE → USD/oz: 3,464.88 USD/oz
4) CME Gold Futures: 3,475.70 USD/oz
Δ (4 − 3): 10.82 USD/oz
```

---

## Local run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export TELEGRAM_BOT_TOKEN=...        TELEGRAM_CHAT_ID=...        SGE_SOURCE=XWTEAM        SGE_PRICE_MODE=SP        FX_SOURCE=TRADINGVIEW        TV_FX_TICKER=FX_IDC:USDCNY        YF_FUT_SYMBOL=GC=F        TV_FUT_TICKER=COMEX:GC1!        TELEGRAM_PARSE_MODE=HTML

python src/report.py
```

---

## Troubleshooting

- **Telegram errors**: Bot not added, wrong ID, or missing permissions.  
- **SGE fetch fails**: XWTEAM may be down. Retry, or switch to `SGE_SOURCE=JISU`.  
- **FX errors**: Use `EXCHANGERATE_HOST` or `YAHOO`.  
- **Futures errors**: Yahoo may throttle; TradingView fallback runs automatically.

---

## License

MIT
