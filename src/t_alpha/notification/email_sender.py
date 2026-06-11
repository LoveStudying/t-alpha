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
