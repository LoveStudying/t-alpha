from datetime import datetime

from t_alpha.scheduler.jobs import T0MonitorJob, is_alert_check_time


def test_alert_check_time_only_trade_checkpoints():
    assert is_alert_check_time(datetime(2026, 6, 11, 10, 0))
    assert is_alert_check_time(datetime(2026, 6, 11, 11, 0))
    assert is_alert_check_time(datetime(2026, 6, 11, 13, 0))
    assert is_alert_check_time(datetime(2026, 6, 11, 14, 0))
    assert is_alert_check_time(datetime(2026, 6, 11, 15, 0))
    assert not is_alert_check_time(datetime(2026, 6, 11, 12, 30))


class FakeMonitorService:
    def __init__(self):
        self.opened = []

    def list_enabled_t0_codes(self):
        return ["601318.SH"]

    def get_open_t0_position(self, code):
        return None

    def generate_realtime_signal(self, code, now):
        return {"code": code, "signal_time": now.strftime("%Y-%m-%d %H:%M:%S")}

    def mark_position_open(self, code, payload):
        self.opened.append((code, payload))


class FakeEmailSender:
    def __init__(self):
        self.messages = []

    def send_t0_signal(self, payload):
        self.messages.append(payload)


def test_t0_monitor_job_sends_buy_signal_and_opens_position():
    service = FakeMonitorService()
    sender = FakeEmailSender()
    job = T0MonitorJob(lambda: [20240104], service, sender)

    sent_count = job.run_once(datetime(2024, 1, 4, 10, 0))

    assert sent_count == 1
    assert sender.messages[0]["code"] == "601318.SH"
    assert service.opened[0][0] == "601318.SH"


class FakeOpenPosition:
    payload_json = '{"code": "601318.SH", "reference_buy_price": 40.0, "target_sell_price": 41.2, "suggested_shares": 300, "max_holding_trade_days": 10}'


class FakeSellMonitorService(FakeMonitorService):
    def __init__(self):
        super().__init__()
        self.closed = []

    def get_open_t0_position(self, code):
        return FakeOpenPosition()

    def get_current_price(self, code):
        return 41.25

    def holding_trade_days(self, position, now):
        return 2

    def generate_sell_signal(self, position_payload, current_price, holding_trade_days, now):
        return {"code": "601318.SH", "exit_reason": "target", "sell_alert_type": "target"}

    def mark_position_closed(self, position, payload):
        self.closed.append(payload)


class FakeSellEmailSender(FakeEmailSender):
    def send_t0_sell_signal(self, payload):
        self.messages.append(payload)


def test_t0_monitor_job_sends_sell_signal_before_new_buy_signal():
    service = FakeSellMonitorService()
    sender = FakeSellEmailSender()
    job = T0MonitorJob(lambda: [20240104], service, sender)

    sent_count = job.run_once(datetime(2024, 1, 4, 10, 0))

    assert sent_count == 1
    assert sender.messages[0]["exit_reason"] == "target"
    assert service.closed[0]["sell_alert_type"] == "target"
