import pytest
import pandas as pd
from unittest import mock
import logging

from diagho_create_inputs.utils import validate_tsv_headers, remove_empty_keys, get_or_compute_checksum, validate_tsv_columns, validate_column_value
from diagho_create_inputs.parser import *


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


@pytest.fixture
def data_dir():
    return Path(__file__).parent / "data"

# Test pour vérifier que les en-têtes sont valides
def test_validate_tsv_headers_valid(data_dir):
    input_tsv = data_dir / "valid_input.tsv"
    required_headers = ['filename', 'checksum', 'file_type', 'sample', 'bam_path', 'family_id', 'person_id', 'father_id','mother_id', 'sex', 'is_affected', 'last_name', 'first_name', 'date_of_birth', 'hpo', 'interpretation_title', 'is_index', 'project', 'assignee', 'priority', 'person_note', 'assembly', 'data_title']
    result = validate_tsv_headers(input_tsv, required_headers)
    assert result is True  # Doit passer si le fichier contient les bonnes colonnes

# Test pour vérifier que les en-têtes sont manquants
def test_validate_tsv_headers_missing_columns(data_dir, mock_logger):
    input_tsv = data_dir / "invalid_header_input.tsv"
    required_headers = ['filename', 'checksum', 'file_type', 'sample', 'bam_path', 'family_id', 'person_id', 'father_id','mother_id', 'sex', 'is_affected', 'last_name', 'first_name', 'date_of_birth', 'hpo', 'interpretation_title', 'is_index', 'project', 'assignee', 'priority', 'person_note', 'assembly', 'data_title']
    result = validate_tsv_headers(input_tsv, required_headers)
    assert result is False  # Doit échouer car il manque des colonnes
    mock_logger.error.assert_called_with('Error: Missing required columns: [\'file_type\']')

# Test pour vérifier que des colonnes inattendues sont présentes
def test_validate_tsv_headers_unexpected_columns(data_dir, mock_logger):
    input_tsv = data_dir / "invalid_header_input2.tsv"
    required_headers = ['filename', 'checksum', 'file_type', 'sample', 'bam_path', 'family_id', 'person_id', 'father_id','mother_id', 'sex', 'is_affected', 'last_name', 'first_name', 'date_of_birth', 'hpo', 'interpretation_title', 'is_index', 'project', 'assignee', 'priority', 'person_note', 'assembly', 'data_title']
    result = validate_tsv_headers(input_tsv, required_headers)
    assert result is False  # Doit échouer car il y a une colonne inattendue
    mock_logger.error.assert_called_with('Warning: Unexpected columns present: [\'unexpected_column\']')
    
        

# Test pour vérifier qu'une erreur de lecture de fichier est correctement gérée
def test_validate_tsv_headers_read_error(mock_logger):
    required_headers = ['col1', 'col2', 'col3']
    # Simuler une exception lors de la lecture du fichier
    with mock.patch('pandas.read_csv', side_effect=Exception('File read error')):
        result = validate_tsv_headers('non_existent_file.tsv', required_headers)
        assert result is False  # Vérifier que la fonction retourne False
        mock_logger.error.assert_called_with('Error reading the file: File read error')





@pytest.fixture
def data_dir():
    return Path(__file__).parent / "data"

def test_validate_tsv_columns_valid(data_dir, mock_logger):
    file_path = data_dir / "valid_columns_input.tsv"
    required_headers = ['filename', 'checksum', 'file_type', 'sample', 'bam_path', 'family_id', 'person_id', 'father_id','mother_id', 'sex', 'is_affected', 'last_name', 'first_name', 'date_of_birth', 'hpo', 'interpretation_title', 'is_index', 'project', 'assignee', 'priority', 'person_note', 'assembly', 'data_title']
    result = validate_tsv_columns(file_path, required_headers)
    assert result is True  # Le fichier doit être valide
    mock_logger.info.assert_called_with(f"File '{file_path}' is valid.")


def test_validate_tsv_columns_invalid_value(data_dir, mock_logger):
    file_path = data_dir / "invalid_columns_input.tsv"
    required_headers = ['filename', 'checksum', 'file_type', 'sample', 'bam_path', 'family_id', 'person_id', 'father_id','mother_id', 'sex', 'is_affected', 'last_name', 'first_name', 'date_of_birth', 'hpo', 'interpretation_title', 'is_index', 'project', 'assignee', 'priority', 'person_note', 'assembly', 'data_title']
    result = validate_tsv_columns(file_path, required_headers)
    assert result is False  # Le fichier doit être valide
    mock_logger.error.assert_called_with(f"Valeur invalide dans la colonne 'file_type' à la ligne 2: A")
    
    
        
        

