#!/usr/bin/python3

import pytest
import json
from unittest import mock
from unittest.mock import patch, MagicMock
import pandas as pd

import pytest
import json
import tempfile
from pathlib import Path

# Importer la fonction que vous voulez tester
from diagho_uploader.process_file import *


# Test : JSON valide
def test_get_files_infos_valid_json():
    """Test avec un JSON valide contenant les informations nécessaires."""
    input_data = {
        "files": [
            {
                "filename": "file1.vcf.gz",
                "checksum": "abc123",
                "assembly": "hg19",
                "samples": [
                    {"person": "person1"},
                    {"person": "person2"}
                ]
            },
            {
                "filename": "file2.vcf.gz",
                "checksum": "def456",
                "assembly": "hg38",
                "samples": [
                    {"person": "person3"}
                ]
            }
        ]
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
        temp_file.write(json.dumps(input_data).encode())
        temp_file_path = temp_file.name

    try:
        result = get_files_infos(temp_file_path)

        expected = {
            "file1.vcf.gz": {
                "checksum": "abc123",
                "assembly": "hg19",
                "persons": ["person1", "person2"]
            },
            "file2.vcf.gz": {
                "checksum": "def456",
                "assembly": "hg38",
                "persons": ["person3"]
            }
        }

        assert result == expected
    finally:
        Path(temp_file_path).unlink()  # Supprimer le fichier temporaire
        

# Test : invalide JSON
def test_get_files_infos_invalid_json():
    """Test avec un fichier JSON mal formé."""
    # JSON invalide
    invalid_json_content = "{ invalid_json: true, }"  # Syntaxe JSON invalide

    # Écriture dans un fichier temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
        temp_file.write(invalid_json_content.encode())
        temp_file_path = temp_file.name

    try:
        # Vérifie qu'une exception JSONDecodeError est levée
        with pytest.raises(json.JSONDecodeError):
            get_files_infos(temp_file_path)
    finally:
        Path(temp_file_path).unlink()
        

# Test : missing data
def test_get_files_infos_missing_keys():
    """Test avec un JSON valide mais des clés manquantes."""
    # JSON d'entrée avec une clé manquante ('checksum')
    input_data = {
        "files": [
            {
                "filename": "file1.txt",
                # "checksum": "abc123",  # Clé manquante
                "assembly": "hg19",
                "samples": [
                    {"person": "person1"}
                ]
            }
        ]
    }

    # Écriture dans un fichier temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
        temp_file.write(json.dumps(input_data).encode())
        temp_file_path = temp_file.name

    try:
        # Vérifie qu'une exception ValueError est levée
        with pytest.raises(ValueError, match="Clé manquante : 'checksum'"):
            get_files_infos(temp_file_path)
    finally:
        Path(temp_file_path).unlink()


# Test : JSON vide
def test_get_files_infos_empty_json():
    """Test avec un JSON vide."""
    input_data = {"files": []}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
        temp_file.write(json.dumps(input_data).encode())
        temp_file_path = temp_file.name

    try:
        result = get_files_infos(temp_file_path)
        assert result == {}
    finally:
        Path(temp_file_path).unlink()
