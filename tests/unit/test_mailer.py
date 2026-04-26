import smtplib
from unittest.mock import MagicMock, patch

import pytest

from uploader.utils.mailer import Mailer

_BASE_CONFIG = {
    "emails": {"send_mail_flag": 1, "recipients": "admin@example.com"},
    "smtp": {"server": "mail.local", "port": 25, "use_tls": False},
}


def _mailer(**email_overrides):
    cfg = {
        **_BASE_CONFIG,
        "emails": {**_BASE_CONFIG["emails"], **email_overrides},
    }
    return Mailer(cfg)


def _smtp_mock():
    instance = MagicMock()
    cls = MagicMock()
    cls.return_value.__enter__.return_value = instance
    cls.return_value.__exit__.return_value = False
    return cls, instance


# ---------------------------------------------------------------------------
# __init__ — enabled / disabled logic
# ---------------------------------------------------------------------------

def test_enabled_with_valid_config():
    m = _mailer()
    assert m.enabled is True
    assert m.recipients == ["admin@example.com"]


def test_disabled_when_flag_is_zero():
    m = _mailer(send_mail_flag=0)
    assert m.enabled is False


def test_disabled_on_invalid_email():
    m = _mailer(recipients="not-an-email")
    assert m.enabled is False


def test_disabled_when_any_recipient_is_invalid():
    m = _mailer(recipients="good@example.com, bad-email")
    assert m.enabled is False


def test_parses_multiple_recipients():
    m = _mailer(recipients="a@x.com, b@y.com")
    assert m.recipients == ["a@x.com", "b@y.com"]


# ---------------------------------------------------------------------------
# alert / info — subject routing
# ---------------------------------------------------------------------------

def test_alert_passes_alert_subject():
    m = _mailer()
    with patch.object(m, "_send") as mock_send:
        m.alert("something broke")
    mock_send.assert_called_once_with("[ALERT] Diagho-Uploader", "something broke")


def test_info_passes_info_subject():
    m = _mailer()
    with patch.object(m, "_send") as mock_send:
        m.info("all good")
    mock_send.assert_called_once_with("[INFO] Diagho-Uploader", "all good")


# ---------------------------------------------------------------------------
# _send — SMTP interaction
# ---------------------------------------------------------------------------

def test_send_does_nothing_when_disabled():
    m = _mailer()
    m.enabled = False
    smtp_cls, smtp_instance = _smtp_mock()
    with patch("uploader.utils.mailer.smtplib.SMTP", smtp_cls):
        m._send("subject", "body")
    smtp_instance.sendmail.assert_not_called()


def test_send_calls_sendmail():
    m = _mailer()
    smtp_cls, smtp_instance = _smtp_mock()
    with patch("uploader.utils.mailer.smtplib.SMTP", smtp_cls):
        m._send("subject", "body")
    smtp_instance.sendmail.assert_called_once()


def test_send_does_not_raise_on_smtp_exception():
    m = _mailer()
    smtp_cls, smtp_instance = _smtp_mock()
    smtp_instance.sendmail.side_effect = smtplib.SMTPException("relay rejected")
    with patch("uploader.utils.mailer.smtplib.SMTP", smtp_cls):
        m._send("subject", "body")  # must not raise


def test_send_does_not_raise_on_connection_error():
    m = _mailer()
    with patch("uploader.utils.mailer.smtplib.SMTP", side_effect=OSError("connection refused")):
        m._send("subject", "body")  # must not raise


def test_send_uses_tls_when_configured():
    cfg = {
        "emails": {"send_mail_flag": 1, "recipients": "admin@example.com"},
        "smtp": {"server": "mail.local", "port": 587, "use_tls": True},
    }
    m = Mailer(cfg)
    smtp_cls, smtp_instance = _smtp_mock()
    with patch("uploader.utils.mailer.smtplib.SMTP", smtp_cls):
        m._send("subject", "body")
    smtp_instance.starttls.assert_called_once()
