from __future__ import annotations

import pandas as pd

from t_alpha.strategy.t0_models import (
    T0SignalCandidate,
    T0StrategyParams,
    T0Trade,
    amount_to_board_lot_shares,
)


class T0BacktestEngine:
    def __init__(self, params: T0StrategyParams):
        self.params = params

    def run(self, code: str, hourly_df: pd.DataFrame, candidates: list[T0SignalCandidate]) -> list[T0Trade]:
        if hourly_df.empty or not candidates:
            return []

        df = hourly_df.copy().sort_values("kline_time").reset_index(drop=True)
        df["kline_time"] = pd.to_datetime(df["kline_time"])
        for column in ("open", "high", "low", "close"):
            df[column] = df[column].astype(float)

        candidates_by_time = sorted(candidates, key=lambda item: item.signal_time)
        trades: list[T0Trade] = []
        blocked_until_index = -1
        opened_trade_dates: set[object] = set()

        for candidate in candidates_by_time:
            signal_time = pd.to_datetime(candidate.signal_time)
            signal_rows = df.index[df["kline_time"] == signal_time].tolist()
            if not signal_rows:
                signal_rows = df.index[df["kline_time"] > signal_time].tolist()
                if not signal_rows:
                    continue
                signal_index = signal_rows[0] - 1
            else:
                signal_index = signal_rows[0]

            buy_index = signal_index + 1
            if buy_index <= blocked_until_index or buy_index >= len(df):
                continue
            buy_date = pd.to_datetime(df.loc[buy_index, "kline_time"]).date()
            if buy_date in opened_trade_dates:
                continue

            trade = self._simulate_trade(code, df, candidate, buy_index)
            if trade is None:
                continue
            trades.append(trade)
            opened_trade_dates.add(buy_date)
            sell_matches = df.index[df["kline_time"] == pd.to_datetime(trade.sell_time)].tolist()
            if sell_matches:
                blocked_until_index = sell_matches[0]

        return trades

    def _simulate_trade(
        self,
        code: str,
        df: pd.DataFrame,
        candidate: T0SignalCandidate,
        buy_index: int,
    ) -> T0Trade | None:
        buy_row = df.loc[buy_index]
        buy_price = float(buy_row["open"])
        buy_amount = self._trade_amount(candidate.score)
        buy_shares = amount_to_board_lot_shares(buy_amount, buy_price)
        if buy_shares < 100:
            return None

        target_price = round(buy_price * (1 + self.params.target_return), 3)
        buy_date = pd.to_datetime(buy_row["kline_time"]).date()
        exit_index = len(df) - 1
        exit_reason = "timeout"
        sell_price = float(df.loc[exit_index, "close"])
        holding_days = self.params.max_holding_trade_days

        seen_dates: list[object] = []
        for idx in range(buy_index, len(df)):
            row_time = pd.to_datetime(df.loc[idx, "kline_time"])
            row_date = row_time.date()
            if row_date not in seen_dates:
                seen_dates.append(row_date)
            current_holding_days = max(1, len([day for day in seen_dates if day >= buy_date]))

            if float(df.loc[idx, "high"]) >= target_price:
                exit_index = idx
                exit_reason = "target"
                sell_price = target_price
                holding_days = current_holding_days
                break

            if current_holding_days >= self.params.max_holding_trade_days:
                exit_index = idx
                exit_reason = "timeout"
                sell_price = float(df.loc[idx, "close"])
                holding_days = current_holding_days
                break

        gross_return = (sell_price - buy_price) / buy_price
        net_return = gross_return - self.params.trade_cost_rate
        profit_amount = (sell_price - buy_price) * buy_shares - buy_price * buy_shares * self.params.trade_cost_rate

        return T0Trade(
            code=code,
            signal_time=candidate.signal_time,
            buy_time=pd.to_datetime(buy_row["kline_time"]).to_pydatetime(),
            buy_price=buy_price,
            buy_amount=buy_amount,
            buy_shares=buy_shares,
            sell_time=pd.to_datetime(df.loc[exit_index, "kline_time"]).to_pydatetime(),
            sell_price=sell_price,
            holding_trade_days=holding_days,
            gross_return=gross_return,
            net_return=net_return,
            profit_amount=profit_amount,
            success=exit_reason == "target",
            exit_reason=exit_reason,
            reasons=candidate.reasons,
        )

    def _trade_amount(self, score: float) -> int:
        bounded_score = max(0.0, min(1.0, score))
        span = self.params.max_trade_amount - self.params.min_trade_amount
        amount = self.params.min_trade_amount + span * bounded_score
        return int(round(amount / 1000) * 1000)
