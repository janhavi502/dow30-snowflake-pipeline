import os
import pytest
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

# ── Snowflake Connection ───────────────────────────────────────
@pytest.fixture(scope="module")
def conn():
    connection = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        role=os.getenv("SNOWFLAKE_ROLE")
    )
    yield connection
    connection.close()


# ── SQL UDF Tests ──────────────────────────────────────────────
class TestDailyReturnUDF:

    def test_positive_return(self, conn):
        # Price went up from 100 to 105 = +5%
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DOW30_DB.HARMONIZED.CALCULATE_DAILY_RETURN(100, 105)
        """)
        result = cursor.fetchone()[0]
        assert result == pytest.approx(5.0, rel=1e-3)

    def test_negative_return(self, conn):
        # Price dropped from 150.25 to 148.10 = -1.4309%
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DOW30_DB.HARMONIZED.CALCULATE_DAILY_RETURN(150.25, 148.10)
        """)
        result = cursor.fetchone()[0]
        assert result == pytest.approx(-1.4309, rel=1e-3)

    def test_zero_prev_close_returns_null(self, conn):
        # Division by zero should return NULL
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DOW30_DB.HARMONIZED.CALCULATE_DAILY_RETURN(0, 105)
        """)
        result = cursor.fetchone()[0]
        assert result is None

    def test_null_prev_close_returns_null(self, conn):
        # NULL input should return NULL
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DOW30_DB.HARMONIZED.CALCULATE_DAILY_RETURN(NULL, 105)
        """)
        result = cursor.fetchone()[0]
        assert result is None

    def test_null_curr_close_returns_null(self, conn):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DOW30_DB.HARMONIZED.CALCULATE_DAILY_RETURN(100, NULL)
        """)
        result = cursor.fetchone()[0]
        assert result is None

    def test_no_change_returns_zero(self, conn):
        # Same price = 0% return
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DOW30_DB.HARMONIZED.CALCULATE_DAILY_RETURN(100, 100)
        """)
        result = cursor.fetchone()[0]
        assert result == pytest.approx(0.0, abs=1e-3)


# ── Python UDF Tests ───────────────────────────────────────────
class TestVolatilityUDF:

    def test_volatility_returns_float(self, conn):
        # Should return a float value
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DOW30_DB.HARMONIZED.CALCULATE_VOLATILITY(
                ARRAY_CONSTRUCT(100, 102, 98, 105, 103, 107, 104, 109, 106, 110)
            )
        """)
        result = cursor.fetchone()[0]
        assert result is not None
        assert isinstance(result, float)

    def test_volatility_is_positive(self, conn):
        # Volatility is always positive
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DOW30_DB.HARMONIZED.CALCULATE_VOLATILITY(
                ARRAY_CONSTRUCT(100, 102, 98, 105, 103, 107, 104, 109, 106, 110)
            )
        """)
        result = cursor.fetchone()[0]
        assert result > 0

    def test_stable_prices_low_volatility(self, conn):
        # Prices barely moving = low volatility
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DOW30_DB.HARMONIZED.CALCULATE_VOLATILITY(
                ARRAY_CONSTRUCT(100, 100.1, 99.9, 100.2, 100.1, 99.8, 100.3, 100.1)
            )
        """)
        result = cursor.fetchone()[0]
        assert result < 0.5

    def test_volatile_prices_high_volatility(self, conn):
        # Prices swinging wildly = high volatility
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DOW30_DB.HARMONIZED.CALCULATE_VOLATILITY(
                ARRAY_CONSTRUCT(100, 120, 80, 130, 70, 140, 60, 150, 50, 160)
            )
        """)
        result = cursor.fetchone()[0]
        assert result > 1.0

    def test_null_input_returns_null(self, conn):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DOW30_DB.HARMONIZED.CALCULATE_VOLATILITY(NULL)
        """)
        result = cursor.fetchone()[0]
        assert result is None


# ── Data Quality Tests ─────────────────────────────────────────
class TestDataQuality:

    def test_raw_table_not_empty(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM DOW30_DB.RAW.RAW_DOW30_STAGING")
        count = cursor.fetchone()[0]
        assert count > 0

    def test_harmonized_table_not_empty(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM DOW30_DB.HARMONIZED.DOW30_HARMONIZED")
        count = cursor.fetchone()[0]
        assert count > 0

    def test_all_30_tickers_present(self, conn):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT ticker)
            FROM DOW30_DB.RAW.RAW_DOW30_STAGING
            WHERE source = 'Yahoo Finance'
        """)
        count = cursor.fetchone()[0]
        assert count == 30

    def test_date_range_starts_from_2020(self, conn):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MIN(trade_date)
            FROM DOW30_DB.RAW.RAW_DOW30_STAGING
        """)
        min_date = cursor.fetchone()[0]
        assert str(min_date) >= "2020-01-01"

    def test_no_negative_prices(self, conn):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM DOW30_DB.RAW.RAW_DOW30_STAGING
            WHERE close_price < 0
        """)
        count = cursor.fetchone()[0]
        assert count == 0

    def test_analytics_daily_metrics_not_empty(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM DOW30_DB.ANALYTICS.DAILY_METRICS")
        count = cursor.fetchone()[0]
        assert count > 0

    def test_analytics_monthly_metrics_not_empty(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM DOW30_DB.ANALYTICS.MONTHLY_METRICS")
        count = cursor.fetchone()[0]
        assert count > 0