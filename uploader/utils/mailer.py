import logging
import re
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class Mailer:
    def __init__(self, config: dict):
        smtp_cfg  = config.get("smtp", {})
        email_cfg = config.get("emails", {})

        self.enabled    = bool(email_cfg.get("send_mail_flag", 0))
        self.recipients = [
            r.strip()
            for r in email_cfg.get("recipients", "").split(",")
            if r.strip()
        ]
        self.server   = smtp_cfg.get("server", "localhost")
        self.port     = int(smtp_cfg.get("port", 25))
        self.use_tls  = bool(smtp_cfg.get("use_tls", False))
        self.username = smtp_cfg.get("username")
        self.password = smtp_cfg.get("password")
        self.from_addr = smtp_cfg.get(
            "from_email_format", "diagho-uploader@localhost"
        ).format(hostname=socket.gethostname())

        if self.enabled:
            invalid = [r for r in self.recipients if not _EMAIL_RE.match(r)]
            if invalid:
                logger.warning(
                    "Invalid recipient address(es), mail disabled: %s", invalid
                )
                self.enabled = False

    def alert(self, content: str) -> None:
        self._send("[ALERT] Diagho-Uploader", content)

    def info(self, content: str) -> None:
        self._send("[INFO] Diagho-Uploader", content)

    def _send(self, subject: str, content: str) -> None:
        if not self.enabled:
            return
        if not self.recipients:
            logger.warning("No recipients configured, skipping mail")
            return

        msg = MIMEMultipart()
        msg["From"]    = self.from_addr
        msg["To"]      = ", ".join(self.recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(content, "plain"))

        try:
            with smtplib.SMTP(self.server, self.port) as smtp:
                smtp.ehlo()
                if self.use_tls:
                    smtp.starttls()
                    smtp.ehlo()
                if self.username and self.password:
                    smtp.login(self.username, self.password)
                smtp.sendmail(self.from_addr, self.recipients, msg.as_string())
            logger.info("Email sent to %s: %s", self.recipients, subject)
        except smtplib.SMTPException as e:
            logger.error("Failed to send email: %s", e)
        except OSError as e:
            logger.error("SMTP connection error (%s:%s): %s", self.server, self.port, e)
