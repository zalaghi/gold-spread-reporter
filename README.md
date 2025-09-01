# گزارشگر اختلاف قیمت طلا (بورس شانگهای → اونس / آتی CME)

این اکشن گیت‌هاب یک خلاصه‌ی تمیز به **تلگرام** ارسال می‌کند که شامل:

1) **بورس طلای شانگهای (Au9999)** به یوان/گرم  
2) نرخ تبدیل **یوان→دلار (CNY→USD)**  
3) قیمت معادل **اونس طلا بر حسب دلار** (محاسبه‌شده از مرحله ۱ و ۲)  
4) قیمت **آتی طلای CME/COMEX** بر حسب دلار/اونس  

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

- `FX_SOURCE` : منبع نرخ ارز  
  - `TRADINGVIEW` (پیش‌فرض)  
  - `EXCHANGERATE_HOST`  
  - `YAHOO`  

- `TV_FX_TICKER` : نماد در تریدینگ‌ویو (پیش‌فرض: `FX_IDC:USDCNY`)  
- `YF_FUT_SYMBOL` : نماد آتی در یاهو (`GC=F` پیش‌فرض)  
- `TV_FUT_TICKER` : نماد آتی در تریدینگ‌ویو (`COMEX:GC1!` پیش‌فرض)  
- `TELEGRAM_PARSE_MODE` : حالت نمایش در تلگرام (`HTML` یا `Markdown`)  

---

## نمونه خروجی

```
گزارش اختلاف طلا (SGE vs CME)
زمان: 2025-09-01 07:00 UTC

1) SGE (Au9999): 794.36 CNY/g
2) CNY→USD: 0.140200
3) SGE → USD/oz: 3,464.88 USD/oz
4) CME Gold Futures: 3,475.70 USD/oz
نتیجه: -10.82 USD/oz
```

---

برای جزئیات بیشتر به نسخه انگلیسی مراجعه کنید ↓

---

## English Version

# Gold Spread Reporter (SGE → USD/oz vs CME Futures)

This GitHub Action posts a clean **Telegram** summary comparing:

1) **SGE** (Shanghai Gold Exchange) Au9999 price (CNY/gram)  
2) **CNY→USD** FX rate  
3) **SGE → USD/oz** (conversion using Step 1 & 2)  
4) **CME/COMEX gold futures** price (USD/oz)  

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

- `FX_SOURCE` : FX provider  
  - `TRADINGVIEW` (default)  
  - `EXCHANGERATE_HOST`  
  - `YAHOO`  

- `TV_FX_TICKER` : TradingView ticker (default: `FX_IDC:USDCNY`)  
- `YF_FUT_SYMBOL` : Yahoo futures symbol (default: `GC=F`)  
- `TV_FUT_TICKER` : TradingView futures ticker (default: `COMEX:GC1!`)  
- `TELEGRAM_PARSE_MODE` : Telegram formatting (`HTML` or `Markdown`)  

---

## Example output

```
Gold Spread (SGE vs CME)
Time: 2025-09-01 07:00 UTC

1) SGE (Au9999): 794.36 CNY/g
2) CNY→USD: 0.140200
3) SGE → USD/oz: 3,464.88 USD/oz
4) CME Gold Futures: 3,475.70 USD/oz
Result: -10.82 USD/oz
```
