import json
from pathlib import Path
import requests
from .exceptions import AuthenticationError

class AuthHandler:
    def __init__(self, config: dict, token_file="tokens.json"):
        self.config = config
        self.token_file = Path(token_file)
        self.token = None
        self.load_token()

    def load_token(self):
        if self.token_file.exists():
            data = json.loads(self.token_file.read_text())
            self.token = data.get("access_token")

    def login(self):
        url = self.config["diagho_api"]["url"].rstrip("/") + "/auth/login/"
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
        self.token = data["access_token"]
        self.token_file.write_text(json.dumps(data))

    def ensure_valid_token(self):
        if self.token is None:
            self.login()