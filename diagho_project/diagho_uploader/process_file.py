import hashlib
import json
import shutil
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Logs
from common.logger_config import logger 

from .api_handler import *
from common.config_loader import *
from common.file_utils import *
from common.mail_utils import *
from common.api_utils import *
from common.log_utils import *


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
    
    log_info("START_UPLOADER", f"JSON file: {file_path}")
    
    
    # Load configuration
    log_info("LOAD_CONFIGURATION", f"Load 'config.yaml'")
    settings = load_configuration(config)
    
    # Get API endpoints
    diagho_api = get_api_endpoints(config)
    
    # Test si fichier JSON OK
    try:
        json_data = validate_json_input(file_path)
        log_info("VALIDATE_JSON_INPUT", f"JSON file validation : pass")
    except ValueError as e:
        log_error("VALIDATE_JSON_INPUT", f"Erreur de validation du fichier JSON: {e}")
        send_mail_alert(settings["recipients"], f"Erreur de validation du fichier JSON: {file_path}\n\n{e}")
        return
        
    
    # Check Diagho API
    try:
        api_healthcheck(diagho_api)
    except ValueError as e:
        send_mail_alert(settings["recipients"], f"API healthcheck error : {e}")
        return
    
    # API login
    try:
        result = api_login(config, diagho_api)
        if result.get("error"):
            error_message = result.get("error")
            send_mail_alert(settings["recipients"], f"API login error: {error_message} ")
            return
    except ValueError as e:
        send_mail_alert(settings["recipients"], f"API login error: {e}")
        return
        
    print("\n continuer... \n")
    
    
    
    
    # Paralléliser le traitement des biofiles
    log_info("PROCESS_BIOFILES", "Process each biofile...")
        
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
                        
            # A partir d'ici : paraléliser les traitements
            futures.append(executor.submit(process_biofile_task, settings, biofile, biofile_infos, diagho_api))

        # Attendre que toutes les tâches soient terminées
        for future in futures:
            future.result()
            
        # Traitement des biofiles terminé  
     
    log_info("PROCESS_BIOFILE", f"All biofiles have been loaded in Diagho")

    time.sleep(5)
    
    # Upload JSON file 
    log_info("IMPORT_CONFIGURATIONS", f"Import JSON: {os.path.basename(file_path)}") 
    kwargs = {
        'diagho_api': diagho_api,
        'file': file_path,
        'recipients': recipients
    }
    response = api_post_config(**kwargs)

    # Vérifie si import du JSON OK    
    check_api_response(response, **kwargs)
    


# Gère le traitement d'un biofile
def process_biofile_task(settings, biofile, biofile_infos, diagho_api):
    """Fonction qui gère le traitement d'un fichier bio (VCF ou BED)"""
    log_info("PROCESS_BIOFILE_TASK", f"Start biofile processing: {biofile}")
        
    # Récupérer les settings
    path_biofiles = settings["path_biofiles"]
    max_retries = settings["get_biofile_max_retries"]
    delay = settings["get_biofile_delay"]
    recipients = settings["recipients"]
    
    # Récupération du biofile (si pas présent au bout de X tentatives... alerte et stop)
    if not wait_for_biofile(biofile, max_retries, delay):
        content = f"Failed to process.\n\nBiofile: {biofile} does not exist in : {path_biofiles}."
        send_mail_alert(recipients, content)
        log_error("PROCESS_BIOFILE_TASK", f"Biofile: {biofile} does not exist.")
        return
    
    # Biofile found
    log_info("PROCESS_BIOFILE_TASK", f"Biofile '{biofile}' found... Continue...")
        
    # Get informations about biofile
    try:
        biofile_type = get_biofile_type(biofile)
        assembly = biofile_infos["assembly"]
        accession_id = settings["accessions"][assembly]
    except ValueError as e:
        send_mail_alert(settings["recipients"], f"{str(e)}")
        log_error("GET_BIOFILE_TYPE", f"{e}")
        return
        
    
    # Verifier le checksum du JSON et celui calculé du biofile
    md5_biofile = md5(biofile)
    md5_from_json = biofile_infos.get("checksum")
    if not check_md5sum(md5_biofile, md5_from_json):
        log_error("PROCESSING_BIOFILE", f"MD5 checksum mismatch for biofile: {biofile} (JSON)")
        return
    
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
    checksum = api_post_biofile(**kwargs).get("checksum")
    
    # Vérifier que le checksum du biofile posté est le même que celui du biofile
    if not check_md5sum(checksum, md5_biofile):
        log_error("PROCESSING_BIOFILE", f"MD5 checksum mismatch for biofile: {biofile}")
        return
    log_info("PROCESSING_BIOFILE", f"{biofile} : Checksums are identical. Continue.")
        
    # check le statut de chargement
    time.sleep(20) # nécessaire pour l'instant car bug initial (statut en FAILURE)
    
    attempt = 1
    loading_status = check_loading_status(attempt, **kwargs)
    if loading_status: # enlever ça plus tard
        content = f"Biofile has been loaded successfully in Diagho.\n\nBiofile: {biofile}"
        send_mail_info(recipients, content)
    if not loading_status:
        content = f"Failed to load biofile in Diagho.\n\nBiofile: {biofile}"
        send_mail_alert(recipients, content)
    
    # Move biofile in backup folder
    filename = os.path.basename(biofile)
    backup_path = settings.get("path_backup_biofiles")
    destination_path = os.path.join(backup_path, filename)
    shutil.move(biofile, destination_path)
    log_info("PROCESSING_BIOFILE", f"{biofile} : Move biofile to {backup_path}.")
        
    

