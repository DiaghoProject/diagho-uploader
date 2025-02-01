import hashlib
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
        json_data = validate_json_input(file_path)
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
    
    # Get settings from config file
    path_biofiles = settings["path_biofiles"]
    max_retries = settings["get_biofile_max_retries"]
    delay = settings["get_biofile_delay"]
    recipients = settings["recipients"]
    
    with ThreadPoolExecutor(max_workers=5) as executor:  # Utiliser 5 threads par exemple
        futures = []
        
        # Get filenames of the biofiles
        biofiles = json_data["files"]
        filenames = [item.get("filename") for item in biofiles if "filename" in item]
        
        # for each biofile...
        for filename in filenames:
            # Get absolute path
            biofile = os.path.join(path_biofiles, filename)            
            biofile_infos = get_biofile_informations(biofiles, filename)
            # pretty_print_json_string(biofile_infos)
            
            # A partir d'ici : paraléliser les traitements
            futures.append(executor.submit(process_biofile_task, settings, biofile, biofile_infos, diagho_api))

        # Attendre que toutes les tâches soient terminées
        for future in futures:
            future.result()
            
    logging.getLogger("PROCESSING_BIOFILE").info(f"All biofiles have been loaded in Diagho")

            
            
            

    
    
    
    # Import du JSON
    
        # Si KO = envoi alerte par mail
    
        


# Gère le traitement d'un biofile
def process_biofile_task(settings, biofile, biofile_infos, diagho_api):
    """Fonction qui gère le traitement d'un fichier bio (VCF ou BED)"""
    logging.getLogger("PROCESS_BIOFILE_TASK").info(f"Start biofile processing: {biofile}")
    
    # Récupérer les settings
    path_biofiles = settings["path_biofiles"]
    max_retries = settings["get_biofile_max_retries"]
    delay = settings["get_biofile_delay"]
    recipients = settings["recipients"]
    
    # Récupération du biofile (si pas présent au bout de X tentatives... alerte et stop)
    if not wait_for_biofile(biofile, max_retries, delay):
        content = f"Failed to process.\n\nBiofile: {biofile} does not exist in : {path_biofiles}."
        send_mail_alert(recipients, content)
        logging.getLogger("PROCESSING_BIOFILE").error(f"Biofile: {biofile} does not exist.")
        return
    
    # Biofile found
    logging.getLogger("PROCESSING_BIOFILE").info(f"Biofile '{biofile}' found... Continue...")
    
    # Get informations about biofile
    try:
        biofile_type = get_biofile_type(biofile)
        print("biofile_type:", biofile_type)
        assembly = biofile_infos["assembly"]
        accession_id = settings["accessions"][assembly]
    except ValueError as e:
        send_mail_alert(settings["recipients"], f"API login error: {e}")
        logging.getLogger("API_LOGIN").error(f"API login error : {e}")
        return
        
    
    # Verifier le checksum du JSON et celui calculé du biofile
    md5_biofile = md5(biofile)
    md5_from_json = biofile_infos.get("checksum")
    
    # Si checksum identiques : POST biofile
    kwargs = {
        "settings": settings,
        "biofile": biofile,
        "diagho_api": diagho_api,
        "biofile_type": biofile_type,
        "assembly": assembly,
        "accession_id": accession_id,
        "checksum": md5_biofile
    }
    checksum = api_post_biofile(**kwargs)
    
    # Vérifier que le checksum du biofile posté est le même que celui du biofile
    if not check_md5sum(checksum, md5_biofile):
        logging.getLogger("PROCESSING_BIOFILE").error(f"MD5 checksum mismatch for biofile: {biofile}")
        return
    logging.getLogger("PROCESSING_BIOFILE").info(f"{biofile} : Checksums are identical. Continue.")
    
    # check le statut de chargement
    time.sleep(120) # nécessaire pour l'instant car bug initial (statut en FAILURE)
    loading_status = check_loading_status(**kwargs)
    
    # process_biofile(config, biofile, biofile_type, checksum_current_biofile, file, assembly, json_input, diagho_api)       
        
    

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


def wait_for_biofile(biofile, max_retries=100, delay=10):
    """
    Attend l'existence du biofile avec un nombre de tentatives limité.
    """
    logger = logging.getLogger("PROCESSING_BIOFILE")
    
    for attempt in range(1, max_retries + 1):
        if os.path.exists(biofile):
            return True
        logger.warning(f"Biofile {biofile} not found... attempt {attempt}")
        time.sleep(delay)
    logger.info(f"Biofile {biofile} found... Continue...")
    return False  # Échec après toutes les tentatives

def md5(filepath):
    """
    Computes the MD5 hash of a file.
    """    
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        error_msg = f"File not found: {filepath}"
    except IOError as e:
        error_msg = f"IO error while reading {filepath}: {e}"
    except Exception as e:
        error_msg = f"Unexpected error while computing MD5 for {filepath}: {e}"
    
    logging.getLogger("MD5_HASH").error(error_msg)
    return {"error": error_msg}

def get_biofile_informations(data, filename):
    """
    Recherche dans la liste de dictionnaires le dictionnaire contenant le 'filename'.
    """
    return next((item for item in data if item.get("filename") == filename), None)

def get_biofile_type(biofile):
    if biofile.endswith('.vcf') or biofile.endswith('.vcf.gz'):
        return 'SNV'
    elif biofile.endswith('.bed') or biofile.endswith('.tsv'):
        return 'CNV'
    else:
        error_message = f"Error: Unsupported biofile type for file: {biofile}"
        logging.getLogger("API_POST_BIOFILE").error(error_message)
        send_mail_alert(error_message)
        return None
    
def check_md5sum(checksum1, checksum2):
    """
    Compares two MD5 checksums.
    """
    if not isinstance(checksum1, str) or not isinstance(checksum2, str):
        raise TypeError("MD5 should be strings.")
    if len(checksum1) != 32 or len(checksum2) != 32:
        raise ValueError("MD5 length issue. Should be 32.")
    return checksum1.lower() == checksum2.lower()