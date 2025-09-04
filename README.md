# گزارشگر اختلاف قیمت طلا (بورس شانگهای → اونس / آتی CME)

این اکشن گیت‌هاب خلاصه‌ای از اختلاف قیمت طلا بین **بورس شانگهای** و **قیمت مرجع جهانی** را به **تلگرام** ارسال می‌کند:

## مراحل محاسبه

1) **قیمت بورس شانگهای (SGE)**  
   - ابزار پیش‌فرض: `Au9999`  
   - امکان انتخاب ابزار: `Au+TD` با استفاده از متغیر `SGE_INSTRUMENT=AUTD`  
   - حالت قیمت (`SGE_PRICE_MODE`):  
     - `SP` → قیمت فروش (Sell/Ask)  
     - `BP` → قیمت خرید (Buy/Bid)  
     - `MID` → میانگین SP و BP  

2) **نرخ تبدیل ارز (CNY→USD)**  
   - تنها منبع: **exchangerate.host** از طریق API Key  
   - نیاز به متغیر `EXCHANGERATE_KEY` در Secrets  

3) **تبدیل قیمت طلا از CNY/گرم به USD/اونس**  

4) **قیمت مرجع جهانی (USD/oz)**  
   - `FUTURES` → آتی‌های COMEX (نماد پیش‌فرض: `COMEX:GC1!`)  
   - `TV_SPOT` → قیمت اسپات از TradingView (پیش‌فرض: `OANDA:XAUUSD`، جایگزین: `TVC:GOLD`)  

5) **اختلاف قیمت (مرحله ۳ − مرحله ۴)**  

---

## متغیرها

- `SGE_SOURCE`: منبع داده بورس طلا (پیش‌فرض: `XWTEAM`)  
- `SGE_INSTRUMENT`: ابزار SGE (`AU9999` یا `AUTD`)  
- `SGE_INSTRUMENT_LABEL`: برچسب نمایشی (پیش‌فرض: `Au9999` یا `Au+TD`)  
- `SGE_PRICE_MODE`: حالت قیمت (SP | BP | MID)  

- `EXCHANGERATE_KEY`: کلید API برای نرخ ارز (exchangerate.host)  

- `REF_SOURCE`: منبع قیمت مرجع (`FUTURES` یا `TV_SPOT`)  
- `TV_FUT_TICKER`: نماد آتی در TradingView (پیش‌فرض: `COMEX:GC1!`)  
- `TV_SPOT_TICKER`: نماد اسپات (پیش‌فرض: `OANDA:XAUUSD`)  
- `TV_SPOT_TICKER_ALT`: نماد اسپات جایگزین (پیش‌فرض: `TVC:GOLD`)  

- `TELEGRAM_BOT_TOKEN`: توکن ربات تلگرام  
- `TELEGRAM_CHAT_ID`: شناسه کانال یا چت تلگرام  
- `TELEGRAM_PARSE_MODE`: حالت نمایش (HTML یا Markdown)  

---

## نمونه خروجی


```
Gold Spread (SGE vs Spot Gold)
Time: 2025-09-04 07:00 UTC

SGE (Au+TD): 792.60 CNY/g
CNY→USD: 0.140200
SGE → USD/oz: 3,465.20 USD/oz
Spot Gold (TradingView): 3,475.70 USD/oz
Result: -10.50 USD/oz
```

---

## English Version
# Gold Spread Reporter (SGE → USD/oz vs Reference Gold)

This GitHub Action sends a **Telegram** summary comparing Shanghai Gold Exchange prices with global benchmarks.

## Steps

1) **Shanghai Gold Exchange (SGE)**  
   - Default instrument: `Au9999`  
   - Optional: `Au+TD` via `SGE_INSTRUMENT=AUTD`  
   - Price mode (`SGE_PRICE_MODE`):  
     - `SP` → Sell (Ask)  
     - `BP` → Buy (Bid)  
     - `MID` → Average of SP and BP  

2) **FX rate (CNY→USD)**  
   - Source: **exchangerate.host** (requires API key)  
   - Key must be provided as `EXCHANGERATE_KEY` in repo Secrets  

3) **Convert SGE from CNY/gram → USD/oz**  

4) **Reference price (USD/oz)**  
   - `FUTURES` → COMEX gold futures (default: `COMEX:GC1!`)  
   - `TV_SPOT` → TradingView spot gold (default: `OANDA:XAUUSD`, fallback: `TVC:GOLD`)  

5) **Spread = Step 3 − Step 4**  

---

## Variables

- `SGE_SOURCE`: SGE data source (default: `XWTEAM`)  
- `SGE_INSTRUMENT`: instrument (`AU9999` or `AUTD`)  
- `SGE_INSTRUMENT_LABEL`: display label (`Au9999` or `Au+TD`)  
- `SGE_PRICE_MODE`: SP | BP | MID  

- `EXCHANGERATE_KEY`: API key for FX (exchangerate.host)  

- `REF_SOURCE`: reference gold source (`FUTURES` or `TV_SPOT`)  
- `TV_FUT_TICKER`: TradingView futures ticker (default: `COMEX:GC1!`)  
- `TV_SPOT_TICKER`: spot ticker (default: `OANDA:XAUUSD`)  
- `TV_SPOT_TICKER_ALT`: fallback ticker (default: `TVC:GOLD`)  

- `TELEGRAM_BOT_TOKEN`: Telegram bot token  
- `TELEGRAM_CHAT_ID`: chat/channel ID  
- `TELEGRAM_PARSE_MODE`: message format (HTML or Markdown)  

---

## Example Output

```
Gold Spread (SGE vs Spot Gold)
Time: 2025-09-04 07:00 UTC

SGE (Au+TD): 792.60 CNY/g
CNY→USD: 0.140200
SGE → USD/oz: 3,465.20 USD/oz
Spot Gold (TradingView): 3,475.70 USD/oz
Result: -10.50 USD/oz
```