def validate_json_input(json_input):
    """
    Valide la structure du fichier JSON.
    """
    try:
        with open(json_input, 'r') as json_file:
            input_data = json.load(json_file)

        if "families" not in input_data:
            raise ValueError("Le fichier JSON doit contenir une clé 'families'.")
        if "files" not in input_data:
            raise ValueError("Le fichier JSON doit contenir une clé 'files'.")
        if "interpretations" not in input_data:
            raise ValueError("Le fichier JSON doit contenir une clé 'interpretations'.")

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
            logger.info(f"Biofile {biofile} found... Continue...")
            return True
        logger.warning(f"Biofile {biofile} not found... attempt {attempt}")
        time.sleep(delay)
    logger.error(f"Biofile {biofile} not found after {attempt} attempt. Exit.")
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
    
    log_error("MD5_HASH", error_msg)
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
        error_message = f"Unsupported biofile type for file: {biofile}"
        raise ValueError(error_message)
    
def check_md5sum(checksum1, checksum2):
    """
    Compares two MD5 checksums.
    """
    if not isinstance(checksum1, str) or not isinstance(checksum2, str):
        raise TypeError("MD5 should be strings.")
    if len(checksum1) != 32 or len(checksum2) != 32: # si chaine vide ?
        raise ValueError("MD5 length issue. Should be 32.")
    return checksum1.lower() == checksum2.lower()



def check_loading_status(attempt, **kwargs):
    """
    Vérification du statut de chargement.

    Returns:
        True : si le fichier est chargé (status 3)
        False : si échec de chargement (status 0)
        None : en cas de dépassement du nombre de tentatives ou statut inconnu
    """   
    settings = kwargs.get("settings")
    
    max_retries = settings["check_loading_max_retries"]
    delay = settings["check_loading_delay"]
    
    def get_status():
        return api_get_loadingstatus(**kwargs).get('loading')

    # Obtenir le statut de chargement initial
    status = get_status()
    log_info("LOADING_BIOFILE", f"Loading initial status: {status}")

    # Plusieurs tentatives... Tant que le statut n'est pas 0 ou 3 (FAILURE ou SUCCESS)
    while status not in [0, 3] and attempt < max_retries:
        log_warning("LOADING_BIOFILE", f"Attempt {attempt + 1}: loading_status = {status} ... Retry...")
        time.sleep(delay)
        status = get_status()
        attempt += 1
    
    # Si trop de tentatives, retourner None
    if attempt >= max_retries:
        log_error("LOADING_BIOFILE", f"GET_LOADING_STATUS: Maximum number of attempts reached.")
        return None

    # Vérifier les statuts finaux
    if status == 3: # SUCCESS
        log_info("LOADING_BIOFILE", f"Loading completed successfully.")
        return True
    elif status == 0: # FAILURE
        log_error("LOADING_BIOFILE", f"Loading failed.")
        return False
    else:
        log_info("LOADING_BIOFILE", f"Unknown status: {status}. Exit.")
        return None


def check_api_response(response, **kwargs):
    """
    Vérifie la réponse de l'API après le POST de la config
    et envoie des notifications en fonction du statut.
    """
    recipients = kwargs.get('recipients')
    json_file = kwargs.get('json_file')

    # Si OK
    if response.status_code == 201:
        send_mail_info(recipients, f"JSON file: {json_file}\n\nThe JSON configuration file was posted in Diagho successfully")
        return

    # Si KO
    if response.status_code == 400:
        json_response = response.json()
        search_string = "A person with the same identifier already exist, but is present in another family."
        json_string = json.dumps(json_response)

        if search_string in json_string:
            persons_content = json_response.get('errors', {}).get('families', [{}])[4].get('persons', 'N/A')
            alert_message = f"JSON file: {json_file}\n\nA person with the same identifier already exists but is present in another family:\n{persons_content}"
        else:
            alert_message = f"JSON file: {json_file}\n\nError in POST configuration."
        send_mail_alert(recipients, alert_message)