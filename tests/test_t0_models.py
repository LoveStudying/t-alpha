from datetime import datetime

from t_alpha.strategy.t0_models import (
    T0Eligibility,
    T0StrategyParams,
    T0Trade,
    amount_to_board_lot_shares,
)


def test_amount_to_board_lot_shares_rounds_down_to_100_shares():
    assert amount_to_board_lot_shares(11000, 42.12) == 200
    assert amount_to_board_lot_shares(5000, 80.00) == 0


def test_trade_net_return_and_success_fields():
    trade = T0Trade(
        code="601318.SH",
        signal_time=datetime(2024, 1, 2, 10),
        buy_time=datetime(2024, 1, 2, 11),
        buy_price=40.0,
        buy_amount=12000,
        buy_shares=300,
        sell_time=datetime(2024, 1, 5, 15),
        sell_price=41.2,
        holding_trade_days=3,
        gross_return=0.03,
        net_return=0.0299,
        profit_amount=358.8,
        success=True,
        exit_reason="target",
        reasons=["BOLL lower touch", "RSI turn up"],
    )

    payload = trade.to_dict()

    assert payload["success"] is True
    assert payload["exit_reason"] == "target"
    assert payload["buy_time"] == "2024-01-02 11:00:00"


def test_eligibility_explains_failure_reason():
    eligibility = T0Eligibility(eligible=False, level="invalid", reasons=["sample count below 30"])

    assert eligibility.to_dict()["reasons"] == ["sample count below 30"]


def test_strategy_params_default_values_match_design():
    params = T0StrategyParams()

    assert params.target_return == 0.03
    assert params.max_holding_trade_days == 10
    assert params.trade_cost_rate == 0.0001
    assert params.min_trade_amount == 5000
    assert params.max_trade_amount == 20000
    assert params.min_success_rate == 0.65
