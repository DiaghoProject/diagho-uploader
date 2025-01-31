import json
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging

from .api_handler import *
from .config_loader import *


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
    
        # Si KO = envoi alerte par mail
    
    
    
    
    
    
    # Check Diagho API
    
        # Si KO = envoi alerte par mail
    
    
    # API login
    
        # Si KO = envoi alerte par mail
        
    
    
    # Paralléliser le traitement des biofiles
    
    
    
    
    
    # Import du JSON
    
        # Si KO = envoi alerte par mail
    
        
    
    
    
    
    
     