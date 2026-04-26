class ApiError(Exception):
    pass

class AuthenticationError(ApiError):
    def __init__(self, message="Access denied, relogging required"):
        super().__init__(message)

class TokenRefreshError(AuthenticationError):
    pass

class MaxAuthRetriesError(AuthenticationError):
    def __init__(self, attempts: int):
        super().__init__(f"Authentication failed {attempts} times in a row. Check API availability and credentials.")

class ChecksumMismatchError(ApiError):
    def __init__(self, filename: str, local: str, remote: str):
        self.filename = filename
        self.local = local
        self.remote = remote
        super().__init__(f"Checksum mismatch for {filename}: local={local}, remote={remote}")

class UploadError(ApiError):
    def __init__(self, filename: str, status_code: int = None, message: str = None):
        self.filename = filename
        self.status_code = status_code
        msg = message or f"Error uploading file {filename}"
        if status_code:
            msg += f" (HTTP {status_code})"
        super().__init__(msg)
