from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from src.application.auth.errors import EmailUnavailableError
from src.core.config import Config


class SmtpEmailSender:
    def __init__(self, config: Config, logger: logging.Logger | None = None) -> None:
        self.config = config
        self.logger = logger

    def send(self, to: str, code: str, expires_in_seconds: int) -> None:
        if not (self.config.smtp_host and self.config.smtp_username and self.config.smtp_password and self.config.smtp_from_address):
            raise EmailUnavailableError("SMTP 配置缺失，无法发送验证码邮件；请先在 server/.env 补齐 SMTP 配置")

        message = EmailMessage()
        message["From"] = self.config.smtp_from_address
        message["To"] = to
        message["Subject"] = "注册验证码"
        message.set_content(
            f"您的注册验证码为 {code}，{expires_in_seconds // 60} 分钟内有效。"
            "如非本人操作，请忽略本邮件。"
        )

        try:
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=10) as smtp:
                if self.config.smtp_port == 587:
                    smtp.starttls()
                smtp.login(self.config.smtp_username, self.config.smtp_password)
                smtp.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            if self.logger is not None:
                self.logger.error(f"SMTP 发送失败：{exc}")
            raise EmailUnavailableError(f"邮件发送链路不可用：{exc}") from exc

        if self.logger is not None:
            self.logger.debug(f"SMTP 发送成功：收件人 {to}")
