from pathlib import Path
import requests
from .auth import AuthHandler
from .endpoints import get_api_endpoints
from .exceptions import ApiError, AuthenticationError, UploadError, ChecksumMismatchError

class ApiClient:
    def __init__(self, config: dict):
        self.config = config
        self.endpoints = get_api_endpoints(config)
        self.auth = AuthHandler(config, endpoints=self.endpoints)
        self.session = requests.Session()
        self.verify = not config.get("allow_insecure", False)

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
        files = {"file": open(file, "rb")}
        
        try:
            r = requests.post(url, data=data, files=files, headers=self._headers())

        except requests.exceptions.HTTPError as e:
            # TODO: fix refresh token not working as expected
            if e.response.status_code == 401:
                self.auth.refresh_or_login()
                r = requests.post(url, data=data, files=files, headers=self._headers())
                if r.status_code == 401:
                    raise AuthenticationError() from e
            else:
                raise UploadError(file.stem, e.response.status_code, str(e)) from e
                
        except requests.exceptions.RequestException as e:
            raise UploadError(file.stem, message=str(e)) from e

        remote_checksum = r.json()["checksum"]
        if remote_checksum != expected_checksum:
            raise ChecksumMismatchError(file.stem, expected_checksum, remote_checksum)

        return remote_checksum