from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from t_alpha.backtest.metrics import summarize_returns


@dataclass(frozen=True)
class BacktestConfig:
    commission_rate: float = 0.0001
    stamp_tax_rate: float = 0.0005
    slippage_bps: float = 1.0


@dataclass(frozen=True)
class BacktestResult:
    code: str
    metrics: dict[str, float]
    trades: list[dict]


class BacktestEngine:
    def __init__(self, config: BacktestConfig):
        self.config = config

    def _cost_rate(self) -> float:
        return self.config.commission_rate * 2 + self.config.stamp_tax_rate + self.config.slippage_bps / 10000 * 2

    def run(self, code: str, hourly_df: pd.DataFrame) -> BacktestResult:
        trades: list[dict] = []
        returns: list[float] = []
        df = hourly_df.reset_index(drop=True)
        cost = self._cost_rate()

        for idx in range(20, len(df) - 1):
            current = float(df.loc[idx, "close"])
            next_open = float(df.loc[idx + 1, "open"])
            if current <= 0 or next_open <= 0:
                continue
            # 用下一根 K 线开盘价成交，避免使用同一根 K 线未来 high/low。
            gross_return = (next_open - current) / current
            net_return = gross_return - cost
            returns.append(net_return)
            trades.append(
                {
                    "signal_time": str(df.loc[idx, "kline_time"]),
                    "entry_price": current,
                    "exit_price": next_open,
                    "net_return": net_return,
                }
            )

        return BacktestResult(code=code, metrics=summarize_returns(returns), trades=trades)
