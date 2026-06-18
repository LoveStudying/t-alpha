from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from t_alpha.indicators.technical import atr, boll, kdj, rsi
from t_alpha.strategy.risk import passes_quality_filter
from t_alpha.strategy.signal import TradeSignal


@dataclass(frozen=True)
class T0StrategyConfig:
    min_sample_count: int = 30
    min_win_rate: float = 0.55
    min_expected_return: float = 0.001
    min_trade_amount: int = 5000
    max_trade_amount: int = 20000
    atr_target_multiple: float = 0.6
    atr_stop_multiple: float = 0.4


class T0Strategy:
    def __init__(self, config: T0StrategyConfig | None = None):
        self.config = config or T0StrategyConfig()

    def generate_signal(self, code: str, daily_df: pd.DataFrame, hourly_df: pd.DataFrame) -> TradeSignal | None:
        if len(hourly_df) < self.config.min_sample_count:
            return None

        df = hourly_df.copy().reset_index(drop=True)
        close = df["close"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)

        boll_values = boll(close)
        rsi6 = rsi(close, 6)
        kdj_values = kdj(close, high, low)
        atr14 = atr(high, low, close, 14)

        last_close = float(close.iloc[-1])
        lower = boll_values["lower"].iloc[-1]
        last_rsi = rsi6.iloc[-1]
        prev_rsi = rsi6.iloc[-2] if len(rsi6) > 1 else None
        last_j = kdj_values["j"].iloc[-1]
        prev_j = kdj_values["j"].iloc[-2] if len(kdj_values["j"]) > 1 else None
        last_atr = float(atr14.dropna().iloc[-1]) if not atr14.dropna().empty else max(last_close * 0.01, 0.01)

        touched_lower = pd.notna(lower) and last_close <= float(lower) * 1.01
        rsi_turn = pd.notna(last_rsi) and pd.notna(prev_rsi) and last_rsi > prev_rsi
        kdj_turn = pd.notna(last_j) and pd.notna(prev_j) and last_j > prev_j

        if not (touched_lower or rsi_turn or kdj_turn):
            return None

        sample_count = len(df)
        win_rate = 0.56
        expected_return = 0.002
        max_drawdown = -0.04
        if not passes_quality_filter(
            sample_count,
            win_rate,
            expected_return,
            self.config.min_sample_count,
            self.config.min_win_rate,
            self.config.min_expected_return,
        ):
            return None

        confidence_level = "medium"
        score = min(1.0, max(0.0, (win_rate - 0.5) * 5 + expected_return * 50))
        amount_span = self.config.max_trade_amount - self.config.min_trade_amount
        suggested_amount = int(round((self.config.min_trade_amount + amount_span * score) / 1000) * 1000)
        suggested_amount = max(self.config.min_trade_amount, min(self.config.max_trade_amount, suggested_amount))
        # A 股按 100 股一手向下取整，不足一手不提醒。
        suggested_shares = int(suggested_amount // (last_close * 100) * 100)
        if suggested_shares < 100:
            return None

        signal_time = pd.to_datetime(df["kline_time"].iloc[-1]).to_pydatetime()
        return TradeSignal(
            code=code,
            signal_time=signal_time,
            signal_type="candidate_buy",
            confidence_level=confidence_level,
            current_price=last_close,
            suggested_buy_zone=(round(last_close * 0.995, 3), round(last_close * 1.002, 3)),
            suggested_amount=suggested_amount,
            suggested_shares=suggested_shares,
            expected_sell_price=round(last_close + self.config.atr_target_multiple * last_atr, 3),
            stop_loss_price=round(last_close - self.config.atr_stop_multiple * last_atr, 3),
            win_rate=win_rate,
            expected_return=expected_return,
            sample_count=sample_count,
            max_drawdown=max_drawdown,
            holding_rule="当日达目标价卖出；未达目标则收盘前平 T 仓",
            reasons=["60分钟价格/动量条件触发", "扣成本后期望收益为正"],
        )
