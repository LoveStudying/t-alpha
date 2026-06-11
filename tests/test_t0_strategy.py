import pandas as pd

from t_alpha.strategy.risk import passes_quality_filter
from t_alpha.strategy.t0_strategy import T0Strategy, T0StrategyConfig


def test_quality_filter_thresholds():
    assert passes_quality_filter(30, 0.56, 0.002, 30, 0.55, 0.001)
    assert not passes_quality_filter(29, 0.56, 0.002, 30, 0.55, 0.001)


def test_strategy_returns_signal_for_turning_hourly_data():
    closes = [10.0] * 25 + [9.5, 9.4, 9.45, 9.5, 9.6]
    df = pd.DataFrame(
        {
            "kline_time": pd.date_range("2024-01-01", periods=len(closes), freq="h"),
            "open": closes,
            "high": [x + 0.2 for x in closes],
            "low": [x - 0.2 for x in closes],
            "close": closes,
            "volume": [1000] * len(closes),
            "amount": [10000] * len(closes),
        }
    )
    strategy = T0Strategy(T0StrategyConfig(min_sample_count=30))

    signal = strategy.generate_signal("601318.SH", df, df)

    assert signal is not None
    assert signal.code == "601318.SH"
    assert signal.suggested_shares >= 100
    assert "不构成投资建议" in signal.disclaimer
