import tempfile
import pytest
import pandas as pd
from unittest import mock
import logging

from diagho_create_inputs.utils import validate_tsv_headers, remove_empty_keys, get_or_compute_checksum, validate_tsv_columns, validate_column_value
from diagho_create_inputs.parser import *
from common.log_utils import *


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
    with pytest.raises(TSVValidationError):
        result = validate_tsv_headers(input_tsv, required_headers)
        # assert result is False  # Doit échouer car il manque des colonnes
        mock_logger.error.assert_called_with('Error: Missing required columns: [\'file_type\']')

# Test pour vérifier que des colonnes inattendues sont présentes
def test_validate_tsv_headers_unexpected_columns(data_dir, mock_logger):
    input_tsv = data_dir / "invalid_header_input2.tsv"
    required_headers = ['filename', 'checksum', 'file_type', 'sample', 'bam_path', 'family_id', 'person_id', 'father_id','mother_id', 'sex', 'is_affected', 'last_name', 'first_name', 'date_of_birth', 'hpo', 'interpretation_title', 'is_index', 'project', 'assignee', 'priority', 'person_note', 'assembly', 'data_title']
    with pytest.raises(TSVValidationError):
        result = validate_tsv_headers(input_tsv, required_headers)
        # assert result is False  # Doit échouer car il y a une colonne inattendue
        mock_logger.error.assert_called_with('Warning: Unexpected columns present: [\'unexpected_column\']')

# Test pour vérifier qu'une erreur de lecture de fichier est correctement gérée
def test_validate_tsv_headers_read_error(mock_logger):
    required_headers = ['col1', 'col2', 'col3']
    # Simuler une exception lors de la lecture du fichier
    with pytest.raises(TSVValidationError):
        with mock.patch('pandas.read_csv', side_effect=Exception('File read error')):
            result = validate_tsv_headers('non_existent_file.tsv', required_headers)
            # assert result is False  # Vérifier que la fonction retourne False
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
    with pytest.raises(TSVValidationError):
        result = validate_tsv_columns(file_path, required_headers)
        # assert result is False  # Le fichier doit être valide
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
def test_get_or_compute_checksum_calculate_md5(mock_logger):
    sample_data = {"filename": "file1.txt"}
    sample_id = "SAMPLE_02"
    biofiles_directory = "biofiles_path"
    with mock.patch("diagho_create_inputs.utils.md5", return_value="computed_md5"):
        result = get_or_compute_checksum(sample_data, sample_id, biofiles_directory)
        assert result == "computed_md5"
        mock_logger.warning.assert_called_with(f"Sample: SAMPLE_02 - Calculating MD5 for file: file1.txt")

# Cas 3: Le checksum est absent, mais `biofiles_directory` n'est pas fourni → ValueError
def test_get_or_compute_checksum_no_directory(mock_logger):
    sample_data = {"filename": "file1.txt"}
    sample_id = "SAMPLE_03"
    with pytest.raises(ValueError, match="Can't calculate MD5 for file: file1.txt."):
        get_or_compute_checksum(sample_data, sample_id)
        mock_logger.error.assert_called_with(f"Sample: SAMPLE_03 - Can't calculate MD5 for file: file1.txt.")
        

# Cas 4: Erreur lors du calcul du checksum → Vérifier qu'une exception est levée
def test_get_or_compute_checksum_md5_error(mock_logger):
    sample_data = {"filename": "file1.txt"}
    sample_id = "SAMPLE_04"
    biofiles_directory = "biofiles_path"

    with mock.patch("diagho_create_inputs.utils.md5", side_effect=Exception("File not found")), pytest.raises(Exception, match="File not found"):
        get_or_compute_checksum(sample_data, sample_id, biofiles_directory)
        mock_logger.warning.assert_called_with(f"Sample: SAMPLE_04 - Calculating MD5 for file: file1.txt")
        
        