# Test avec un dictionnaire contenant des clés vides
def test_remove_empty_keys_basic():
    d = {"a": "value", "b": None, "c": "", "d": 42}
    expected = {"a": "value", "d": 42}
    assert remove_empty_keys(d) == expected
    
# Test avec un dictionnaire contenant un sous-dictionnaire
def test_remove_empty_keys_nested():
    d = {"a": "value", "b": {"c": None, "d": "ok"}, "e": ""}
    expected = {"a": "value", "b": {"d": "ok"}}
    assert remove_empty_keys(d) == expected
    
# Test avec un dictionnaire complètement vide
def test_remove_empty_keys_empty_dict():
    d = {}
    expected = {}
    assert remove_empty_keys(d) == expected
    
# Test avec un dictionnaire ne contenant aucune clé vide
def test_remove_empty_keys_no_empty_values():
    d = {"a": "hello", "b": 123, "c": [1, 2, 3]}
    expected = {"a": "hello", "b": 123, "c": [1, 2, 3]}
    assert remove_empty_keys(d) == expected

# Test avec une structure plus complexe
def test_remove_empty_keys_deeply_nested():
    d = {
        "a": {"b": {"c": None, "d": ""}, "e": {"f": "value"}},
        "g": "",
        "h": "keep",
    }
    expected = {"a": {"e": {"f": "value"}}, "h": "keep"}
    assert remove_empty_keys(d) == expected

# Test avec une structure plus complexe
def test_remove_empty_keys_deeply_nested():
    d = {
        "a": {"b": {"c": None, "d": ""}, "e": {"f": "value"}},
        "g": "",
        "h": "keep",
    }
    expected = {"a": {"e": {"f": "value"}}, "h": "keep"}
    print(remove_empty_keys(d))
    assert remove_empty_keys(d) == expected
    
# Test avec une entrée qui n'est pas un dictionnaire (doit retourner tel quel)
@pytest.mark.parametrize("non_dict_input", [None, 123, "string", [1, 2, 3], (4, 5)])
def test_remove_empty_keys_non_dict(non_dict_input):
    assert remove_empty_keys(non_dict_input) == non_dict_input
    
    
    



# Cas 1: Le checksum est déjà présent dans sample_data
def test_get_or_compute_checksum_already_present():
    sample_data = {"checksum": "abc123", "filename": "file1.txt"}
    sample_id = "SAMPLE_01"
    result = get_or_compute_checksum(sample_data, sample_id)
    assert result == "abc123"
    
# Cas 2: Le checksum est absent, mais on le calcule avec md5()
def test_get_or_compute_checksum_calculate_md5():
    sample_data = {"filename": "file1.txt"}
    sample_id = "SAMPLE_02"
    biofiles_directory = "biofiles_path"

    with mock.patch("diagho_create_inputs.utils.md5", return_value="computed_md5"):
        result = get_or_compute_checksum(sample_data, sample_id, biofiles_directory)
        assert result == "computed_md5"

# Cas 3: Le checksum est absent, mais `biofiles_directory` n'est pas fourni → ValueError
def test_get_or_compute_checksum_no_directory():
    sample_data = {"filename": "file1.txt"}
    sample_id = "SAMPLE_03"

    with pytest.raises(ValueError, match="Can't calculate MD5 for file: file1.txt."):
        get_or_compute_checksum(sample_data, sample_id)
        

# Cas 4: Erreur lors du calcul du checksum → Vérifier qu'une exception est levée
def test_get_or_compute_checksum_md5_error():
    sample_data = {"filename": "file1.txt"}
    sample_id = "SAMPLE_04"
    biofiles_directory = "biofiles_path"

    with mock.patch("diagho_create_inputs.utils.md5", side_effect=Exception("File not found")), \
         pytest.raises(Exception, match="File not found"):
        get_or_compute_checksum(sample_data, sample_id, biofiles_directory)
        
        
        


@pytest.fixture
def data_dir():
    return Path(__file__).parent / "data"

# Cas 1: Fichier TSV valide, conversion réussie
def test_diagho_tsv2json_valid(data_dir, tmp_path):
    input_tsv = data_dir / "valid_input.tsv"
    output_json = data_dir / "output.json"

    diagho_tsv2json(input_tsv, output_json)

    with open(output_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "0" in data # il y a bien 1 ligne
    assert data["0"]["filename"] == "file01.vcf.gz" # vérif de la valeur de la colonne