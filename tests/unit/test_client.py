import smtplib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests as req_lib

from uploader.infrastructure.api.client import ApiClient
from uploader.infrastructure.api.exceptions import (
    ApiError,
    AuthenticationError,
    ChecksumMismatchError,
    UploadError,
)

_CONFIG = {
    "diagho_api": {
        "username": "u",
        "password": "p",
        "url": "http://fake/api/v1/",
        "allow_insecure": True,
    }
}


def _make_client():
    client = ApiClient(_CONFIG)
    client.auth.access_token = "fake-token"
    client.auth.ensure_valid_token = MagicMock()
    return client


def _resp(status_code, json_body=None, text=""):
    m = MagicMock()
    m.status_code = status_code
    m.json.return_value = json_body if json_body is not None else {}
    m.text = text
    m.ok = 200 <= status_code < 300
    return m


# ---------------------------------------------------------------------------
# healthcheck
# ---------------------------------------------------------------------------

def test_healthcheck_success():
    client = _make_client()
    client.session.get = MagicMock(return_value=_resp(200, {"status": "ok"}))
    assert client.healthcheck() == {"status": "ok"}


def test_healthcheck_failure_raises():
    client = _make_client()
    client.session.get = MagicMock(return_value=_resp(503))
    with pytest.raises(ApiError):
        client.healthcheck()


# ---------------------------------------------------------------------------
# upload_biofile
# ---------------------------------------------------------------------------

def test_upload_biofile_success(tmp_path):
    client = _make_client()
    f = tmp_path / "snv.vcf.gz"
    f.write_bytes(b"data")
    checksum = "abc123"

    with patch("uploader.infrastructure.api.client.requests.post",
               return_value=_resp(200, {"checksum": checksum})):
        result = client.upload_biofile("post_biofile_snv", {}, f, checksum)

    assert result == checksum


def test_upload_biofile_checksum_mismatch_raises(tmp_path):
    client = _make_client()
    f = tmp_path / "snv.vcf.gz"
    f.write_bytes(b"data")

    with patch("uploader.infrastructure.api.client.requests.post",
               return_value=_resp(200, {"checksum": "wrong"})):
        with pytest.raises(ChecksumMismatchError):
            client.upload_biofile("post_biofile_snv", {}, f, "expected")


def test_upload_biofile_401_retries_and_succeeds(tmp_path):
    client = _make_client()
    f = tmp_path / "snv.vcf.gz"
    f.write_bytes(b"data")
    checksum = "abc123"

    with patch("uploader.infrastructure.api.client.requests.post",
               side_effect=[_resp(401), _resp(200, {"checksum": checksum})]), \
         patch.object(client.auth, "refresh_or_login"):
        result = client.upload_biofile("post_biofile_snv", {}, f, checksum)

    assert result == checksum


def test_upload_biofile_double_401_raises_auth_error(tmp_path):
    client = _make_client()
    f = tmp_path / "snv.vcf.gz"
    f.write_bytes(b"data")

    with patch("uploader.infrastructure.api.client.requests.post", return_value=_resp(401)), \
         patch.object(client.auth, "refresh_or_login"):
        with pytest.raises(AuthenticationError):
            client.upload_biofile("post_biofile_snv", {}, f, "checksum")


def test_upload_biofile_400_already_uploaded_is_idempotent(tmp_path):
    client = _make_client()
    f = tmp_path / "snv.vcf.gz"
    f.write_bytes(b"data")
    checksum = "abc123"

    with patch("uploader.infrastructure.api.client.requests.post",
               return_value=_resp(400, ["File has already been uploaded"])):
        result = client.upload_biofile("post_biofile_snv", {}, f, checksum)

    assert result == checksum


def test_upload_biofile_400_other_raises_upload_error(tmp_path):
    client = _make_client()
    f = tmp_path / "snv.vcf.gz"
    f.write_bytes(b"data")

    with patch("uploader.infrastructure.api.client.requests.post",
               return_value=_resp(400, {"detail": "bad field"})):
        with pytest.raises(UploadError):
            client.upload_biofile("post_biofile_snv", {}, f, "checksum")


def test_upload_biofile_server_error_raises_upload_error(tmp_path):
    client = _make_client()
    f = tmp_path / "snv.vcf.gz"
    f.write_bytes(b"data")

    with patch("uploader.infrastructure.api.client.requests.post",
               return_value=_resp(500, text="internal error")):
        with pytest.raises(UploadError):
            client.upload_biofile("post_biofile_snv", {}, f, "checksum")


def test_upload_biofile_network_error_raises_upload_error(tmp_path):
    client = _make_client()
    f = tmp_path / "snv.vcf.gz"
    f.write_bytes(b"data")

    with patch("uploader.infrastructure.api.client.requests.post",
               side_effect=req_lib.exceptions.ConnectionError("unreachable")):
        with pytest.raises(UploadError):
            client.upload_biofile("post_biofile_snv", {}, f, "checksum")


# ---------------------------------------------------------------------------
# post_metadata
# ---------------------------------------------------------------------------

def test_post_metadata_success():
    client = _make_client()
    client.session.post = MagicMock(return_value=_resp(200))
    client.post_metadata({"key": "val"})  # must not raise


def test_post_metadata_non_ok_raises():
    client = _make_client()
    client.session.post = MagicMock(return_value=_resp(500, text="err"))
    with pytest.raises(ApiError):
        client.post_metadata({})


def test_post_metadata_network_error_raises():
    client = _make_client()
    client.session.post = MagicMock(side_effect=req_lib.exceptions.ConnectionError("down"))
    with pytest.raises(ApiError):
        client.post_metadata({})


# ---------------------------------------------------------------------------
# get_biofile_loading_status
# ---------------------------------------------------------------------------

def test_get_biofile_loading_status_returns_status():
    client = _make_client()
    client.session.get = MagicMock(
        return_value=_resp(200, {"results": [{"loadingStatus": "success"}]})
    )
    assert client.get_biofile_loading_status("abc") == "success"


def test_get_biofile_loading_status_empty_results_raises():
    client = _make_client()
    client.session.get = MagicMock(return_value=_resp(200, {"results": []}))
    with pytest.raises(ApiError, match="No biofile found"):
        client.get_biofile_loading_status("abc")


def test_get_biofile_loading_status_missing_field_raises():
    client = _make_client()
    client.session.get = MagicMock(return_value=_resp(200, {"results": [{}]}))
    with pytest.raises(ApiError, match="loadingStatus"):
        client.get_biofile_loading_status("abc")


def test_get_biofile_loading_status_non_ok_raises():
    client = _make_client()
    client.session.get = MagicMock(return_value=_resp(404))
    with pytest.raises(ApiError):
        client.get_biofile_loading_status("abc")


def test_get_biofile_loading_status_network_error_raises():
    client = _make_client()
    client.session.get = MagicMock(side_effect=req_lib.exceptions.ConnectionError("down"))
    with pytest.raises(ApiError):
        client.get_biofile_loading_status("abc")
