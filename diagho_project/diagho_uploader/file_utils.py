import hashlib
import inspect
import json
import os
import time

from common.log_utils import *
from diagho_uploader.api_handler import api_get_loadingstatus


def validate_json_input(json_input):
    """
    Valide la structure du fichier JSON.
    """
    function_name = inspect.currentframe().f_code.co_name
    json_filename = os.path.basename(json_input)
    try:
        with open(json_input, 'r') as json_file:
            input_data = json.load(json_file)

        if "families" not in input_data:
            log_message(function_name, "ERROR", f"{os.path.basename(json_filename)}- Le fichier JSON doit contenir une clé 'families'.")
            raise ValueError("Le fichier JSON doit contenir une clé 'families'.")
        if "files" not in input_data:
            log_message(function_name, "ERROR", f"{os.path.basename(json_filename)}- Le fichier JSON doit contenir une clé 'files'.")
            raise ValueError("Le fichier JSON doit contenir une clé 'files'.")
        if "interpretations" not in input_data:
            log_message(function_name, "ERROR", f"{os.path.basename(json_filename)}- Le fichier JSON doit contenir une clé 'interpretations'.")
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



def get_biofile_informations(data, filename):
    """
    Recherche dans la liste de dictionnaires le dictionnaire contenant le 'filename'.
    """
    return next((item for item in data if item.get("filename") == filename), None)




def wait_for_biofile(biofile, max_retries=100, delay=10):
    """
    Attend l'existence du biofile avec un nombre de tentatives limité.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    biofile_filename = os.path.basename(biofile)
    for attempt in range(1, max_retries + 1):
        if os.path.exists(biofile):
            log_biofile_message(function_name, "SUCCESS", biofile_filename, f"Biofile found. Continue.")
            return True
        log_biofile_message(function_name, "WARNING", biofile_filename, f"Biofile not found... attempt {attempt}")
        time.sleep(delay)
    log_biofile_message(function_name, "ERROR", biofile_filename, f"Biofile not found after {attempt} attempt. Exit.")
    return False  # Échec après toutes les tentatives





def get_biofile_type(biofile):
    """
    Retourne le type de biofile : SNV ou CNV. Nécessaire pour les endpoints de l'API.

    Args:
        biofile (str): fichier à traiter.

    Returns:
        str: 'SNV' ou 'CNV'
    """
    if biofile.endswith('.vcf') or biofile.endswith('.vcf.gz'):
        return 'SNV'
    elif biofile.endswith('.bed') or biofile.endswith('.tsv'):
        return 'CNV'
    else:
        error_message = f"Unsupported biofile type for file: {biofile}"
        raise ValueError(error_message)
    
    
def md5(filepath):
    """
    Computes the MD5 hash of a file.
    """
    function_name = inspect.currentframe().f_code.co_name
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
    
    log_message(function_name, "ERROR", error_msg)
    return {"error": error_msg}



 
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
    function_name = inspect.currentframe().f_code.co_name
    
    settings = kwargs.get("settings")
    biofile_filename = kwargs.get("biofile_filename")
    
    max_retries = settings["check_loading_max_retries"]
    delay = settings["check_loading_delay"]
    
    def get_status():
        return api_get_loadingstatus(**kwargs).get('loading')

    # Obtenir le statut de chargement initial
    status = get_status()
    log_biofile_info(function_name, biofile_filename, f"Loading initial status: {status}")

    # Plusieurs tentatives... Tant que le statut n'est pas 0 ou 3 (FAILURE ou SUCCESS)
    while status not in [0, 3] and attempt < max_retries:
        log_biofile_message(function_name, "WARNING", biofile_filename, f"Attempt {attempt + 1}: loading_status = {status} ... Retry...")
        time.sleep(delay)
        status = get_status()
        attempt += 1
    
    # Si trop de tentatives, retourner None
    if attempt >= max_retries:
        log_biofile_message(function_name, "ERROR", biofile_filename, f"Maximum number of attempts reached.")
        return None

    # Vérifier les statuts finaux
    if status == 3: # SUCCESS
        log_biofile_message(function_name, "SUCCESS", biofile_filename, f"Loading completed successfully.")
        return True
    elif status == 0: # FAILURE
        log_biofile_message(function_name, "ERROR", biofile_filename, f"Loading failed.")
        return False
    else:
        log_biofile_message(function_name, "ERROR", biofile_filename, f"Unknown status: {status}. Exit.")
        return None

