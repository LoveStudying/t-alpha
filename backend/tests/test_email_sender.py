from datetime import datetime

from t_alpha.notification.email_sender import build_alert_email, build_t0_alert_email, build_t0_sell_alert_email
from t_alpha.strategy.signal import TradeSignal


def test_build_alert_email_contains_signal_numbers():
    signal = TradeSignal(
        code="601318.SH",
        signal_time=datetime(2026, 6, 11, 10, 0),
        signal_type="candidate_buy",
        confidence_level="medium",
        current_price=50.0,
        suggested_buy_zone=(49.8, 50.1),
        suggested_amount=10000,
        suggested_shares=200,
        expected_sell_price=50.6,
        stop_loss_price=49.6,
        win_rate=0.587,
        expected_return=0.0068,
        sample_count=84,
        max_drawdown=-0.041,
        holding_rule="当日达目标价卖出；未达目标则收盘前平 T 仓",
        reasons=["RSI低位回升"],
    )

    subject, body = build_alert_email(signal)

    assert "601318.SH" in subject
    assert "58.70%" in subject
    assert "10000" in body
    assert "200" in body
    assert "50.6" in body
    assert "不构成投资建议" in body

def test_build_t0_alert_email_contains_recent_summary():
    payload = {
        "code": "601318.SH",
        "signal_time": "2024-01-02 10:00:00",
        "current_price": 40.0,
        "suggested_buy_zone": [39.8, 40.1],
        "suggested_amount": 12000,
        "suggested_shares": 300,
        "target_sell_price": 41.2,
        "max_holding_trade_days": 10,
        "full_success_rate": 0.66,
        "full_trade_count": 60,
        "recent_success_rate": 0.70,
        "recent_trade_count": 5,
        "reasons": ["BOLL lower band touch"],
    }

    subject, body = build_t0_alert_email(payload)

    assert "[T0 buy alert]" in subject
    assert "target sell price: 41.2" in body
    assert "recent 3m success rate: 70.00%" in body


def test_build_t0_sell_alert_email_contains_exit_reason_and_profit():
    payload = {
        "code": "601318.SH",
        "signal_time": "2024-01-02 10:00:00",
        "buy_alert_time": "2024-01-02 10:05:00",
        "reference_buy_price": 40.0,
        "suggested_shares": 300,
        "target_sell_price": 41.2,
        "sell_alert_time": "2024-01-04 10:00:00",
        "current_price": 41.25,
        "trigger_price": 41.2,
        "sell_alert_type": "target",
        "holding_trade_days": 2,
        "gross_return": 0.03,
        "net_return": 0.0299,
        "estimated_profit_amount": 360.0,
        "position_status": "closed",
    }

    subject, body = build_t0_sell_alert_email(payload)

    assert "[T0 sell alert]" in subject
    assert "exit type: target" in body
    assert "virtual position status: closed" in body
