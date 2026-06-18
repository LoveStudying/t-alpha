from email.message import EmailMessage
import smtplib

from t_alpha.config import Settings
from t_alpha.strategy.signal import TradeSignal


def build_alert_email(signal: TradeSignal) -> tuple[str, str]:
    subject = f"[做T提醒] {signal.code} 出现候选买点 胜率{signal.win_rate:.2%} 预期收益{signal.expected_return:.2%}"
    body = "\n".join(
        [
            f"股票代码: {signal.code}",
            f"信号时间: {signal.signal_time:%Y-%m-%d %H:%M:%S}",
            f"当前价格: {signal.current_price}",
            f"建议关注买入区间: {signal.suggested_buy_zone[0]} - {signal.suggested_buy_zone[1]}",
            f"建议买入金额: {signal.suggested_amount}",
            f"建议买入股数: {signal.suggested_shares}",
            f"预计卖出点位: {signal.expected_sell_price}",
            f"止损点位: {signal.stop_loss_price}",
            f"历史样本数: {signal.sample_count}",
            f"胜率: {signal.win_rate:.2%}",
            f"扣成本后预期收益: {signal.expected_return:.2%}",
            f"最大回撤: {signal.max_drawdown:.2%}",
            f"持仓规则: {signal.holding_rule}",
            f"触发原因: {'; '.join(signal.reasons)}",
            "风险提示: 仅供研究参考，不构成投资建议。历史回测不代表未来表现。",
        ]
    )
    return subject, body


def build_t0_alert_email(payload: dict) -> tuple[str, str]:
    subject = f"[T0 buy alert] {payload['code']} low-buy signal target 3%"
    body = "\n".join(
        [
            f"code: {payload['code']}",
            f"signal time: {payload['signal_time']}",
            f"current price: {payload['current_price']}",
            f"buy zone: {payload['suggested_buy_zone'][0]} - {payload['suggested_buy_zone'][1]}",
            f"suggested amount: {payload['suggested_amount']}",
            f"suggested shares: {payload['suggested_shares']}",
            f"target sell price: {payload['target_sell_price']}",
            f"max holding trade days: {payload['max_holding_trade_days']}",
            f"3y trade count: {payload['full_trade_count']}",
            f"3y success rate: {payload['full_success_rate']:.2%}",
            f"recent 3m trade count: {payload['recent_trade_count']}",
            f"recent 3m success rate: {payload['recent_success_rate']:.2%}",
            f"reasons: {'; '.join(payload['reasons'])}",
            "risk: research only. This virtual T0 position requires sufficient sellable base shares.",
        ]
    )
    return subject, body


def build_t0_sell_alert_email(payload: dict) -> tuple[str, str]:
    subject = f"[T0 sell alert] {payload['code']} {payload['sell_alert_type']}"
    body = "\n".join(
        [
            f"code: {payload['code']}",
            f"original signal time: {payload['signal_time']}",
            f"buy alert time: {payload['buy_alert_time']}",
            f"reference buy price: {payload['reference_buy_price']}",
            f"suggested shares: {payload['suggested_shares']}",
            f"target sell price: {payload['target_sell_price']}",
            f"current price: {payload['current_price']}",
            f"trigger price: {payload['trigger_price']}",
            f"sell alert time: {payload['sell_alert_time']}",
            f"holding trade days: {payload['holding_trade_days']}",
            f"exit type: {payload['sell_alert_type']}",
            f"gross return: {payload['gross_return']:.2%}",
            f"net return estimate: {payload['net_return']:.2%}",
            f"estimated profit amount: {payload['estimated_profit_amount']}",
            f"virtual position status: {payload['position_status']}",
            "risk: if the buy alert was not actually executed, this sell alert is only a tracking signal.",
        ]
    )
    return subject, body


class EmailSender:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send_signal(self, signal: TradeSignal) -> None:
        subject, body = build_alert_email(signal)
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.settings.smtp_from
        message["To"] = self.settings.alert_to
        message.set_content(body)

        with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port) as smtp:
            smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(message)

    def send_t0_signal(self, payload: dict) -> None:
        subject, body = build_t0_alert_email(payload)
        self._send_text(subject, body)

    def send_t0_sell_signal(self, payload: dict) -> None:
        subject, body = build_t0_sell_alert_email(payload)
        self._send_text(subject, body)

    def _send_text(self, subject: str, body: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.settings.smtp_from
        message["To"] = self.settings.alert_to
        message.set_content(body)

        with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port) as smtp:
            smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(message)
