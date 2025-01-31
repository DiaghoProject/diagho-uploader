import os
import pytest
import shutil
from unittest.mock import patch
from datetime import datetime
from time import sleep
import tempfile


from diagho_uploader.file_watcher import *

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



