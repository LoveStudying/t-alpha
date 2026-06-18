from datetime import datetime
import json


CHECKPOINTS = {(10, 0), (11, 0), (13, 0), (14, 0), (15, 0)}


def is_alert_check_time(now: datetime) -> bool:
    return (now.hour, now.minute) in CHECKPOINTS


def is_trade_day(calendar: list[int], now: datetime) -> bool:
    return int(now.strftime("%Y%m%d")) in set(calendar)


class AlertJob:
    def __init__(self, calendar_provider, watchlist_provider, data_provider, strategy, email_sender):
        self.calendar_provider = calendar_provider
        self.watchlist_provider = watchlist_provider
        self.data_provider = data_provider
        self.strategy = strategy
        self.email_sender = email_sender

    def run_once(self, now: datetime) -> int:
        if not is_trade_day(self.calendar_provider(), now) or not is_alert_check_time(now):
            return 0

        sent_count = 0
        for item in self.watchlist_provider():
            daily_df, hourly_df = self.data_provider(item.code)
            signal = self.strategy.generate_signal(item.code, daily_df, hourly_df)
            if signal is not None:
                self.email_sender.send_signal(signal)
                sent_count += 1
        return sent_count


class T0MonitorJob:
    def __init__(self, calendar_provider, monitor_service, email_sender):
        self.calendar_provider = calendar_provider
        self.monitor_service = monitor_service
        self.email_sender = email_sender

    def run_once(self, now: datetime) -> int:
        if not is_trade_day(self.calendar_provider(), now) or not is_alert_check_time(now):
            return 0

        sent_count = 0
        for code in self.monitor_service.list_enabled_t0_codes():
            open_position = self.monitor_service.get_open_t0_position(code)
            if open_position is not None:
                position_payload = json.loads(open_position.payload_json)
                current_price = self.monitor_service.get_current_price(code)
                holding_days = self.monitor_service.holding_trade_days(open_position, now)
                sell_payload = self.monitor_service.generate_sell_signal(position_payload, current_price, holding_days, now)
                if sell_payload is None:
                    continue
                self.email_sender.send_t0_sell_signal(sell_payload)
                self.monitor_service.mark_position_closed(open_position, sell_payload)
                sent_count += 1
                continue

            payload = self.monitor_service.generate_realtime_signal(code, now)
            if payload is None:
                continue
            self.email_sender.send_t0_signal(payload)
            self.monitor_service.mark_position_open(code, payload)
            sent_count += 1
        return sent_count
