USE DATABASE DOW30_DB;
USE WAREHOUSE DOW30_WAREHOUSE;

-- ── Python UDF: Calculate 30-Day Volatility ───────────────────
-- Takes an array of closing prices
-- Returns the annualized volatility (standard deviation of returns)
-- This is a key metric used by traders and analysts

CREATE OR REPLACE FUNCTION DOW30_DB.HARMONIZED.CALCULATE_VOLATILITY(
    prices ARRAY
)
RETURNS FLOAT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('numpy')
HANDLER = 'calculate_volatility'
AS
$$
import numpy as np

def calculate_volatility(prices):
    if prices is None or len(prices) < 2:
        return None
    
    # Convert to numpy array
    price_array = np.array([float(p) for p in prices if p is not None])
    
    if len(price_array) < 2:
        return None
    
    # Calculate daily returns
    daily_returns = np.diff(price_array) / price_array[:-1]
    
    # Annualized volatility (multiply by sqrt of 252 trading days)
    volatility = float(np.std(daily_returns) * np.sqrt(252))
    
    return round(volatility, 6)
$$;

-- Test it with sample prices
SELECT DOW30_DB.HARMONIZED.CALCULATE_VOLATILITY(
    ARRAY_CONSTRUCT(100, 102, 98, 105, 103, 107, 104, 109, 106, 110)
) AS test_volatility;