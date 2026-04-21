class ApiError(Exception):
    """Base class for all API-related errors."""
    pass

class AuthenticationError(ApiError):
    """Raised when login/auth fails (401, invalid token, etc.)"""
    def __init__(self, message="Access denied, relogging required"):
        super().__init__(message)

class TokenRefreshError(AuthenticationError):
    pass

class ChecksumMismatchError(ApiError):
    """Raised when local checksum != remote checksum during file upload"""
    def __init__(self, filename: str, local: str, remote: str):
        self.filename = filename
        self.local = local
        self.remote = remote
        msg = f"Checksum mismatch for {filename}: local={local}, remote={remote}"
        super().__init__(msg)

class UploadError(ApiError):
    """Generic upload failure (network issues, 5xx responses, etc.)"""
    def __init__(self, filename: str, status_code: int = None, message: str = None):
        self.filename = filename
        self.status_code = status_code
        msg = message or f"Error uploading file {filename}"
        if status_code:
            msg += f" (HTTP {status_code})"
        super().__init__(msg)

class BiofileParsingError(ApiError):
    """Raised when a biofile reaches a terminal failure status after upload."""
    def __init__(self, filename: str, status: str):
        self.filename = filename
        self.status = status
        super().__init__(f"Biofile '{filename}' parsing failed with status: {status}")
