import os
import pytest
import shutil
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



