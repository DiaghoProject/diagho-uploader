import hashlib
import json
import re
from unittest import mock
from unittest.mock import patch
import os
import time
import logging
import pytest


from diagho_uploader.file_utils import check_loading_status, get_biofile_informations, validate_json_input, wait_for_biofile
from diagho_uploader.file_utils import get_biofile_type
from diagho_uploader.file_utils import check_md5sum
from diagho_uploader.file_utils import md5

from common.log_utils import *

@pytest.fixture
def mock_exists():
    """Mocke os.path.exists pour contrôler son retour."""
    with patch("os.path.exists") as mock:
        yield mock





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



# Fixture pour mocker le logger
@pytest.fixture(scope="function")
def mock_logger():
    with mock.patch.object(logging, 'getLogger') as mock_get_logger:
        mock_logger = mock.Mock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger  # On "yield" pour rendre le mock disponible pour les tests
        # Aucune nécessité de nettoyage ici, car pytest le gère 
    

def test_wait_for_biofile_found(mock_logger):
    biofile = "path_to_biofile"
    # Simuler l'existence du fichier
    with mock.patch('os.path.exists', return_value=True):
        result = wait_for_biofile(biofile)
        assert result is True  # Vérifier que la fonction retourne True
        # Vérifier qu'un message de log de niveau INFO a été créé
        mock_logger.info.assert_called_with('path_to_biofile - Biofile found. Continue.')
        # mock_logger.info.assert_called_with('path_to_biofile - Biofile found. Continue.')

def test_wait_for_biofile_not_found(mock_logger):
    biofile = "path_to_biofile"
    # Simuler l'absence du fichier
    with mock.patch('os.path.exists', return_value=False):
        result = wait_for_biofile(biofile, max_retries=5, delay=0) # délai à 0 pour ne pas attendre
        assert result is False  # Vérifier que la fonction retourne False
        mock_logger.error.assert_called_with('path_to_biofile - Biofile not found after 5 attempt. Exit.')

def test_wait_for_biofile_found_after_some_retries(mock_logger):
    biofile = "path_to_biofile"
    # Simuler que le fichier n'existe pas pendant quelques tentatives puis qu'il existe
    with mock.patch('os.path.exists', side_effect=[False, False, True]):
        with mock.patch('time.sleep') as mock_sleep:
            result = wait_for_biofile(biofile, max_retries=5, delay=1)
            assert result is True  # Vérifier que la fonction retourne True après quelques tentatives
            assert mock_sleep.call_count == 1 # Vérifie que sleep a été appelé 1 fois
            mock_sleep.assert_called_with(1)  # Vérifier que sleep a été appelé avec un délai de 1 seconde
            mock_logger.warning.assert_called_with('path_to_biofile - Biofile not found... attempt 1')
    
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
    
    
    

# Test pour un fichier JSON valide
def test_validate_json_input_valid():
    # Créer un fichier temporaire JSON valide
    test_data = {
        "families": [],
        "files": [
            {
                "filename": "file1.bam",
                "checksum": "abc123",
                "assembly": "GRCh37",
                "samples": [{"person": "person1"}]
            }
        ],
        "interpretations": []
    }
    test_file = 'test_valid_config.json'
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)
    
    # Appeler la fonction pour valider le fichier JSON
    result = validate_json_input(test_file)
    
    # Vérifier si le résultat est correct
    assert result == test_data, f"Expected {test_data}, but got {result}"
    
    # Supprimer le fichier temporaire après le test
    os.remove(test_file)


# Test pour un fichier JSON sans la clé 'families'
def test_validate_json_input_missing_families(mock_logger):
    test_data = {
        "files": [
            {
                "filename": "file1.bam",
                "checksum": "abc123",
                "assembly": "GRCh37",
                "samples": [{"person": "person1"}]
            }
        ],
        "interpretations": []
    }
    test_file = 'test_missing_families.json'
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)

    with pytest.raises(ValueError, match="Le fichier JSON doit contenir une clé 'families'."):
        validate_json_input(test_file)
    # Vérifier que le message de log a été appelé pour la clé manquante
    mock_logger.error.assert_called_with(f"{os.path.basename(test_file)}- Le fichier JSON doit contenir une clé 'families'.")
    os.remove(test_file)
    
