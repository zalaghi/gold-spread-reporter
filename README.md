# گزارشگر اختلاف قیمت طلا (بورس شانگهای → اونس / آتی CME)

این اکشن گیت‌هاب یک خلاصه‌ی تمیز به **تلگرام** ارسال می‌کند که شامل:

1) **بورس طلای شانگهای (Au9999)** به یوان/گرم  
2) نرخ تبدیل **یوان→دلار (CNY→USD)**  
3) قیمت معادل **اونس طلا بر حسب دلار** (محاسبه‌شده از مرحله ۱ و ۲)  
4) قیمت **مرجع طلا** (فیوچرز یا اسپات تریدینگ‌ویو) بر حسب دلار/اونس  

سپس **نتیجه = (مرحله ۳ − مرحله ۴)** را نشان می‌دهد:  
- اگر ۳ > ۴ → با علامت `+`  
- اگر ۳ < ۴ → با علامت `-`  
- اگر برابر باشند → بدون علامت

---

## متغیرها

- `SGE_SOURCE` : منبع داده بورس طلا  
  - `XWTEAM` (پیش‌فرض) → منبع رایگان بدون کلید  
  - `JISU` → نیاز به کلید `JISUAPI_KEY` دارد  

- `SGE_PRICE_MODE` : انتخاب قیمت از SGE  
  - `SP` → قیمت فروش (ask)  
  - `BP` → قیمت خرید (bid)  
  - `MID` → میانگین SP و BP  

- `FX_SOURCE` : منبع نرخ ارز (پیش‌فرض: `EXCHANGERATE_HOST`)  
  - `EXCHANGERATE_HOST`  
  - `YAHOO`  

- `REF_SOURCE` : منبع قیمت مرجع طلا (مرحله ۴)  
  - `FUTURES` (پیش‌فرض) → فیوچرز: یاهو `GC=F` و در صورت شکست تریدینگ‌ویو `COMEX:GC1!`  
  - `TV_SPOT` → قیمت اسپات از تریدینگ‌ویو (پیش‌فرض: `OANDA:XAUUSD` و در صورت شکست `TVC:GOLD`)  

- `YF_FUT_SYMBOL` : نماد فیوچرز در یاهو (`GC=F` پیش‌فرض)  
- `TV_FUT_TICKER` : نماد فیوچرز در تریدینگ‌ویو (`COMEX:GC1!` پیش‌فرض)  
- `TV_SPOT_MARKET` : مارکت تریدینگ‌ویو برای اسپات (پیش‌فرض: `forex`)  
- `TV_SPOT_TICKER` : نماد اسپات تریدینگ‌ویو (پیش‌فرض: `OANDA:XAUUSD`)  
- `TV_SPOT_MARKET_ALT` : مارکت جایگزین (پیش‌فرض: `cfd`)  
- `TV_SPOT_TICKER_ALT` : نماد جایگزین (پیش‌فرض: `TVC:GOLD`)  

- `TELEGRAM_PARSE_MODE` : حالت نمایش در تلگرام (`HTML` یا `Markdown`)  

---

## نمونه خروجی

```
Gold Spread (SGE vs Spot Gold)
Time: 2025-09-01 07:00 UTC

SGE (Au9999): 794.36 CNY/g
CNY→USD: 0.140200
SGE → USD/oz: 3,464.88 USD/oz
Spot Gold (TradingView): 3,475.70 USD/oz
Result: -10.82 USD/oz
```

---

## English Version

# Gold Spread Reporter (SGE → USD/oz vs Reference Gold)

This GitHub Action posts a clean **Telegram** summary comparing:

1) **SGE** (Shanghai Gold Exchange) Au9999 price (CNY/gram)  
2) **CNY→USD** FX rate  
3) **SGE → USD/oz** (conversion using Step 1 & 2)  
4) **Reference gold price** (either CME/COMEX futures or TradingView spot, in USD/oz)  

Then it prints **Result = (3 − 4)**:  
- If 3 > 4 → prefix `+`  
- If 3 < 4 → prefix `-`  
- If equal → no sign

---

## Variables

- `SGE_SOURCE` : data source for SGE  
  - `XWTEAM` (default) → free source (no key)  
  - `JISU` → requires `JISUAPI_KEY`  

- `SGE_PRICE_MODE` : which field to use  
  - `SP` → Sell Price (ask)  
  - `BP` → Buy Price (bid)  
  - `MID` → Average of SP and BP  

- `FX_SOURCE` : FX provider (default: `EXCHANGERATE_HOST`)  
  - `EXCHANGERATE_HOST`  
  - `YAHOO`  

- `REF_SOURCE` : reference gold price (Step 4)  
  - `FUTURES` (default) → Yahoo `GC=F` futures, fallback TradingView `COMEX:GC1!`  
  - `TV_SPOT` → TradingView spot price (default: `OANDA:XAUUSD`, fallback `TVC:GOLD`)  

- `YF_FUT_SYMBOL` : Yahoo futures symbol (default: `GC=F`)  
- `TV_FUT_TICKER` : TradingView futures ticker (default: `COMEX:GC1!`)  
- `TV_SPOT_MARKET` : TradingView market for spot (default: `forex`)  
- `TV_SPOT_TICKER` : TradingView spot ticker (default: `OANDA:XAUUSD`)  
- `TV_SPOT_MARKET_ALT` : alternate market (default: `cfd`)  
- `TV_SPOT_TICKER_ALT` : alternate spot ticker (default: `TVC:GOLD`)  

- `TELEGRAM_PARSE_MODE` : Telegram formatting (`HTML` or `Markdown`)  

---

## Example output

```
Gold Spread (SGE vs Spot Gold)
Time: 2025-09-01 07:00 UTC

SGE (Au9999): 794.36 CNY/g
CNY→USD: 0.140200
SGE → USD/oz: 3,464.88 USD/oz
Spot Gold (TradingView): 3,475.70 USD/oz
Result: -10.82 USD/oz
```

