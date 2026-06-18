import pandas as pd

from t_alpha.backtest.engine import BacktestConfig, BacktestEngine
from t_alpha.backtest.metrics import summarize_returns


def test_summarize_returns_counts_wins():
    metrics = summarize_returns([0.01, -0.005, 0.002])
    assert metrics["sample_count"] == 3
    assert metrics["win_rate"] == 2 / 3
    assert metrics["expected_return"] > 0


def test_backtest_engine_returns_metrics():
    df = pd.DataFrame(
        {
            "kline_time": pd.date_range("2024-01-01", periods=40, freq="h"),
            "open": [10.0] * 40,
            "high": [10.2] * 40,
            "low": [9.8] * 40,
            "close": [10.0 + (i % 3) * 0.02 for i in range(40)],
            "volume": [1000] * 40,
            "amount": [10000] * 40,
        }
    )
    engine = BacktestEngine(BacktestConfig(commission_rate=0.0001, stamp_tax_rate=0.0005, slippage_bps=1))

    result = engine.run("601318.SH", df)

    assert result.code == "601318.SH"
    assert "sample_count" in result.metrics
