from datetime import datetime

import pandas as pd

from t_alpha.backtest.t0_engine import T0BacktestEngine
from t_alpha.strategy.t0_models import T0SignalCandidate, T0StrategyParams


def _hourly_for_trade() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "kline_time": pd.to_datetime(
                [
                    "2024-01-02 10:00",
                    "2024-01-02 11:00",
                    "2024-01-02 14:00",
                    "2024-01-03 10:00",
                    "2024-01-04 10:00",
                ]
            ),
            "open": [40.0, 40.0, 40.5, 41.1, 40.2],
            "high": [40.2, 41.3, 41.4, 41.5, 40.4],
            "low": [39.8, 39.9, 40.4, 40.9, 39.9],
            "close": [40.0, 40.6, 41.0, 41.2, 40.1],
            "volume": [1000.0] * 5,
            "amount": [40000.0] * 5,
        }
    )


def test_backtest_buys_next_bar_open_and_exits_at_target():
    hourly = _hourly_for_trade()
    candidate = T0SignalCandidate("601318.SH", datetime(2024, 1, 2, 10), 40.0, 1.0, ["test"])
    engine = T0BacktestEngine(T0StrategyParams(target_return=0.03, trade_cost_rate=0.0001))

    trades = engine.run("601318.SH", hourly, [candidate])

    assert len(trades) == 1
    assert trades[0].buy_time == datetime(2024, 1, 2, 11)
    assert trades[0].buy_price == 40.0
    assert trades[0].sell_price == 41.2
    assert trades[0].success is True
    assert trades[0].exit_reason == "target"
    assert round(trades[0].net_return, 4) == 0.0299


def test_backtest_blocks_overlapping_positions():
    hourly = _hourly_for_trade()
    candidates = [
        T0SignalCandidate("601318.SH", datetime(2024, 1, 2, 10), 40.0, 1.0, ["first"]),
        T0SignalCandidate("601318.SH", datetime(2024, 1, 2, 11), 40.6, 1.0, ["overlap"]),
    ]
    engine = T0BacktestEngine(T0StrategyParams())

    trades = engine.run("601318.SH", hourly, candidates)

    assert len(trades) == 1
    assert trades[0].reasons == ["first"]


def test_backtest_times_out_after_max_holding_trade_days():
    hourly = pd.DataFrame(
        {
            "kline_time": pd.date_range("2024-01-02 10:00", periods=20, freq="60min"),
            "open": [40.0] * 20,
            "high": [40.5] * 20,
            "low": [39.5] * 20,
            "close": [40.1] * 20,
            "volume": [1000.0] * 20,
            "amount": [40000.0] * 20,
        }
    )
    candidate = T0SignalCandidate("601318.SH", hourly.loc[0, "kline_time"].to_pydatetime(), 40.0, 1.0, ["test"])
    engine = T0BacktestEngine(T0StrategyParams(max_holding_trade_days=3))

    trades = engine.run("601318.SH", hourly, [candidate])

    assert trades[0].success is False
    assert trades[0].exit_reason == "timeout"
    assert trades[0].holding_trade_days == 3
