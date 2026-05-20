USE DATABASE DOW30_DB;
USE WAREHOUSE DOW30_WAREHOUSE;

-- ── Stored Procedure: Incremental Update ──────────────────────
-- Reads NEW records from the Stream on RAW table
-- Applies daily return UDF
-- Inserts clean data into HARMONIZED table
-- Only processes NEW data — not everything again

CREATE OR REPLACE PROCEDURE DOW30_DB.HARMONIZED.UPDATE_DOW30_SP()
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'update_dow30'
AS
$$
from snowflake.snowpark import Session

def update_dow30(session: Session) -> str:

    # ── Step 1: Check if Stream has new data ──────────────────
    stream_check = session.sql("""
        SELECT COUNT(*) as cnt 
        FROM DOW30_DB.RAW.DOW30_STREAM
    """).collect()
    
    new_records = stream_check[0]['CNT']
    
    if new_records == 0:
        return "No new records in stream. Nothing to process."
    
    # ── Step 2: Read new records from Stream ──────────────────
    session.sql("""
        INSERT INTO DOW30_DB.HARMONIZED.DOW30_HARMONIZED (
            ticker,
            company_name,
            trade_date,
            open_price,
            high_price,
            low_price,
            close_price,
            volume,
            daily_return,
            is_valid
        )
        SELECT
            s.ticker,
            s.company_name,
            s.trade_date::DATE,
            s.open_price,
            s.high_price,
            s.low_price,
            s.close_price,
            s.volume,
            DOW30_DB.HARMONIZED.CALCULATE_DAILY_RETURN(
                LAG(s.close_price) OVER (
                    PARTITION BY s.ticker 
                    ORDER BY s.trade_date
                ),
                s.close_price
            ) AS daily_return,
            CASE
                WHEN s.close_price IS NULL THEN FALSE
                WHEN s.close_price <= 0    THEN FALSE
                ELSE TRUE
            END AS is_valid
        FROM DOW30_DB.RAW.DOW30_STREAM s
        WHERE s.METADATA$ACTION = 'INSERT'
    """).collect()

    # ── Step 3: Return success message ────────────────────────
    return f"Successfully processed {new_records} new records into HARMONIZED table."
$$;

-- ── Run the stored procedure ──────────────────────────────────
CALL DOW30_DB.HARMONIZED.UPDATE_DOW30_SP();