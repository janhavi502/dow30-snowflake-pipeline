USE DATABASE DOW30_DB;
USE WAREHOUSE DOW30_WAREHOUSE;

-- ── Populate DAILY_METRICS ─────────────────────────────────────
INSERT INTO DOW30_DB.ANALYTICS.DAILY_METRICS (
    ticker,
    company_name,
    trade_date,
    close_price,
    daily_return,
    volatility_30d,
    avg_volume_30d,
    updated_at
)
SELECT
    h.ticker,
    h.company_name,
    h.trade_date,
    h.close_price,
    h.daily_return,
    DOW30_DB.HARMONIZED.CALCULATE_VOLATILITY(
        ARRAY_AGG(h2.close_price) WITHIN GROUP (ORDER BY h2.trade_date)
    ) AS volatility_30d,
    AVG(h2.volume) AS avg_volume_30d,
    CURRENT_TIMESTAMP()
FROM DOW30_DB.HARMONIZED.DOW30_HARMONIZED h
LEFT JOIN DOW30_DB.HARMONIZED.DOW30_HARMONIZED h2
    ON h.ticker = h2.ticker
    AND h2.trade_date BETWEEN DATEADD(DAY, -30, h.trade_date) AND h.trade_date
WHERE h.is_valid = TRUE
GROUP BY
    h.ticker,
    h.company_name,
    h.trade_date,
    h.close_price,
    h.daily_return;

-- ── Populate MONTHLY_METRICS ───────────────────────────────────
INSERT INTO DOW30_DB.ANALYTICS.MONTHLY_METRICS (
    ticker,
    company_name,
    year,
    month,
    monthly_return,
    avg_close,
    avg_volume,
    volatility,
    updated_at
)
SELECT
    ticker,
    company_name,
    YEAR(trade_date)  AS year,
    MONTH(trade_date) AS month,
    ROUND(
        ((MAX(close_price) - MIN(close_price)) / MIN(close_price)) * 100
    , 4) AS monthly_return,
    ROUND(AVG(close_price), 4)  AS avg_close,
    ROUND(AVG(volume), 0)       AS avg_volume,
    DOW30_DB.HARMONIZED.CALCULATE_VOLATILITY(
        ARRAY_AGG(close_price) WITHIN GROUP (ORDER BY trade_date)
    ) AS volatility,
    CURRENT_TIMESTAMP()
FROM DOW30_DB.HARMONIZED.DOW30_HARMONIZED
WHERE is_valid = TRUE
GROUP BY
    ticker,
    company_name,
    YEAR(trade_date),
    MONTH(trade_date);

-- ── Useful analytics queries ───────────────────────────────────

-- Top 5 best performing stocks by average monthly return
SELECT
    ticker,
    company_name,
    ROUND(AVG(monthly_return), 2) AS avg_monthly_return,
    ROUND(AVG(volatility), 4)     AS avg_volatility
FROM DOW30_DB.ANALYTICS.MONTHLY_METRICS
WHERE ticker NOT IN ('DJIA', 'SP500', 'NASDAQCOM')
GROUP BY ticker, company_name
ORDER BY avg_monthly_return DESC
LIMIT 5;

-- Most volatile stocks
SELECT
    ticker,
    company_name,
    ROUND(AVG(volatility_30d), 4) AS avg_volatility
FROM DOW30_DB.ANALYTICS.DAILY_METRICS
WHERE ticker NOT IN ('DJIA', 'SP500', 'NASDAQCOM')
GROUP BY ticker, company_name
ORDER BY avg_volatility DESC
LIMIT 5;

-- Monthly returns for a specific stock (AAPL)
SELECT
    year,
    month,
    monthly_return,
    avg_close
FROM DOW30_DB.ANALYTICS.MONTHLY_METRICS
WHERE ticker = 'AAPL'
ORDER BY year, month;