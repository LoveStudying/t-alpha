from datetime import datetime

from t_alpha.backtest.t0_optimizer import (
    T0OptimizationResult,
    evaluate_eligibility,
    summarize_trades,
)
from t_alpha.strategy.t0_models import T0StrategyParams, T0Trade


def _trade(success: bool, net_return: float, day: int) -> T0Trade:
    return T0Trade(
        code="601318.SH",
        signal_time=datetime(2024, 1, day, 10),
        buy_time=datetime(2024, 1, day, 11),
        buy_price=40.0,
        buy_amount=12000,
        buy_shares=300,
        sell_time=datetime(2024, 1, day, 15),
        sell_price=40.0 * (1 + net_return),
        holding_trade_days=1,
        gross_return=net_return,
        net_return=net_return,
        profit_amount=12000 * net_return,
        success=success,
        exit_reason="target" if success else "timeout",
    )


def test_summarize_trades_counts_success_and_consecutive_failures():
    trades = [_trade(True, 0.03, 2), _trade(False, -0.01, 3), _trade(False, -0.02, 4)]

    metrics = summarize_trades(trades)

    assert metrics.trade_count == 3
    assert metrics.success_count == 1
    assert metrics.failure_count == 2
    assert metrics.max_consecutive_failures == 2
    assert metrics.max_single_loss == -0.02


def test_evaluate_eligibility_requires_sample_rate_and_positive_return():
    params = T0StrategyParams(min_3y_trades=3, observe_min_3y_trades=2, min_success_rate=0.65)
    full = summarize_trades([_trade(True, 0.03, 2), _trade(True, 0.03, 3), _trade(False, -0.01, 4)])
    validation = summarize_trades([_trade(True, 0.03, 5), _trade(True, 0.03, 6)])

    eligibility = evaluate_eligibility(full, validation, params)

    assert eligibility.eligible is True
    assert eligibility.level == "eligible"


def test_optimization_result_serializes_report():
    metrics = summarize_trades([_trade(True, 0.03, 2)])
    result = T0OptimizationResult(
        params=T0StrategyParams(),
        full_metrics=metrics,
        train_metrics=metrics,
        validation_metrics=metrics,
        recent_metrics=metrics,
        recent_trades=[],
        eligibility=evaluate_eligibility(metrics, metrics, T0StrategyParams()),
    )

    assert result.to_dict()["params"]["target_return"] == 0.03
