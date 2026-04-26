import base64
import json
import time
from unittest.mock import MagicMock, patch

import pytest

from uploader.infrastructure.api.auth import AuthHandler, _token_is_expired
from uploader.infrastructure.api.exceptions import AuthenticationError, MaxAuthRetriesError, TokenRefreshError

_FAKE_CONFIG    = {"diagho_api": {"username": "u", "password": "p", "allow_insecure": True}}
_FAKE_ENDPOINTS = {"login": "http://fake/login/", "refresh": "http://fake/refresh/"}


def _make_jwt(exp: int) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps({"exp": exp, "token_type": "access"}).encode()
    ).decode().rstrip("=")
    return f"eyJhbGciOiJIUzI1NiJ9.{payload}.fakesig"


def _mock_post(status_code: int, json_body=None, text=""):
    m = MagicMock()
    m.status_code = status_code
    m.json.return_value = json_body or {}
    m.text = text
    return m


# ---------------------------------------------------------------------------
# _token_is_expired
# ---------------------------------------------------------------------------

def test_expired_token_detected():
    token = _make_jwt(int(time.time()) - 60)
    assert _token_is_expired(token) is True


def test_valid_token_not_expired():
    token = _make_jwt(int(time.time()) + 3600)
    assert _token_is_expired(token) is False


def test_malformed_token_treated_as_expired():
    assert _token_is_expired("not.a.jwt") is True


def test_empty_string_treated_as_expired():
    assert _token_is_expired("") is True


def test_token_with_no_exp_treated_as_expired():
    payload = base64.urlsafe_b64encode(b'{"token_type":"access"}').decode().rstrip("=")
    token = f"header.{payload}.sig"
    assert _token_is_expired(token) is True


# ---------------------------------------------------------------------------
# AuthHandler.ensure_valid_token
# ---------------------------------------------------------------------------

def test_ensure_valid_calls_refresh_or_login_when_expired():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler.access_token = _make_jwt(int(time.time()) - 60)
    with patch.object(handler, "refresh_or_login") as mock:
        handler.ensure_valid_token()
    mock.assert_called_once()


def test_ensure_valid_calls_refresh_or_login_when_no_token():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler.access_token = None
    with patch.object(handler, "refresh_or_login") as mock:
        handler.ensure_valid_token()
    mock.assert_called_once()


def test_ensure_valid_skips_refresh_when_token_current():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler.access_token = _make_jwt(int(time.time()) + 3600)
    with patch.object(handler, "refresh_or_login") as mock:
        handler.ensure_valid_token()
    mock.assert_not_called()


def test_ensure_valid_raises_during_cooldown():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler.access_token = _make_jwt(int(time.time()) - 60)  # expired
    handler._auth_retry_after = time.time() + 3600

    with pytest.raises(AuthenticationError):
        handler.ensure_valid_token()


# ---------------------------------------------------------------------------
# AuthHandler.login / refresh (mocked HTTP)
# ---------------------------------------------------------------------------

def test_login_stores_tokens():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    access  = _make_jwt(int(time.time()) + 3600)
    refresh = _make_jwt(int(time.time()) + 86400)

    with patch("uploader.infrastructure.api.auth.requests.post",
               return_value=_mock_post(200, {"access": access, "refresh": refresh})):
        handler.login()

    assert handler.access_token == access
    assert handler.refresh_token == refresh


def test_login_raises_on_failure():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)

    with patch("uploader.infrastructure.api.auth.requests.post",
               return_value=_mock_post(401, text="Unauthorized")):
        with pytest.raises(AuthenticationError):
            handler.login()


def test_refresh_updates_access_token():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler.refresh_token = _make_jwt(int(time.time()) + 86400)
    new_access = _make_jwt(int(time.time()) + 3600)

    with patch("uploader.infrastructure.api.auth.requests.post",
               return_value=_mock_post(200, {"access": new_access})):
        handler.refresh()

    assert handler.access_token == new_access


def test_refresh_raises_without_refresh_token():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler.refresh_token = None
    with pytest.raises(TokenRefreshError):
        handler.refresh()


def test_refresh_or_login_falls_back_to_login_on_refresh_failure():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler.refresh_token = _make_jwt(int(time.time()) + 86400)

    with patch.object(handler, "refresh", side_effect=TokenRefreshError("failed")), \
         patch.object(handler, "login") as mock_login:
        handler.refresh_or_login()

    mock_login.assert_called_once()


# ---------------------------------------------------------------------------
# Cooldown behaviour
# ---------------------------------------------------------------------------

def test_refresh_or_login_raises_immediately_during_cooldown():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler._auth_retry_after = time.time() + 3600

    with pytest.raises(AuthenticationError):
        handler.refresh_or_login()


# ---------------------------------------------------------------------------
# Failure counting and reset
# ---------------------------------------------------------------------------

def test_login_resets_failure_count():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler._auth_failures = 5
    handler._auth_retry_after = time.time() + 3600

    access  = _make_jwt(int(time.time()) + 3600)
    refresh = _make_jwt(int(time.time()) + 86400)

    with patch("uploader.infrastructure.api.auth.requests.post",
               return_value=_mock_post(200, {"access": access, "refresh": refresh})):
        handler.login()

    assert handler._auth_failures == 0
    assert handler._auth_retry_after == 0.0


def test_refresh_resets_failure_count():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler._auth_failures = 3
    handler._auth_retry_after = time.time() + 3600
    handler.refresh_token = _make_jwt(int(time.time()) + 86400)

    with patch("uploader.infrastructure.api.auth.requests.post",
               return_value=_mock_post(200, {"access": _make_jwt(int(time.time()) + 3600)})):
        handler.refresh()

    assert handler._auth_failures == 0
    assert handler._auth_retry_after == 0.0


def test_refresh_or_login_increments_failure_and_sets_cooldown():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)

    with patch.object(handler, "refresh", side_effect=TokenRefreshError("failed")), \
         patch.object(handler, "login", side_effect=AuthenticationError("bad creds")):
        with pytest.raises(AuthenticationError):
            handler.refresh_or_login()

    assert handler._auth_failures == 1
    assert handler._auth_retry_after > time.time()


def test_refresh_or_login_raises_max_auth_retries_on_7th_failure():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler._auth_failures = 6  # next failure is the 7th

    with patch.object(handler, "refresh", side_effect=TokenRefreshError("failed")), \
         patch.object(handler, "login", side_effect=AuthenticationError("bad creds")):
        with pytest.raises(MaxAuthRetriesError):
            handler.refresh_or_login()

    assert handler._auth_failures == 7
