from __future__ import annotations

import pandas as pd

from t_alpha.indicators.technical import boll, kdj, ma, rsi
from t_alpha.strategy.t0_models import T0SignalCandidate, T0StrategyParams


REQUIRED_COLUMNS = {"kline_time", "open", "high", "low", "close", "volume", "amount"}


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"missing kline columns: {sorted(missing)}")
    prepared = df.copy().sort_values("kline_time").reset_index(drop=True)
    prepared["kline_time"] = pd.to_datetime(prepared["kline_time"])
    for column in ("open", "high", "low", "close", "volume", "amount"):
        prepared[column] = prepared[column].astype(float)
    return prepared


def _daily_trend_passes(daily_df: pd.DataFrame, params: T0StrategyParams) -> bool:
    if len(daily_df) < params.ma_long:
        return False
    close = daily_df["close"].astype(float)
    ma_short_value = ma(close, params.ma_short).iloc[-1]
    ma_long_value = ma(close, params.ma_long).iloc[-1]
    last_close = close.iloc[-1]
    if pd.isna(ma_short_value) or pd.isna(ma_long_value):
        return False
    return bool(ma_short_value > ma_long_value or last_close > ma_long_value)


def generate_low_buy_candidates(
    code: str,
    daily_df: pd.DataFrame,
    hourly_df: pd.DataFrame,
    params: T0StrategyParams,
) -> list[T0SignalCandidate]:
    daily = _prepare(daily_df)
    hourly = _prepare(hourly_df)
    if not _daily_trend_passes(daily, params):
        return []
    if len(hourly) < max(params.boll_n, params.kdj_n, params.rsi_n) + 2:
        return []

    close = hourly["close"].astype(float)
    high = hourly["high"].astype(float)
    low = hourly["low"].astype(float)
    boll_values = boll(close, params.boll_n, params.boll_k)
    rsi_values = rsi(close, params.rsi_n)
    kdj_values = kdj(close, high, low, params.kdj_n)

    candidates: list[T0SignalCandidate] = []
    start = max(params.boll_n, params.kdj_n, params.rsi_n) + 1
    for idx in range(start, len(hourly)):
        last_close = float(close.iloc[idx])
        lower = boll_values["lower"].iloc[idx]
        current_rsi = rsi_values.iloc[idx]
        previous_rsi = rsi_values.iloc[idx - 1]
        current_j = kdj_values["j"].iloc[idx]
        previous_j = kdj_values["j"].iloc[idx - 1]

        touched_lower = pd.notna(lower) and last_close <= float(lower) * params.boll_lower_buffer
        rsi_turn = pd.notna(current_rsi) and pd.notna(previous_rsi) and current_rsi > previous_rsi
        kdj_turn = pd.notna(current_j) and pd.notna(previous_j) and current_j > previous_j

        reasons: list[str] = []
        if touched_lower:
            reasons.append("BOLL lower band touch")
        if rsi_turn:
            reasons.append("RSI turns up")
        if kdj_turn:
            reasons.append("KDJ J turns up")
        if not reasons:
            continue

        lower_gap = 0.0
        if pd.notna(lower) and last_close > 0:
            lower_gap = max(0.0, (float(lower) - last_close) / last_close)
        score = min(1.0, 0.2 * len(reasons) + lower_gap)
        candidates.append(
            T0SignalCandidate(
                code=code,
                signal_time=pd.to_datetime(hourly.loc[idx, "kline_time"]).to_pydatetime(),
                signal_price=last_close,
                score=score,
                reasons=reasons,
            )
        )
    return candidates
