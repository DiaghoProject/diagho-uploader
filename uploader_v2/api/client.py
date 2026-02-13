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

    def upload_file(self, path, expected_checksum):
        filename = path.name
        file_type = "SNV" if (filename.endswith(".vcf") or filename.endswith(".vcf.gz")) else "CNV"
        url = self.endpoints[f"post_biofile_{file_type.lower()}"]

        try:
            with path.open("rb") as f:
                r = self.session.post(url, headers=self._headers(), files={"file": f}, verify=self.verify)
            r.raise_for_status()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.auth.refresh_or_login()
                r = self.session.post(url, headers=self._headers(), files={"file": open(path, "rb")}, verify=self.verify)
                if r.status_code == 401:
                    raise AuthenticationError() from e
            else:
                raise UploadError(filename, e.response.status_code, str(e)) from e
        except requests.exceptions.RequestException as e:
            raise UploadError(filename, message=str(e)) from e

        remote_checksum = r.json()["checksum"]
        if remote_checksum != expected_checksum:
            raise ChecksumMismatchError(filename, expected_checksum, remote_checksum)

        return remote_checksum