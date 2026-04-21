import base64
import json
import time

import pytest

from uploader.infrastructure.api.auth import AuthHandler, _token_is_expired
from uploader.infrastructure.api.exceptions import AuthenticationError, TokenRefreshError

_FAKE_CONFIG    = {"diagho_api": {"username": "u", "password": "p", "allow_insecure": True}}
_FAKE_ENDPOINTS = {"login": "http://fake/login/", "refresh": "http://fake/refresh/"}


def _make_jwt(exp: int) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps({"exp": exp, "token_type": "access"}).encode()
    ).decode().rstrip("=")
    return f"eyJhbGciOiJIUzI1NiJ9.{payload}.fakesig"


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

def test_ensure_valid_calls_refresh_or_login_when_expired(mocker):
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler.access_token = _make_jwt(int(time.time()) - 60)
    mock = mocker.patch.object(handler, "refresh_or_login")
    handler.ensure_valid_token()
    mock.assert_called_once()


def test_ensure_valid_calls_refresh_or_login_when_no_token(mocker):
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler.access_token = None
    mock = mocker.patch.object(handler, "refresh_or_login")
    handler.ensure_valid_token()
    mock.assert_called_once()


def test_ensure_valid_skips_refresh_when_token_current(mocker):
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler.access_token = _make_jwt(int(time.time()) + 3600)
    mock = mocker.patch.object(handler, "refresh_or_login")
    handler.ensure_valid_token()
    mock.assert_not_called()


# ---------------------------------------------------------------------------
# AuthHandler.login / refresh (mocked HTTP)
# ---------------------------------------------------------------------------

def test_login_stores_tokens(mocker):
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    access  = _make_jwt(int(time.time()) + 3600)
    refresh = _make_jwt(int(time.time()) + 86400)

    mock_post = mocker.patch("uploader.infrastructure.api.auth.requests.post")
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"access": access, "refresh": refresh}

    handler.login()

    assert handler.access_token == access
    assert handler.refresh_token == refresh


def test_login_raises_on_failure(mocker):
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)

    mock_post = mocker.patch("uploader.infrastructure.api.auth.requests.post")
    mock_post.return_value.status_code = 401
    mock_post.return_value.text = "Unauthorized"

    with pytest.raises(AuthenticationError):
        handler.login()


def test_refresh_updates_access_token(mocker):
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler.refresh_token = _make_jwt(int(time.time()) + 86400)
    new_access = _make_jwt(int(time.time()) + 3600)

    mock_post = mocker.patch("uploader.infrastructure.api.auth.requests.post")
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"access": new_access}

    handler.refresh()

    assert handler.access_token == new_access


def test_refresh_raises_without_refresh_token():
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler.refresh_token = None
    with pytest.raises(TokenRefreshError):
        handler.refresh()


def test_refresh_or_login_falls_back_to_login_on_refresh_failure(mocker):
    handler = AuthHandler(_FAKE_CONFIG, _FAKE_ENDPOINTS)
    handler.refresh_token = _make_jwt(int(time.time()) + 86400)

    mocker.patch.object(handler, "refresh", side_effect=TokenRefreshError("failed"))
    mock_login = mocker.patch.object(handler, "login")

    handler.refresh_or_login()

    mock_login.assert_called_once()
