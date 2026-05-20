USE DATABASE DOW30_DB;
USE WAREHOUSE DOW30_WAREHOUSE;

-- ── Task 1: Daily Data Ingestion ───────────────────────────────
CREATE OR REPLACE TASK DOW30_DB.RAW.LOAD_DOW30_TASK
    WAREHOUSE = DOW30_WAREHOUSE
    SCHEDULE  = 'USING CRON 0 6 * * * UTC'
AS
CALL DOW30_DB.HARMONIZED.UPDATE_DOW30_SP();

-- ── Task 2: Daily Metrics Update ──────────────────────────────
CREATE OR REPLACE TASK DOW30_DB.ANALYTICS.UPDATE_DOW30_METRICS_TASK
    WAREHOUSE = DOW30_WAREHOUSE
    SCHEDULE  = 'USING CRON 0 7 * * * UTC'
AS
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
    ON  h.ticker = h2.ticker
    AND h2.trade_date BETWEEN DATEADD(DAY, -30, h.trade_date) AND h.trade_date
WHERE h.is_valid = TRUE
AND   h.trade_date = CURRENT_DATE() - 1
GROUP BY
    h.ticker,
    h.company_name,
    h.trade_date,
    h.close_price,
    h.daily_return;

-- ── Activate both tasks ────────────────────────────────────────
ALTER TASK DOW30_DB.RAW.LOAD_DOW30_TASK RESUME;
ALTER TASK DOW30_DB.ANALYTICS.UPDATE_DOW30_METRICS_TASK RESUME;

-- ── Verify tasks are running ───────────────────────────────────
SHOW TASKS IN DATABASE DOW30_DB;