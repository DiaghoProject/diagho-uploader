import pytest
import responses
import requests
import logging
from unittest.mock import patch

from diagho_uploader.api_handler import *
from common.log_utils import log_error


# Configurer le logger pour rediriger les logs vers un fichier spécifique
@pytest.fixture(scope="function", autouse=True)
def setup_logging():
    # Créer un logger spécifique pour les tests
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Créer un gestionnaire de fichier qui écrit dans 'test_log.log'
    file_handler = logging.FileHandler('test_log.log')
    file_handler.setLevel(logging.DEBUG)
    
    # Créer un formatteur pour les logs
    formatter = logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s")
    file_handler.setFormatter(formatter)
    
    # Ajouter le gestionnaire au logger
    logger.addHandler(file_handler)

    # Réinitialiser les handlers après le test pour éviter les interférences
    yield

    # Nettoyage après le test
    logger.removeHandler(file_handler)

         


@pytest.fixture
def api_endpoints():
    """Fixture pour fournir les URLs de test."""
    return {"healthcheck": "https://mock-api.com/healthcheck"}        
         

@responses.activate
def test_api_healthcheck_success(api_endpoints):
    """Teste si la fonction retourne True quand l'API répond correctement."""
    responses.add(responses.GET, api_endpoints["healthcheck"], status=200)

    assert api_healthcheck(api_endpoints) is True

@responses.activate
def test_api_healthcheck_http_error(api_endpoints):
    """Teste si une erreur HTTP est bien levée."""
    responses.add(responses.GET, api_endpoints["healthcheck"], status=500)

    with pytest.raises(ValueError, match="HTTP Error"):
        api_healthcheck(api_endpoints)

@responses.activate
def test_api_healthcheck_request_error(api_endpoints, caplog):
    """Teste si une erreur de connexion est bien capturée et loggée."""
    # Simule une exception de requête (par exemple, un problème de connexion)
    responses.add(responses.GET, api_endpoints["healthcheck"], body=requests.exceptions.RequestException("Connection failed"))
    with pytest.raises(ValueError, match="Request Error"):
        with caplog.at_level(logging.ERROR):
            api_healthcheck(api_endpoints)
            assert "API healthcheck: KO - Request Error" in caplog.text
            
            
                   
            
# Validate credentials
def test_validate_credentials_success():
    config = {"diagho_api": {"username": "test_user", "password": "test_pass"}}
    username, password = validate_credentials(config)
    assert username == "test_user"
    assert password == "test_pass"

def test_validate_credentials_missing_username():
    config = {"diagho_api": {"password": "pass"}}
    with pytest.raises(ValueError, match="Username or password is missing"):
        validate_credentials(config)

def test_validate_credentials_missing_password():
    config = {"diagho_api": {"username": "test_user"}}
    with pytest.raises(ValueError, match="Username or password is missing"):
        validate_credentials(config)

def test_validate_credentials_missing_both():
    config = {"diagho_api": {}}
    with pytest.raises(ValueError, match="Username or password is missing"):
        validate_credentials(config)
        

# store token
def test_store_tokens_success(tmp_path):
    """ Vérifie que les tokens sont bien stockés en JSON """
    tokens = {"access_token": "abc123", "refresh_token": "xyz789"}
    file_path = tmp_path / "test_tokens.json"
    store_tokens(tokens, str(file_path))
    with open(file_path, "r") as file:
        saved_data = json.load(file)
    assert saved_data == tokens
    
def test_store_tokens_invalid_input():
    """ Vérifie qu'une erreur est retournée si 'tokens' n'est pas un dictionnaire """
    result = store_tokens(["not", "a", "dict"])
    assert result == {"error": "'tokens' must be a dictionary"}