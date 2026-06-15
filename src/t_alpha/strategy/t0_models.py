from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Literal


EligibilityLevel = Literal["eligible", "observe", "invalid"]
ExitReason = Literal["target", "timeout"]


@dataclass(frozen=True)
class T0StrategyParams:
    target_return: float = 0.03
    max_holding_trade_days: int = 10
    trade_cost_rate: float = 0.0001
    min_trade_amount: int = 5000
    max_trade_amount: int = 20000
    min_3y_trades: int = 60
    observe_min_3y_trades: int = 30
    min_success_rate: float = 0.65
    boll_n: int = 20
    boll_k: float = 2.0
    boll_lower_buffer: float = 1.01
    rsi_n: int = 6
    kdj_n: int = 9
    ma_short: int = 20
    ma_long: int = 60


@dataclass(frozen=True)
class T0SignalCandidate:
    code: str
    signal_time: datetime
    signal_price: float
    score: float
    reasons: list[str]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["signal_time"] = self.signal_time.strftime("%Y-%m-%d %H:%M:%S")
        return data


@dataclass(frozen=True)
class T0Trade:
    code: str
    signal_time: datetime
    buy_time: datetime
    buy_price: float
    buy_amount: int
    buy_shares: int
    sell_time: datetime
    sell_price: float
    holding_trade_days: int
    gross_return: float
    net_return: float
    profit_amount: float
    success: bool
    exit_reason: ExitReason
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("signal_time", "buy_time", "sell_time"):
            data[key] = getattr(self, key).strftime("%Y-%m-%d %H:%M:%S")
        return data


@dataclass(frozen=True)
class T0Metrics:
    trade_count: int
    success_count: int
    failure_count: int
    success_rate: float
    average_return: float
    median_return: float
    average_profit_amount: float
    max_single_loss: float
    max_consecutive_failures: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class T0Eligibility:
    eligible: bool
    level: EligibilityLevel
    reasons: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class T0StrategyReport:
    code: str
    strategy_name: str
    params: T0StrategyParams
    full_metrics: T0Metrics
    train_metrics: T0Metrics
    validation_metrics: T0Metrics
    recent_metrics: T0Metrics
    recent_trades: list[T0Trade]
    eligibility: T0Eligibility
    generated_at: datetime
    disclaimer: str

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "strategy_name": self.strategy_name,
            "params": asdict(self.params),
            "full_metrics": self.full_metrics.to_dict(),
            "train_metrics": self.train_metrics.to_dict(),
            "validation_metrics": self.validation_metrics.to_dict(),
            "recent_metrics": self.recent_metrics.to_dict(),
            "recent_trades": [trade.to_dict() for trade in self.recent_trades],
            "eligibility": self.eligibility.to_dict(),
            "generated_at": self.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "disclaimer": self.disclaimer,
        }


def amount_to_board_lot_shares(amount: int, price: float) -> int:
    if amount <= 0 or price <= 0:
        return 0
    return int(amount // (price * 100) * 100)
