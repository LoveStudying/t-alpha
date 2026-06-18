from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import median

from t_alpha.strategy.t0_models import T0Eligibility, T0Metrics, T0StrategyParams, T0Trade


def summarize_trades(trades: list[T0Trade]) -> T0Metrics:
    if not trades:
        return T0Metrics(
            trade_count=0,
            success_count=0,
            failure_count=0,
            success_rate=0.0,
            average_return=0.0,
            median_return=0.0,
            average_profit_amount=0.0,
            max_single_loss=0.0,
            max_consecutive_failures=0,
        )

    success_count = sum(1 for trade in trades if trade.success)
    returns = [trade.net_return for trade in trades]
    profits = [trade.profit_amount for trade in trades]
    max_consecutive_failures = 0
    current_failures = 0
    for trade in trades:
        if trade.success:
            current_failures = 0
            continue
        current_failures += 1
        max_consecutive_failures = max(max_consecutive_failures, current_failures)

    return T0Metrics(
        trade_count=len(trades),
        success_count=success_count,
        failure_count=len(trades) - success_count,
        success_rate=success_count / len(trades),
        average_return=sum(returns) / len(returns),
        median_return=median(returns),
        average_profit_amount=sum(profits) / len(profits),
        max_single_loss=min(returns),
        max_consecutive_failures=max_consecutive_failures,
    )


def evaluate_eligibility(full_metrics: T0Metrics, validation_metrics: T0Metrics, params: T0StrategyParams) -> T0Eligibility:
    reasons: list[str] = []
    if full_metrics.trade_count < params.observe_min_3y_trades:
        return T0Eligibility(False, "invalid", ["3-year trade count below observation threshold"])
    if full_metrics.trade_count < params.min_3y_trades:
        reasons.append("3-year trade count below monitor threshold")
    if full_metrics.success_rate <= params.min_success_rate:
        reasons.append("3-year success rate below gate")
    if validation_metrics.success_rate <= params.min_success_rate:
        reasons.append("validation success rate below gate")
    if full_metrics.average_return <= 0:
        reasons.append("average net return is not positive")

    if reasons:
        level = "observe" if full_metrics.trade_count >= params.observe_min_3y_trades else "invalid"
        return T0Eligibility(False, level, reasons)
    return T0Eligibility(True, "eligible", [])


@dataclass(frozen=True)
class T0OptimizationResult:
    params: T0StrategyParams
    full_metrics: T0Metrics
    train_metrics: T0Metrics
    validation_metrics: T0Metrics
    recent_metrics: T0Metrics
    recent_trades: list[T0Trade]
    eligibility: T0Eligibility

    def to_dict(self) -> dict:
        return {
            "params": asdict(self.params),
            "full_metrics": self.full_metrics.to_dict(),
            "train_metrics": self.train_metrics.to_dict(),
            "validation_metrics": self.validation_metrics.to_dict(),
            "recent_metrics": self.recent_metrics.to_dict(),
            "recent_trades": [trade.to_dict() for trade in self.recent_trades],
            "eligibility": self.eligibility.to_dict(),
        }
