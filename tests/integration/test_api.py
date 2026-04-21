"""
Integration tests — require a live Diagho API.

Run with: pytest -m integration
Skipped automatically when config/config.yaml is absent.
"""
import pytest
import yaml
from pathlib import Path

from uploader.infrastructure.api.client import ApiClient
from uploader.infrastructure.api.exceptions import ApiError

_CONFIG_PATH = Path("config/config.yaml")


@pytest.fixture(scope="module")
def config():
    if not _CONFIG_PATH.exists():
        pytest.skip("config/config.yaml not found")
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def client(config):
    return ApiClient(config)


@pytest.mark.integration
def test_healthcheck(client):
    result = client.healthcheck()
    assert result is not None


@pytest.mark.integration
def test_login(client):
    client.auth.login()
    assert client.auth.access_token is not None
    assert client.auth.refresh_token is not None


@pytest.mark.integration
def test_token_refresh(client):
    client.auth.login()
    old_token = client.auth.access_token
    client.auth.refresh()
    assert client.auth.access_token is not None
    assert client.auth.access_token != old_token


@pytest.mark.integration
def test_ensure_valid_token_does_not_raise(client):
    client.auth.access_token = None
    client.auth.ensure_valid_token()
    assert client.auth.access_token is not None
