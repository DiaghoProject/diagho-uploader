import hashlib
import inspect
import json
import os
import time

from utils.logger import *
from diagho_uploader.api_handler import api_get_loadingstatus


def get_biofile_informations(data, filename):
    """
    Search the dictionary containing the 'filename' in the list of dictionaries (data), and returns this dictionnary.
    """
    return next((item for item in data if item.get("filename") == filename), None)


def wait_for_biofile(biofile, max_retries=100, delay=10):
    """
    Waits for the biofile to exist, with a limited number of attempts.
    """
    function_name = inspect.currentframe().f_code.co_name
    biofile_filename = os.path.basename(biofile)

    if os.path.exists(biofile):
        log_biofile_message(function_name, "INFO", biofile_filename, "Biofile found. Continue.")
        return True
    
    for attempt in range(1, max_retries + 1):
        if os.path.exists(biofile):
            log_biofile_message(function_name, "INFO", biofile_filename, f"Biofile found. Continue.")
            return True
        log_biofile_message(function_name, "WARNING", biofile_filename, f"Biofile not found... attempt {attempt}")
        time.sleep(delay)
        
    log_biofile_message(function_name, "ERROR", biofile_filename, f"Biofile not found after {max_retries} attempt. Exit.")
    return False  # Échec après toutes les tentatives


def get_biofile_type(biofile):
    """
    Returns biofile type: SNV or CNV. Required for API endpoints.

    Args:
        biofile (str): biofile.

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
    Check the loadinfg status.

    Returns:
        True : file is loaded (status 3)
        False : loading failed (status 0)
        None : if number of attempts exceeded or status unknown
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
    log_biofile_message(function_name, "DEBUG", biofile_filename, f"Loading initial status: {status}")

    # Plusieurs tentatives... Tant que le statut n'est pas 0 ou 3 (FAILURE ou SUCCESS)
    while status not in [0, 3] and attempt < max_retries:
        log_biofile_message(function_name, "INFO", biofile_filename, f"Attempt {attempt + 1}: loading_status = {status} ... Retry...")
        time.sleep(delay)
        status = get_status()
        attempt += 1
    
    # Si trop de tentatives, retourner None
    if attempt >= max_retries:
        log_biofile_message(function_name, "ERROR", biofile_filename, f"Maximum number of attempts reached.")
        return None

    # Vérifier les statuts finaux
    if status == 3: # SUCCESS
        log_biofile_message(function_name, "INFO", biofile_filename, f"Loading completed successfully.")
        return True
    elif status == 0: # FAILURE
        log_biofile_message(function_name, "ERROR", biofile_filename, f"Loading failed.")
        return False
    else:
        log_biofile_message(function_name, "ERROR", biofile_filename, f"Unknown status: {status}. Exit.")
        return None


def pretty_print_json_string(string):
    """
    Pretty print a JSON string.
    Used for debug.

    Arguments:
        json_str (str): The JSON string to be pretty printed.
    """
    try:
        json_string = json.dumps(string)
        json_dict = json.loads(json_string)
        print(json.dumps(json_dict, indent = 1))
    except json.JSONDecodeError as e:
        print(f"Invalid JSON string: {e}")
     