import os
import requests
import pandas as pd
import snowflake.connector
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── DOW 30 Tickers and Company Names ──────────────────────────
DOW30_STOCKS = {
    "AAPL": "Apple Inc",
    "MSFT": "Microsoft Corporation",
    "JPM":  "JPMorgan Chase",
    "GS":   "Goldman Sachs",
    "V":    "Visa Inc",
    "AXP":  "American Express",
    "UNH":  "UnitedHealth Group",
    "JNJ":  "Johnson & Johnson",
    "WMT":  "Walmart Inc",
    "HD":   "Home Depot",
    "MCD":  "McDonalds Corporation",
    "DIS":  "Walt Disney Company",
    "NKE":  "Nike Inc",
    "AMZN": "Amazon Inc",
    "BA":   "Boeing Company",
    "CAT":  "Caterpillar Inc",
    "HON":  "Honeywell International",
    "IBM":  "IBM Corporation",
    "INTC": "Intel Corporation",
    "CVX":  "Chevron Corporation",
    "PG":   "Procter and Gamble",
    "KO":   "Coca-Cola Company",
    "MMM":  "3M Company",
    "MRK":  "Merck and Co",
    "VZ":   "Verizon Communications",
    "TRV":  "Travelers Companies",
    "AMGN": "Amgen Inc",
    "CRM":  "Salesforce Inc",
    "DOW":  "Dow Inc",
    "DD":   "DuPont de Nemours"
}

# ── FRED Series IDs for each ticker ───────────────────────────
# FRED doesn't have individual stock prices
# We use Yahoo Finance for stock data via yfinance
# and FRED for the DOW index itself

START_DATE = "2020-01-01"
END_DATE   = datetime.today().strftime("%Y-%m-%d")

# ── Fetch stock data using yfinance ───────────────────────────
def fetch_stock_data():
    import yfinance as yf

    all_data = []

    print(f"Fetching DOW 30 stock data from {START_DATE} to {END_DATE}...")

    for ticker, company in DOW30_STOCKS.items():
        try:
            print(f"  Fetching {ticker} — {company}...")
            stock = yf.download(
                ticker,
                start=START_DATE,
                end=END_DATE,
                progress=False
            )

            if stock.empty:
                print(f"  No data for {ticker}, skipping...")
                continue

            stock = stock.reset_index()
            stock.columns = [c[0] if isinstance(c, tuple) else c
                             for c in stock.columns]

            for _, row in stock.iterrows():
                all_data.append({
                    "ticker":       ticker,
                    "company_name": company,
                    "trade_date":   str(row["Date"])[:10],
                    "open_price":   float(row["Open"])   if pd.notna(row["Open"])  else None,
                    "high_price":   float(row["High"])   if pd.notna(row["High"])  else None,
                    "low_price":    float(row["Low"])    if pd.notna(row["Low"])   else None,
                    "close_price":  float(row["Close"])  if pd.notna(row["Close"]) else None,
                    "volume":       int(row["Volume"])   if pd.notna(row["Volume"])else None,
                    "source":       "Yahoo Finance"
                })

        except Exception as e:
            print(f"  Error fetching {ticker}: {e}")
            continue

    print(f"\nTotal records fetched: {len(all_data)}")
    return all_data


# ── Fetch DOW Index from FRED ──────────────────────────────────
def fetch_dow_index():
    api_key = os.getenv("FRED_API_KEY")
    series = {
        "DJIA":   "Dow Jones Industrial Average",
        "SP500":  "S&P 500 Index",
        "NASDAQCOM": "NASDAQ Composite Index"
    }

    all_data = []

    print("Fetching index data from FRED...")

    for series_id, name in series.items():
        url = (
            f"https://api.stlouisfed.org/fred/series/observations"
            f"?series_id={series_id}"
            f"&observation_start={START_DATE}"
            f"&observation_end={END_DATE}"
            f"&api_key={api_key}"
            f"&file_type=json"
        )

        response = requests.get(url)
        data     = response.json()

        if "observations" not in data:
            print(f"  Error fetching {series_id}: {data}")
            continue

        print(f"  Fetched {len(data['observations'])} records for {series_id}")

        for obs in data["observations"]:
            if obs["value"] == ".":
                continue
            all_data.append({
                "ticker":       series_id,
                "company_name": name,
                "trade_date":   obs["date"],
                "open_price":   None,
                "high_price":   None,
                "low_price":    None,
                "close_price":  float(obs["value"]),
                "volume":       None,
                "source":       "FRED"
            })

    print(f"Total index records: {len(all_data)}")
    return all_data


# ── Load data into Snowflake ───────────────────────────────────
def load_to_snowflake(records):
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        role=os.getenv("SNOWFLAKE_ROLE")
    )

    cursor = conn.cursor()
    cursor.execute("USE SCHEMA DOW30_DB.RAW")

    print(f"\nLoading {len(records)} records into Snowflake...")

    insert_sql = """
        INSERT INTO RAW_DOW30_STAGING (
            ticker, company_name, trade_date,
            open_price, high_price, low_price,
            close_price, volume, source
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    batch = [
        (
            r["ticker"], r["company_name"], r["trade_date"],
            r["open_price"], r["high_price"], r["low_price"],
            r["close_price"], r["volume"], r["source"]
        )
        for r in records
    ]

    # Insert in chunks of 1000
    chunk_size = 1000
    for i in range(0, len(batch), chunk_size):
        chunk = batch[i:i + chunk_size]
        cursor.executemany(insert_sql, chunk)
        print(f"  Inserted {min(i + chunk_size, len(batch))} / {len(batch)} rows")

    conn.commit()
    cursor.close()
    conn.close()

    print("Done! Data loaded into RAW_DOW30_STAGING")


# ── Main ───────────────────────────────────────────────────────
if __name__ == "__main__":
    stock_data = fetch_stock_data()
    index_data = fetch_dow_index()
    all_data   = stock_data + index_data
    load_to_snowflake(all_data)