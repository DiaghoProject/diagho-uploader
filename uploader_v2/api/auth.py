import json
from pathlib import Path
import requests
from .exceptions import AuthenticationError, TokenRefreshError
from pydantic import BaseModel

class TokenData(BaseModel):
    access: str
    refresh: str

# TODO: Could be largely simplified with an API key authentication, with limited access to endpoints
class AuthHandler:
    def __init__(self, config: dict, endpoints, token_file="tokens.json"):
        self.config = config
        self.token_file = Path(token_file)
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self._load_token()

    def _load_token(self):
        if self.token_file.exists():
            data = json.loads(self.token_file.read_text())
            tokens = TokenData.model_validate(data)
            self.access_token = tokens.access
            self.refresh_token = tokens.refresh

    def _save_tokens(self):
        tokens = TokenData(
            access=self.access_token,
            refresh=self.refresh_token,
        )
        self.token_file.write_text(tokens.model_dump_json())

    def login(self):
        url = self.endpoints.login
        r = requests.post(
            url,
            json={
                "username": self.config["diagho_api"]["username"],
                "password": self.config["diagho_api"]["password"],
            },
            verify=not self.config.get("allow_insecure", False),
        )
        if r.status_code != 200:
            raise AuthenticationError(f"Login failed: {r.text}")

        data = r.json()
        self.access_token = data["access"]
        self.refresh_token = data["refresh"]
        self._save_tokens()

    def refresh(self):
        if not self.refresh_token:
            raise TokenRefreshError("No refresh token available")

        url = self.endpoints.refresh
        r = self.session.post(
            url,
            json={"refresh": self.refresh_token},
        )

        if r.status_code != 200:
            raise TokenRefreshError("Refresh failed")

        data = r.json()
        self.access_token = data["access"]
        self._save_tokens()

    def ensure_valid_token(self):
        if not self.access_token:
            self.login()

    def refresh_or_login(self):
        try:
            self.refresh()
        except TokenRefreshError:
            self.login()