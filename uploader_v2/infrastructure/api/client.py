from pathlib import Path
import requests
from .auth import AuthHandler
from .endpoints import get_api_endpoints
from .exceptions import ApiError, AuthenticationError, UploadError, ChecksumMismatchError, BiofileParsingError

class ApiClient:
    def __init__(self, config: dict):
        self.config = config
        self.endpoints = get_api_endpoints(config)
        self.auth = AuthHandler(config, endpoints=self.endpoints)
        self.session = requests.Session()
        self.verify = not config["diagho_api"].get("allow_insecure", False)

    def _headers(self):
        self.auth.ensure_valid_token()
        return {"Authorization": f"Bearer {self.auth.access_token}"}

    def healthcheck(self):
        url = self.endpoints["healthcheck"]
        r = self.session.get(url, verify=self.verify)
        if r.status_code != 200:
            raise ApiError("Healthcheck failed")
        return r.json()
    
    def upload_biofile(self, endpoint: str, data: dict, file: Path, expected_checksum: str):
        url = self.endpoints[endpoint]

        with open(file, "rb") as fh:
            try:
                r = requests.post(url, data=data, files={"file": fh}, headers=self._headers(), verify=self.verify)
            except requests.exceptions.RequestException as e:
                raise UploadError(file.stem, message=str(e)) from e

            if r.status_code == 401:
                self.auth.refresh_or_login()
                fh.seek(0)
                try:
                    r = requests.post(url, data=data, files={"file": fh}, headers=self._headers(), verify=self.verify)
                except requests.exceptions.RequestException as e:
                    raise UploadError(file.stem, message=str(e)) from e
                if r.status_code == 401:
                    raise AuthenticationError()

            if not r.ok:
                raise UploadError(file.stem, r.status_code, r.text)

        remote_checksum = r.json()["checksum"]
        if remote_checksum != expected_checksum:
            raise ChecksumMismatchError(file.stem, expected_checksum, remote_checksum)

        return remote_checksum

    def post_metadata(self, payload: dict) -> None:
        url = self.endpoints["post_config"]
        try:
            r = self.session.post(url, json=payload, headers=self._headers(), verify=self.verify)
        except requests.exceptions.RequestException as e:
            raise ApiError(str(e)) from e
        if not r.ok:
            raise ApiError(f"Metadata POST failed (HTTP {r.status_code}): {r.text}")

    def get_biofile_loading_status(self, checksum: str) -> str:
        url = f"{self.endpoints['get_biofile']}?checksum={checksum}"
        try:
            r = self.session.get(url, headers=self._headers(), verify=self.verify)
        except requests.exceptions.RequestException as e:
            raise ApiError(str(e)) from e
        if not r.ok:
            raise ApiError(f"Failed to get biofile status (HTTP {r.status_code})")
        results = r.json().get("results", [])
        if not results:
            raise ApiError(f"No biofile found for checksum {checksum}")
        status = results[0].get("loadingStatus")
        if status is None:
            raise ApiError(f"Missing loadingStatus field for checksum {checksum}")
        return status