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
from common.api_utils import *


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
    
    # Get API endpoints
    diagho_api = get_api_endpoints(config)
    
    
    # Test si fichier JSON OK
    try:
        dict_biofiles = validate_json_input(file_path)
    except ValueError as e:
        logging.getLogger("VALIDATE_JSON_INPUT").error(f"Erreur de validation du fichier JSON: {e}")
        send_mail_alert(settings["recipients"], f"Erreur de validation du fichier JSON: {file_path}\n\n{e}")
        print(f"Erreur de validation : {e}")
        return
        
    
    
    
    # Check Diagho API
    try:
        api_healthcheck(diagho_api)
    except ValueError as e:
        send_mail_alert(settings["recipients"], f"API healthcheck error : {e}")
        logging.getLogger("API_HEALTHCHECK").error(f"API healthcheck error : {e}")
        return
    
    # API login
    try:
        result = api_login(config, diagho_api)
        if result.get("error"):
            error_message = result.get("error")
            send_mail_alert(settings["recipients"], f"API login error: {error_message} ")
            logging.getLogger("API_LOGIN").error(f"API login error : {error_message} ")
            return
    except ValueError as e:
        send_mail_alert(settings["recipients"], f"API login error: {e}")
        logging.getLogger("API_LOGIN").error(f"API login error : {e}")
        return
        
    print("\n continuer... \n")
    
    # Paralléliser le traitement des biofiles
    logging.getLogger("PROCESS_BIOFILES").info(f"Process each biofile...")
    
    
    
    
    
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
