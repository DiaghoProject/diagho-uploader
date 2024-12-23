import os
import json
import pytest
import hashlib
import inspect
import requests
from unittest import mock

from process_file import *

# Tests : functions.py

# 1 : check_json_format(file_path)
def test_check_json_format_well_formatted():
    """Test avec un fichier JSON bien formaté."""
    mock_open = mock.mock_open(read_data='{"key": "value"}')
    with mock.patch('builtins.open', mock_open):
        result = check_json_format("well_formatted.json")
        assert result == True

def test_check_json_format_malformatted():
    """Test avec un fichier JSON mal formaté."""
    mock_open = mock.mock_open(read_data='{"key": "value"')
    with mock.patch('builtins.open', mock_open):
        result = check_json_format("malformatted.json")
        assert result == False

def test_check_json_format_file_not_found():
    """Test avec un fichier qui n'existe pas."""
    with mock.patch('builtins.open', side_effect=FileNotFoundError):
        result = check_json_format("non_existent.json")
        assert result == False

def test_check_json_format_unexpected_error():
    """Test avec une erreur inattendue."""
    with mock.patch('builtins.open', side_effect=OSError):
        result = check_json_format("unexpected_error.json")
        assert result == False
        
# 2 : check_md5sum(checksum1, checksum2)
def test_check_md5sum_identical():
    """Test avec deux sommes de contrôle MD5 identiques."""
    assert check_md5sum("d41d8cd98f00b204e9800998ecf8427e", "d41d8cd98f00b204e9800998ecf8427e") == True

def test_check_md5sum_different():
    """Test avec deux sommes de contrôle MD5 différentes."""
    assert check_md5sum("d41d8cd98f00b204e9800998ecf8427e", "e99a18c428cb38d5f260853678922e03") == False

def test_check_md5sum_invalid_length():
    """Test avec des sommes de contrôle MD5 de longueur incorrecte."""
    with pytest.raises(ValueError):
        check_md5sum("d41d8cd98f00b204e9800998ecf8427", "e99a18c428cb38d5f260853678922e03")

    with pytest.raises(ValueError):
        check_md5sum("d41d8cd98f00b204e9800998ecf8427e", "e99a18c428cb38d5f260853678922e0")

def test_check_md5sum_invalid_type():
    """Test avec des entrées non valides."""
    with pytest.raises(TypeError):
        check_md5sum(123, "d41d8cd98f00b204e9800998ecf8427e")

    with pytest.raises(TypeError):
        check_md5sum("d41d8cd98f00b204e9800998ecf8427e", None)
        
# 3
def test_md5_file_exists():
    """Test avec un fichier existant et lisible."""
    mock_open = mock.mock_open(read_data=b'Test data for MD5 hash')
    expected_hash = hashlib.md5(b'Test data for MD5 hash').hexdigest()

    with mock.patch('builtins.open', mock_open):
        result = md5('testfile.txt')
        assert result == expected_hash

def test_md5_file_not_found():
    """Test avec un fichier non trouvé."""
    with mock.patch('builtins.open', side_effect=FileNotFoundError):
        result = md5('non_existent_file.txt')
        assert result is None

def test_md5_io_error():
    """Test avec une erreur d'entrée/sortie."""
    with mock.patch('builtins.open', side_effect=IOError):
        result = md5('unreadable_file.txt')
        assert result is None
        
# 4 : md5(filepath)



# def test_diagho_api_test_success(mocker):
#     """Test pour une requête réussie avec un code 200."""
#     mocker.patch('requests.get', return_value=mock.Mock(status_code=200))
#     mocker.patch('builtins.print')
#     # mocker.patch('__main__.load_config', return_value={'diagho_api': {'healthcheck': 'http://lx026:8080/api/v1/healthcheck'}})

#     result = diagho_api_test('config/config.yaml')
#     assert result == True

# def test_diagho_api_test_http_error(mocker):
#     """Test pour une erreur HTTP (ex. 404)."""
#     mock_response = mock.Mock()
#     mock_response.status_code = 404
#     mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
#     mocker.patch('requests.get', return_value=mock_response)
    
#     mock_print = mocker.patch('builtins.print')
#     result = diagho_api_test('config/config.yaml')
#     assert mock_print.call_count == 3
#     assert any(">>> ERROR: HTTP error occurred." in call[0][0] for call in mock_print.call_args_list)
#     assert result == False

# def test_diagho_api_test_request_exception(mocker):
#     """Test pour une autre exception de requête."""
#     mocker.patch('requests.get', side_effect=requests.exceptions.RequestException("Connection error"))
    
#     mock_print = mocker.patch('builtins.print')
#     result = diagho_api_test('config/config.yaml')
#     mock_print.assert_called_with(">>> ERROR: Request exception occurred.")
#     assert result == False

# def test_diagho_api_test_exit_on_error(mocker):
#     """Test pour la sortie du programme en cas d'erreur avec exit_on_error=True."""
#     mocker.patch('requests.get', side_effect=requests.exceptions.RequestException("Connection error"))
    
#     with pytest.raises(SystemExit):
#         diagho_api_test('http://example.com', exit_on_error=True)