# Test pour un fichier JSON sans la clé 'files'
def test_validate_json_input_missing_files(mock_logger):
    test_data = {
        "families": [],
        "interpretations": []
    }
    test_file = 'test_missing_files.json'
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)
    
    with pytest.raises(ValueError, match="Le fichier JSON doit contenir une clé 'files'."):
        validate_json_input(test_file)
        
    # Vérifier que le message de log a été appelé pour la clé manquante
    mock_logger.error.assert_called_with(f"{os.path.basename(test_file)}- Le fichier JSON doit contenir une clé 'files'.")    
    os.remove(test_file)
    
# Test pour un fichier JSON sans la clé 'interpretation'
def test_validate_json_input_missing_interpretations(mock_logger):
    test_data = {
        "families": [],
        "files": []
    }
    test_file = 'test_missing_interpretations.json'
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)
    
    with pytest.raises(ValueError, match="Le fichier JSON doit contenir une clé 'interpretations'."):
        validate_json_input(test_file)
        
    # Vérifier que le message de log a été appelé pour la clé manquante
    mock_logger.error.assert_called_with(f"{os.path.basename(test_file)}- Le fichier JSON doit contenir une clé 'interpretations'.")    
    os.remove(test_file)
    
# Test pour un fichier JSON avec des fichiers manquants de certaines clés requises
def test_validate_json_input_missing_keys_in_file():
    test_data = {
        "families": [],
        "files": [
            {
                "filename": "file1.bam",
                "checksum": "abc123",
                "assembly": "GRCh37"
            }
        ],
        "interpretations": []
    }
    test_file = 'test_missing_keys_in_file.json'
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)
    with pytest.raises(ValueError, match=re.escape("Clés manquantes: ['samples']")):
        validate_json_input(test_file)
    os.remove(test_file)
    
# Test pour un fichier JSON avec des échantillons invalides (liste vide)
def test_validate_json_input_invalid_samples():
    test_data = {
        "families": [],
        "files": [
            {
                "filename": "file1.bam",
                "checksum": "abc123",
                "assembly": "GRCh37",
                "samples": []  # Liste vide, invalid
            }
        ],
        "interpretations": []
    }
    test_file = 'test_invalid_samples.json'
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)
    with pytest.raises(ValueError, match="'samples' doit être une liste non vide"):
        validate_json_input(test_file)
    os.remove(test_file)
    

def test_validate_json_input_invalid_samples_without_person():
    test_data = {
        "families": [],
        "files": [
            {
                "filename": "file1.bam",
                "checksum": "abc123",
                "assembly": "GRCh37",
                "samples": [{
                    "name": "sample01"
                    }]
            }
        ],
        "interpretations": []
    }
    test_file = 'test_invalid_samples.json'
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)
    with pytest.raises(ValueError, match="Clé 'person' manquante dans un sample du fichier 'file1.bam'."):
        validate_json_input(test_file)
    os.remove(test_file)
    

# Test pour un fichier JSON invalide (non JSON ou inexistant)
def test_validate_json_input_invalid_json():
    test_file = 'test_invalid_json.json'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("This is not a valid JSON!")
    with pytest.raises(ValueError, match="Erreur lors de la lecture du fichier JSON"):
        validate_json_input(test_file)
    os.remove(test_file)
    
    
# @pytest.fixture
# def mock_settings():
#     """Fixture pour les paramètres de configuration."""
#     return {
#         "check_loading_max_retries": 3,
#         "check_loading_delay": 1  # On mockera `time.sleep`, donc cette valeur n'affectera pas le test
#     }
    
# @pytest.fixture
# def mock_kwargs(mock_settings):
#     """Fixture pour les arguments passés à la fonction."""
#     return {
#         "settings": mock_settings,
#         "biofile_filename": "test_file"
#     }
    
# @pytest.mark.parametrize("return_values, expected_result", [
#     ([{"loading": 3}], True),          # Succès immédiat
#     ([{"loading": 0}], False),         # Échec immédiat
#     ([{"loading": 1}, {"loading": 1}, {"loading": 3}], True),  # Succès après plusieurs tentatives
#     ([{"loading": 1}, {"loading": 1}, {"loading": 0}], False), # Échec après plusieurs tentatives
#     ([{"loading": 1}, {"loading": 1}, {"loading": 1}, {"loading": 1}], None), # Dépassement max retries
#     ([{"loading": 99}], None),         # Statut inconnu
# ])

# def test_check_loading_status(return_values, expected_result, mock_kwargs):
#     """Test de check_loading_status avec différents scénarios."""
#     with patch("diagho_uploader.api_handler.api_get_loadingstatus", side_effect=return_values), patch("time.sleep"):
#         check_loading_status(0, **mock_kwargs)
#         assert check_loading_status(0, **mock_kwargs) == expected_result