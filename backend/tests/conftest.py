import pandas as pd
import pytest


@pytest.fixture
def sample_kline_df():
    return pd.DataFrame(
        {
            "kline_time": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
            "open": [10.0, 10.2, 10.1],
            "high": [10.3, 10.4, 10.5],
            "low": [9.9, 10.0, 10.0],
            "close": [10.2, 10.1, 10.4],
            "volume": [1000, 1200, 1500],
            "amount": [10200.0, 12120.0, 15600.0],
        }
    )
