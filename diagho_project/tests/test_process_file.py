import hashlib
from diagho_uploader.process_file import get_biofile_informations
import pytest
import os
import time
from colorlog import ColoredFormatter

from unittest.mock import patch

from diagho_uploader.process_file import wait_for_biofile
from diagho_uploader.process_file import get_biofile_type
from diagho_uploader.process_file import check_md5sum
from diagho_uploader.process_file import md5

from common.log_utils import *

@pytest.fixture
def mock_logger():
    with patch("logging.getLogger") as mock:
        yield mock.return_value

@pytest.fixture
def mock_log_warning():
    """Mocke la fonction log_warning pour éviter d'écrire des logs réels."""
    with patch("common.log_utils.log_warning") as mock:
        yield mock
        
@pytest.fixture
def mock_log_error():
    """Mocke la fonction log_error."""
    with patch("common.log_utils.log_error") as mock:
        yield mock
        
@pytest.fixture
def mock_sleep():
    with patch("diagho_uploader.process_file.time.sleep") as mock:
        yield mock
        
@pytest.fixture
def mock_exists():
    """Mocke os.path.exists pour contrôler son retour."""
    with patch("os.path.exists") as mock:
        yield mock





# Tests fonction : wait_for_biofile
def test_wait_for_biofile_found_immediately(mock_logger, mock_sleep, mock_exists):
    """Test lorsque le fichier est immédiatement trouvé."""
    mock_exists.return_value = True  # Simule que le fichier existe dès le début

    assert wait_for_biofile("test.vcf", max_retries=5, delay=1) is True

    mock_logger.warning.assert_not_called()  # Aucun log d'avertissement ne doit être fait
    # mock_logger.info.assert_called_once_with("Biofile test.vcf found. Continue.")  # Log OK
    mock_logger.error.assert_not_called()  # Pas d'erreur
    mock_sleep.assert_not_called()  # Pas d'attente inutile
    
def test_wait_for_biofile_not_found(mock_logger, mock_sleep, mock_exists):
    """Test lorsque le fichier n'est jamais trouvé."""
    mock_exists.return_value = False  # Simule que le fichier n'existe jamais

    assert wait_for_biofile("test.vcf", max_retries=5, delay=1) is False

    assert mock_logger.warning.call_count == 5  # Vérifie que logger.warning() est appelé 5 fois
    assert mock_logger.error.call_count == 1  # Vérifie que logger.error() est appelé une fois
    assert mock_sleep.call_count == 5  # Vérifie que sleep() est appelé 5 fois

def test_wait_for_biofile_found_after_some_retries(mock_logger, mock_sleep, mock_exists):
    """Test lorsque le fichier apparaît après quelques tentatives."""
    # Simule que le fichier n'existe pas au début, mais apparaît après 3 essais
    mock_exists.side_effect = [False, False, False, True]

    assert wait_for_biofile("test.vcf", max_retries=5, delay=1) is True

    # assert mock_logger.warning.call_count == 3  # Vérifie que logger.warning() est appelé 3 fois
    # assert mock_logger.info.call_count == 1  # Un seul log de succès
    assert mock_logger.error.call_count == 0  # Pas d'erreur
    assert mock_sleep.call_count == 3  # Vérifie que sleep() est appelé 3 fois
    
    
    
# Tests fonction : get_biofile_type
@pytest.mark.parametrize("biofile, expected", [
    ("sample.vcf", "SNV"),
    ("sample.vcf.gz", "SNV"),
    ("sample.bed", "CNV"),
    ("sample.tsv", "CNV"),
])

def test_get_biofile_type_valid(biofile, expected):
    """Teste les extensions valides."""
    assert get_biofile_type(biofile) == expected
    
def test_get_biofile_type_invalid():
    """Teste une extension non supportée en vérifiant qu'une ValueError est levée."""
    biofile = "sample.txt"
    expected_message = f"Unsupported biofile type for file: {biofile}"
    with pytest.raises(ValueError, match=expected_message):
        get_biofile_type(biofile)
        


# Tests fonction : check_md5sum

# Test avec checksums identiques
def test_equal_md5():
    assert check_md5sum("d41d8cd98f00b204e9800998ecf8427e", "d41d8cd98f00b204e9800998ecf8427e") == True

# Test avec checksums différents
def test_different_md5():
    assert check_md5sum("d41d8cd98f00b204e9800998ecf8427e", "e99a18c428cb38d5f260853678922e03") == False

# Test avec un checksum non string (int)
def test_non_string_first_checksum():
    with pytest.raises(TypeError, match="MD5 should be strings."):
        check_md5sum(1234567890, "d41d8cd98f00b204e9800998ecf8427e")
def test_non_string_second_checksum():
    with pytest.raises(TypeError, match="MD5 should be strings."):
        check_md5sum("d41d8cd98f00b204e9800998ecf8427e", 1234567890)

# Test avec des chaînes vides
def test_empty_strings():
    with pytest.raises(ValueError, match="MD5 length issue. Should be 32."):
        check_md5sum("", "")
        
        


# Tests fonction : md5

# Test avec un fichier existant
def test_md5_valid_file():
    # Crée un fichier temporaire pour tester
    test_file = "testfile.txt"
    with open(test_file, 'w') as f:
        f.write("Hello, World!")

    expected_md5 = hashlib.md5(b"Hello, World!").hexdigest()
    assert md5(test_file) == expected_md5

    # Nettoyer après le test
    os.remove(test_file)
    
# Test avec un fichier inexistant
def test_md5_file_not_found():
    non_existing_file = "non_existing_file.txt"
    result = md5(non_existing_file)
    assert result == {"error": "File not found: non_existing_file.txt"}

# Test avec un fichier vide
def test_md5_empty_file():
    test_file = "empty_file.txt"
    with open(test_file, 'w') as f:
        pass  # Crée un fichier vide

    expected_md5 = hashlib.md5().hexdigest()  # MD5 d'un fichier vide est une chaîne de 32 caractères '0'
    assert md5(test_file) == expected_md5

    os.remove(test_file)
    
# Test avec un fichier auquel on n'a pas accès (par exemple, permission refusée)
def test_md5_io_error():
    # Crée un fichier temporaire
    test_file = "testfile2.txt"
    with open(test_file, 'w') as f:
        f.write("Hello, World!")

    # Change les permissions pour ne pas pouvoir lire le fichier
    os.chmod(test_file, 0o0200)

    result = md5(test_file)
    assert "IO error while reading" in result['error']

    # Rétablir les permissions et nettoyer après le test
    os.chmod(test_file, 0o644)
    os.remove(test_file)
    
# Test avec une exception inattendue
def test_md5_unexpected_error(monkeypatch):
    # Simule une exception inattendue, par exemple un problème lors de l'appel à open()
    def mock_open(filepath, mode):
        raise Exception("Unexpected error during file opening")

    monkeypatch.setattr("builtins.open", mock_open)

    test_file = "testfile3.txt"
    result = md5(test_file)
    assert "Unexpected error" in result['error']
    
    
    

# Tests fonction : get_biofile_informations
sample_data = [
    {"filename": "file1.vcf", "checksum": "123"},
    {"filename": "file2.vcf", "checksum": "456"},
    {"filename": "file3.vcf", "checksum": "789"},
]

# Test avec un fichier existant
def test_existing_file():
    result = get_biofile_informations(sample_data, "file2.vcf")
    assert result == {"filename": "file2.vcf", "checksum": "456"}