def create_temp_file(content, encoding="utf-8"):
    """Crée un fichier temporaire avec le contenu donné et retourne son chemin."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding=encoding)
    temp_file.write(content)
    temp_file.close()
    return temp_file.name     

def test_remove_trailing_empty_lines():
    """Test suppression des lignes vides à la fin du fichier."""
    content = "Line 1\nLine 2\nLine 3\n\n\n"  # Lignes vides à la fin
    expected_output = "Line 1\nLine 2\nLine 3\n"  # Résultat attendu

    temp_file_path = create_temp_file(content)
    try:
        remove_trailing_empty_lines(temp_file_path, encoding="utf-8")
        with open(temp_file_path, "r", encoding="utf-8") as file:
            result = file.read()
        assert result == expected_output, f"Output incorrect: {result}"
    finally:
        os.remove(temp_file_path)  # Nettoyage du fichier temporaire

def test_no_trailing_empty_lines():
    """Test avec un fichier sans ligne vide à la fin (ne doit rien changer)."""
    content = "Line 1\nLine 2\nLine 3\n"
    temp_file_path = create_temp_file(content)
    try:
        remove_trailing_empty_lines(temp_file_path, encoding="utf-8")
        with open(temp_file_path, "r", encoding="utf-8") as file:
            result = file.read()
        assert result == content, "Le fichier ne devait pas être modifié."
    finally:
        os.remove(temp_file_path)






@pytest.mark.parametrize("column_name, value, expected", [
    # FILENAME
    ("filename", "file1.txt", True),
    ("filename", "", False),
    
    # FILE_TYPE
    ("file_type", "SNV", True),
    ("file_type", "CNV", True),
    ("file_type", "INVALID_TYPE", False),
    
    # DATE_OF_BIRTH
    ("date_of_birth", "2024-02-06", True),  # Actuellement, la fonction accepte tout
    ("date_of_birth", "not-a-date", True),  # La gestion du format est désactivée
    
    # ASSEMBLY
    ("assembly", "GRCh37", True),
    ("assembly", "GRCh38", True),
    ("assembly", "T2T", True),
    ("assembly", "hg19", False),
    
    # SAMPLE
    ("sample", "Sample_001", True),
    ("sample", "", False),
    
    # BAM_PATH
    ("bam_path", "/path/to/file.bam", True),
    ("bam_path", "", False),
    
    # FAMILY_ID
    ("family_id", "FAM123", True),
    ("family_id", "", False),
    
    # PERSON_ID
    ("person_id", "P12345", True),
    ("person_id", "", False),
    
    # SEX
    ("sex", "male", True),
    ("sex", "female", True),
    ("sex", "unknown", True),
    ("sex", "other", False),
    
    # IS_AFFECTED
    ("is_affected", "0", True),
    ("is_affected", "1", True),
    ("is_affected", "2", False),
    
    # INTERPRETATION_TITLE
    ("interpretation_title", "Some title", True),
    ("interpretation_title", "", False),
    
    # IS_INDEX
    ("is_index", "0", True),
    ("is_index", "1", True),
    ("is_index", "2", False),
    
    # PROJECT
    ("project", "ProjectX", True),
    ("project", "", False),
    
    # AUTRE (par défaut accepté)
    ("unknown_column", "any value", True),
    ("another_column", "", True),
])
def test_validate_column_value(column_name, value, expected):
    """Teste la fonction validate_column_value pour différents cas."""
    assert validate_column_value(column_name, value) == expected
    
    
    
@pytest.mark.parametrize("date_str, expected", [
    # Cas valides
    ("06/02/2025", "2025-02-06"),
    ("31/12/1999", "1999-12-31"),
    ("01/01/2000", "2000-01-01"),
    
    # Cas invalides
    ("2025-02-06", ""),  # Format incorrect (YYYY-MM-DD au lieu de DD/MM/YYYY)
    ("06-02-2025", ""),  # Mauvais séparateur
    ("06/13/2025", ""),  # Mois invalide (13)
    ("32/01/2025", ""),  # Jour invalide (32)
    ("", ""),  # Chaîne vide
    ("not-a-date", ""),  # Chaîne aléatoire
    ("29/02/2021", ""),  # Année non bissextile (pas de 29 février)
    ("29/02/2024", "2024-02-29"),  # Année bissextile (ok)
])
def test_parse_date(date_str, expected):
    """Teste la fonction parse_date pour différents cas."""
    assert parse_date(date_str) == expected



def test_write_JSON_file():
    # Données d'exemple
    data_dict = {'key1': 'value1', 'key2': 'value2'}
    key_name = 'my_data'
    output_file = 'test_output.json'

    # Appeler la fonction pour écrire dans le fichier
    write_JSON_file(data_dict, key_name, output_file)

    # Vérifier si le fichier a été écrit correctement
    with open(output_file, 'r', encoding='utf-8') as f:
        written_content = json.load(f)

    # Le contenu attendu
    expected_json = {'my_data': ['value1', 'value2']}

    # Comparer le contenu du fichier écrit avec le JSON attendu
    assert written_content == expected_json, f"Expected {expected_json}, but got {written_content}"

    # Supprimer le fichier temporaire après le test
    os.remove(output_file)
    





# Test pour un fichier JSON valide
def test_load_data_from_config_file_valid():
    # Créer un fichier temporaire JSON
    test_data = {"excludeColumns": ["col1", "col2", "col3"]}
    test_file = 'test_valid_config.json'
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)
    
    # Appeler la fonction pour charger les données du fichier
    result = load_data_from_config_file(test_file)
    
    # Vérifier si le résultat est correct
    assert result == test_data, f"Expected {test_data}, but got {result}"
    
    # Supprimer le fichier temporaire après le test
    os.remove(test_file)
    
    
# Test pour un fichier inexistant
def test_load_data_from_config_file_not_found(mock_logger):
    test_file = 'non_existent_file.json'
    # Utiliser patch pour vérifier si le message de log est appelé
    result = load_data_from_config_file(test_file)
    # Vérifier que la fonction retourne une chaîne vide
    assert result == "", "Expected empty string when file not found"
    # Vérifier que le message de log a été appelé avec le bon message
    mock_logger.warning.assert_called_with(f"File not found: {test_file}.")
    