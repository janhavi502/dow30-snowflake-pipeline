USE DATABASE DOW30_DB;
USE WAREHOUSE DOW30_WAREHOUSE;

-- ── SQL UDF: Calculate Daily Return Percentage ─────────────────
-- Takes previous close and current close
-- Returns the percentage change between the two
-- Example: prev=100, curr=105 → returns 5.0 (meaning +5%)

CREATE OR REPLACE FUNCTION DOW30_DB.HARMONIZED.CALCULATE_DAILY_RETURN(
    prev_close FLOAT,
    curr_close FLOAT
)
RETURNS FLOAT
LANGUAGE SQL
AS
$$
    CASE
        WHEN prev_close IS NULL OR prev_close = 0 THEN NULL
        WHEN curr_close IS NULL THEN NULL
        ELSE ROUND(((curr_close - prev_close) / prev_close) * 100, 4)
    END
$$;

-- Test it
SELECT DOW30_DB.HARMONIZED.CALCULATE_DAILY_RETURN(100, 105) AS test_return;
-- Expected output: 5.0

SELECT DOW30_DB.HARMONIZED.CALCULATE_DAILY_RETURN(150.25, 148.10) AS test_return;
-- Expected output: -1.4309 (negative because price dropped)