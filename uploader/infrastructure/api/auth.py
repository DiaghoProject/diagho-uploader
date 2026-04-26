import base64
import json
import logging
import time

import requests

from .exceptions import AuthenticationError, MaxAuthRetriesError, TokenRefreshError

logger = logging.getLogger(__name__)

_MAX_AUTH_FAILURES = 7
_AUTH_RETRY_DELAY = 30  # seconds


def _token_is_expired(token: str) -> bool:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)  # JWT base64url strips padding; Python decoder requires it
        data = json.loads(base64.urlsafe_b64decode(payload))
        return data.get("exp", 0) < time.time()
    except Exception:
        return True


class AuthHandler:
    def __init__(self, config: dict, endpoints):
        self.config = config
        self.endpoints = endpoints
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self._auth_failures: int = 0
        self._auth_retry_after: float = 0.0

    def _reset_failures(self):
        self._auth_failures = 0
        self._auth_retry_after = 0.0

    def login(self):
        url = self.endpoints["login"]
        r = requests.post(
            url,
            json={
                "identifier": self.config["diagho_api"]["username"],
                "password": self.config["diagho_api"]["password"],
            },
            verify=not self.config["diagho_api"].get("allow_insecure", False),
        )
        if r.status_code != 200:
            raise AuthenticationError(f"Login failed: {r.text}")
        data = r.json()
        self.access_token = data["access"]
        self.refresh_token = data["refresh"]
        self._reset_failures()
        logger.info("Login successful")

    def refresh(self):
        if not self.refresh_token:
            raise TokenRefreshError("No refresh token available")
        url = self.endpoints["refresh"]
        r = requests.post(url, json={"refresh": self.refresh_token})
        if r.status_code != 200:
            raise TokenRefreshError("Refresh failed")
        data = r.json()
        self.access_token = data["access"]
        self._reset_failures()
        logger.debug("Token refreshed")

    def ensure_valid_token(self):
        if not self.access_token or _token_is_expired(self.access_token):
            if time.time() < self._auth_retry_after:
                raise AuthenticationError("Authentication in cooldown, waiting before retry")
            self.refresh_or_login()

    def refresh_or_login(self):
        if time.time() < self._auth_retry_after:
            raise AuthenticationError("Authentication in cooldown, waiting before retry")
        try:
            self.refresh()
        except TokenRefreshError:
            logger.warning("Token refresh failed, falling back to login")
            try:
                self.login()
            except AuthenticationError:
                self._auth_failures += 1
                if self._auth_failures >= _MAX_AUTH_FAILURES:
                    logger.error(
                        "Authentication failed %d times in a row. Check API availability and credentials.",
                        self._auth_failures,
                    )
                    raise MaxAuthRetriesError(self._auth_failures)
                logger.warning(
                    "Authentication failed (%d/%d), retrying in %ds",
                    self._auth_failures, _MAX_AUTH_FAILURES, _AUTH_RETRY_DELAY,
                )
                self._auth_retry_after = time.time() + _AUTH_RETRY_DELAY
                raise
