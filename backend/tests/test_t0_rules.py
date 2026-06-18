import pandas as pd

from t_alpha.strategy.t0_models import T0StrategyParams
from t_alpha.strategy.t0_rules import generate_low_buy_candidates


def _hourly_frame(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "kline_time": pd.date_range("2024-01-02 10:00:00", periods=len(closes), freq="60min"),
            "open": closes,
            "high": [price + 0.2 for price in closes],
            "low": [price - 0.2 for price in closes],
            "close": closes,
            "volume": [1000.0] * len(closes),
            "amount": [100000.0] * len(closes),
        }
    )


def _daily_frame(length: int = 80) -> pd.DataFrame:
    closes = [40.0 + idx * 0.02 for idx in range(length)]
    return pd.DataFrame(
        {
            "kline_time": pd.date_range("2023-10-01", periods=length, freq="B"),
            "open": closes,
            "high": [price + 0.3 for price in closes],
            "low": [price - 0.3 for price in closes],
            "close": closes,
            "volume": [500000.0] * length,
            "amount": [20000000.0] * length,
        }
    )


def test_generate_candidate_when_lower_band_and_momentum_turn():
    hourly = _hourly_frame([40.0] * 25 + [39.0, 38.8, 38.9, 39.1, 39.3])
    daily = _daily_frame()

    candidates = generate_low_buy_candidates("601318.SH", daily, hourly, T0StrategyParams())

    assert candidates
    assert candidates[-1].code == "601318.SH"
    assert candidates[-1].score > 0
    assert any("RSI" in reason or "KDJ" in reason or "BOLL" in reason for reason in candidates[-1].reasons)


def test_no_candidate_when_daily_trend_filter_fails():
    hourly = _hourly_frame([40.0] * 25 + [39.0, 38.8, 38.9, 39.1, 39.3])
    daily = _daily_frame()
    daily["close"] = list(reversed(daily["close"].tolist()))

    candidates = generate_low_buy_candidates("601318.SH", daily, hourly, T0StrategyParams())

    assert candidates == []
