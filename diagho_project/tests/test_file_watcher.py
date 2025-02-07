import os
from unittest import mock
import pytest
import shutil
from pathlib import Path
from unittest.mock import patch
from datetime import datetime
from time import sleep
import tempfile


from diagho_uploader.file_watcher import *






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
    



# Test de la fonction list_files
def test_list_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer des fichiers temporaires
        file1 = os.path.join(tmpdir, "file1.txt")
        file2 = os.path.join(tmpdir, "file2.txt")
        with open(file1, "w") as f:
            f.write("Content of file1")
        with open(file2, "w") as f:
            f.write("Content of file2")
        
        # Tester la fonction list_files
        files = list_files(tmpdir)
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert len(files) == 2



@pytest.fixture
def mock_paths(tmp_path):
    """Fixture créant des chemins de test dans un répertoire temporaire."""
    file_path = tmp_path / "test_file.txt"
    target_directory = tmp_path / "target_dir"
    
    # Création d'un fichier de test
    file_path.write_text("test content")

    return str(file_path), str(target_directory)



@patch("common.log_utils.log_message")
@patch("shutil.copy")  # Patch shutil.copy correctement
@patch("pathlib.Path.mkdir")  # Patch Path.mkdir correctement
def test_copy_file(mock_mkdir, mock_copy, mock_log, mock_paths, mock_logger):
    """Test de la fonction copy_file."""
    file_path, target_directory = mock_paths
    copy_file(file_path, target_directory)
    # Vérifier que mkdir a bien été appelé pour créer le dossier cible
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    # Vérifier que le fichier a bien été copié
    mock_copy.assert_called_once_with(file_path, target_directory)
    # Vérifier que le log a bien été écrit
    mock_logger.info.assert_called_with(f"Copy file: {file_path} to: {target_directory}")


@patch("common.log_utils.log_message")
@patch("os.remove")  # Patch os.remove
def test_remove_file_success(mock_remove, mock_log, mock_logger):
    """Test de la suppression réussie d'un fichier."""
    file_path = "/fake/path/to/file.txt"
    remove_file(file_path)
    # Vérifier que os.remove a bien été appelé
    mock_remove.assert_called_once_with(file_path)
    # Vérifier que le log de succès a été appelé
    mock_logger.info.assert_called_with(f"Remove file: {file_path}")


@patch("common.log_utils.log_message")
@patch("os.remove", side_effect=FileNotFoundError("File not found"))  # Simule une erreur
def test_remove_file_failure(mock_remove, mock_logger):
    """Test de la suppression échouée d'un fichier."""
    file_path = "/fake/path/to/missing_file.txt"
    remove_file(file_path)
    # Vérifier que os.remove a bien été appelé
    mock_remove.assert_called_once_with(file_path)



