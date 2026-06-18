import pandas as pd

from t_alpha.indicators.technical import atr, boll, kdj, ma, rsi


def test_indicator_outputs_keep_length():
    close = pd.Series([10, 10.2, 10.1, 10.5, 10.4, 10.6, 10.8, 10.7, 10.9, 11.0] * 3)
    high = close + 0.2
    low = close - 0.2

    assert len(ma(close, 5)) == len(close)
    assert len(rsi(close, 6)) == len(close)
    assert len(boll(close, 20)) == len(close)
    assert len(kdj(close, high, low)) == len(close)
    assert len(atr(high, low, close, 14)) == len(close)


def test_kdj_handles_flat_prices_without_infinite_values():
    close = pd.Series([10.0] * 20)
    result = kdj(close, close, close)
    assert not result["j"].dropna().isin([float("inf"), float("-inf")]).any()
