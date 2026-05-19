--  Create warehouse and database:

CREATE WAREHOUSE DOW30_WAREHOUSE
    WITH WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

CREATE DATABASE DOW30_DB;

-- Create the 3 schemas:
CREATE SCHEMA DOW30_DB.RAW;
CREATE SCHEMA DOW30_DB.HARMONIZED;
CREATE SCHEMA DOW30_DB.ANALYTICS;


-- Create RAW table:

USE SCHEMA DOW30_DB.RAW;

CREATE TABLE RAW_DOW30_STAGING (
    ticker          VARCHAR(10),
    company_name    VARCHAR(100),
    trade_date      DATE,
    open_price      FLOAT,
    high_price      FLOAT,
    low_price       FLOAT,
    close_price     FLOAT,
    volume          BIGINT,
    source          VARCHAR(50),
    loaded_at       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Create Stream on RAW table:
CREATE STREAM DOW30_DB.RAW.DOW30_STREAM
    ON TABLE DOW30_DB.RAW.RAW_DOW30_STAGING
    APPEND_ONLY = TRUE;


-- Create HARMONIZED table:
USE SCHEMA DOW30_DB.HARMONIZED;

CREATE TABLE DOW30_HARMONIZED (
    ticker              VARCHAR(10),
    company_name        VARCHAR(100),
    trade_date          DATE,
    open_price          FLOAT,
    high_price          FLOAT,
    low_price           FLOAT,
    close_price         FLOAT,
    volume              BIGINT,
    daily_return        FLOAT,
    is_valid            BOOLEAN,
    harmonized_at       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Create ANALYTICS tables:
USE SCHEMA DOW30_DB.ANALYTICS;

CREATE TABLE DAILY_METRICS (
    ticker              VARCHAR(10),
    company_name        VARCHAR(100),
    trade_date          DATE,
    close_price         FLOAT,
    daily_return        FLOAT,
    volatility_30d      FLOAT,
    avg_volume_30d      FLOAT,
    updated_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE MONTHLY_METRICS (
    ticker              VARCHAR(10),
    company_name        VARCHAR(100),
    year                INTEGER,
    month               INTEGER,
    monthly_return      FLOAT,
    avg_close           FLOAT,
    avg_volume          FLOAT,
    volatility          FLOAT,
    updated_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);