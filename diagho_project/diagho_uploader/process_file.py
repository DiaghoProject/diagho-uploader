import json
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging

from .api_handler import *
from common.config_loader import *
from common.file_utils import *
from common.mail_utils import *


def diagho_upload_file(**kwargs):
    """
    Process input file (JSON).
    Load biofiles in Diagho.
    Load JSON file.

    Args:
        file_path (str): input file (JSON).
        config (dict): configuration.
    """
    
    # Args
    config = kwargs.get("config")
    file_path = kwargs.get("file_path")
    
    logging.getLogger("START_UPLOADER").info(f">>> JSON file: {file_path}")
    
    # Load configuration
    logging.getLogger("LOAD_CONFIGURATION").info(f"Load config.yaml")
    settings = load_configuration(config)
    print(settings["recipients"])  # Liste des destinataires d'emails
    print(settings["path_biofiles"])  # Chemin des biofiles
    print(settings["diagho_api"]["login"])  # Endpoint pour login
    
    
    # Test fichier JSON OK : missing key etc...
    try:
        dict_biofiles = validate_json_input(file_path)
        print("Fichier JSON valide, traitement possible.")
    except ValueError as e:
        logging.getLogger("VALIDATE_JSON_INPUT").error(f"Erreur de validation du fichier JSON: {e}")
        send_mail_alert(settings["recipients"], f"Erreur de validation du fichier JSON: {file_path}\n\n{e}")
        print(f"Erreur de validation : {e}")
        
    
    
    
    # Check Diagho API
    
        # Si KO = envoi alerte par mail
    
    
    # API login
    
        # Si KO = envoi alerte par mail
        
    
    
    # Paralléliser le traitement des biofiles
    
    
    
    
    
    # Import du JSON
    
        # Si KO = envoi alerte par mail
    
        
    
    

def validate_json_input(json_input):
    """
    Valide la structure du fichier JSON.
    """
    try:
        with open(json_input, 'r') as json_file:
            input_data = json.load(json_file)

        if "files" not in input_data:
            
            raise ValueError("Le fichier JSON doit contenir une clé 'files'.")

        required_keys = ["filename", "checksum", "assembly", "samples"]
        
        for file in input_data["files"]:
            # Vérifier la présence des clés obligatoires
            missing_keys = [key for key in required_keys if key not in file]
            if missing_keys:
                raise ValueError(f"Clés manquantes: {missing_keys}")

            # Vérifier la structure des samples
            if not isinstance(file["samples"], list) or not file["samples"]:
                raise ValueError(f"'samples' doit être une liste non vide pour '{file['filename']}'.")

            for sample in file["samples"]:
                if "person" not in sample:
                    raise ValueError(f"Clé 'person' manquante dans un sample du fichier '{file['filename']}'.")
        return input_data

    except (json.JSONDecodeError, FileNotFoundError) as e:
        raise ValueError(f"Erreur lors de la lecture du fichier JSON : {e}")
