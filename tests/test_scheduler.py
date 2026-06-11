from datetime import datetime

from t_alpha.scheduler.jobs import is_alert_check_time


def test_alert_check_time_only_trade_checkpoints():
    assert is_alert_check_time(datetime(2026, 6, 11, 10, 0))
    assert is_alert_check_time(datetime(2026, 6, 11, 11, 0))
    assert is_alert_check_time(datetime(2026, 6, 11, 13, 0))
    assert is_alert_check_time(datetime(2026, 6, 11, 14, 0))
    assert is_alert_check_time(datetime(2026, 6, 11, 15, 0))
    assert not is_alert_check_time(datetime(2026, 6, 11, 12, 30))
