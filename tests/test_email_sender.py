from datetime import datetime

from t_alpha.notification.email_sender import build_alert_email
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
