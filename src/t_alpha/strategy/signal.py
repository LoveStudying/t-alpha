from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

from t_alpha.constants import DISCLAIMER


@dataclass(frozen=True)
class TradeSignal:
    code: str
    signal_time: datetime
    signal_type: str
    confidence_level: str
    current_price: float
    suggested_buy_zone: tuple[float, float]
    suggested_amount: int
    suggested_shares: int
    expected_sell_price: float
    stop_loss_price: float
    win_rate: float
    expected_return: float
    sample_count: int
    max_drawdown: float
    holding_rule: str
    reasons: list[str]
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict:
        data = asdict(self)
        data["signal_time"] = self.signal_time.strftime("%Y-%m-%d %H:%M:%S")
        return data
