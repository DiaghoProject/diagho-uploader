import base64
import json
import logging
import time

import requests

from .exceptions import AuthenticationError, TokenRefreshError

logger = logging.getLogger(__name__)


def _token_is_expired(token: str) -> bool:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        return data.get("exp", 0) < time.time()
    except Exception:
        return True


# TODO: Could be largely simplified with an API key authentication
class AuthHandler:
    def __init__(self, config: dict, endpoints):
        self.config = config
        self.endpoints = endpoints
        self.access_token: str | None = None
        self.refresh_token: str | None = None

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
        logger.debug("Token refreshed")

    def ensure_valid_token(self):
        if not self.access_token or _token_is_expired(self.access_token):
            self.refresh_or_login()

    def refresh_or_login(self):
        try:
            self.refresh()
        except TokenRefreshError:
            logger.warning("Token refresh failed, falling back to login")
            self.login()
