import hashlib
import json
import shutil
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from datetime import datetime

from diagho_create_inputs.parser import create_json_files

from diagho_uploader.api_handler import *
from diagho_uploader.file_utils import *

from common.config_loader import *
from common.file_utils import *
from common.mail_utils import *
from common.api_utils import *
from common.log_utils import *


def diagho_upload_file(**kwargs):
    """
    Process input file (JSON) : load biofiles in Diagho and load JSON file.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    # Args
    config = kwargs.get("config")
    config_file = kwargs.get("config_file")
    file_path = kwargs.get("file_path")   
    
    log_message(function_name, "INFO", f"START UPLOADER : Input file: {file_path}")

    # Load settings
    settings = load_configuration(config)
    path_biofiles = settings["path_biofiles"]
    recipients = settings["recipients"]
    
    # Get API endpoints
    diagho_api = get_api_endpoints(config)
    
    # Si fichier d'input en TSV : créer le JSON
    if file_path.endswith(".tsv"):
        log_message(function_name, "INFO", f"Input file = TSV ... Need to create JSON file.")
        
        # Répertoire pour traitement 'create_json'
        output_directory = os.path.join(os.path.dirname(file_path), "tsv2json")
        os.makedirs(output_directory, exist_ok=True)
        
        # Fichier JSON à créer
        output_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}.json"
        output_file = os.path.join(output_directory, output_filename)
        output_prefix = os.path.splitext(os.path.basename(file_path))[0]
        try:
            create_json_files(file_path, output_file, output_prefix)
        except Exception as e:
            log_message(function_name, "ERROR", f"Erreur détectée: {e}.")
            return
        
        # Valider que le JSON est bien écrit
        if not os.path.exists(output_file):
            log_message(function_name, "ERROR", f"JSON file not found: {output_file}")
            raise FileNotFoundError(f"File not found: {output_file}.")
        
        log_message(function_name, "SUCCESS", f"File: {file_path} --> {output_file}")
        
        # Redéfinir les inputs pour la suite
        # file_path = output_file
        json_file = output_file
        time.sleep(2)
        
    if file_path.endswith(".json"):
        json_file = file_path
    
    json_filename = os.path.basename(json_file)
    
    # Test si fichier JSON OK
    try:
        json_data = validate_json_input(json_file)
    except ValueError as e:
        send_mail_alert(recipients, f"Erreur de validation du fichier JSON: {json_filename}\n\n{e}")
        return
        
    
    # Check Diagho API
    try:
        api_healthcheck(diagho_api)
    except ValueError as e:
        send_mail_alert(recipients, f"API healthcheck error : {e}")
        return
    
    # API login
    try:
        result = api_login(config, diagho_api)
        if result.get("error"):
            error_message = result.get("error")
            send_mail_alert(recipients, f"API login error: {error_message} ")
            return
    except ValueError as e:
        send_mail_alert(recipients, f"API login error: {e}")
        return
    
    
    # Traitements parallèles :
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        
        # Get filenames of the biofiles
        biofiles = json_data["files"]
        filenames = [item.get("filename") for item in biofiles if "filename" in item]
        log_message(function_name, "INFO", f"{os.path.basename(json_file)} - Process each biofile: {filenames}")
        
        # for each biofile...
        for filename in filenames:
            # Get absolute path
            biofile = os.path.join(path_biofiles, filename)            
            biofile_infos = get_biofile_informations(biofiles, filename)
                        
            # A partir d'ici : paraléliser les traitements
            futures.append(executor.submit(process_biofile_task, settings, biofile, biofile_infos, diagho_api))

        # Attendre que toutes les tâches soient terminées avec succès
        for future in concurrent.futures.as_completed(futures):
            if not future.result():  # Si une tâche a échoué : log + sortir du traitement
                time.sleep(5)
                log_message("PROCESS_BIOFILE", "ERROR", f"FAILED: one task failed, processing stopped. Exit.")
                return
            
    # Tous les biofiles ont été traités.     
    log_message("PROCESS_BIOFILE", "SUCCESS", f"All biofiles have been loaded in Diagho: {filenames}")

    time.sleep(5)
    
    # Upload JSON file 
    log_message("UPLOAD_JSON", "INFO", f"Upload JSON: {os.path.basename(json_file)}") 
    kwargs = {
        'diagho_api': diagho_api,
        'file': json_file,
        'recipients': recipients,
        'json_file': os.path.basename(json_file)
    }
    response = api_post_config(**kwargs)

    # Vérifie si import du JSON OK    
    check_api_response(response, **kwargs)
    


# Gère le traitement d'un biofile
def process_biofile_task(settings, biofile, biofile_infos, diagho_api):
    """
    Traitement d'un fichier bio (VCF ou BED).

    Args:
        settings (dict): paramétrages.
        biofile (str): fichier VCF ou BED à traiter.
        biofile_infos (dict): informations sur le biofile à traiter.
        diagho_api (dict): endpoints.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    biofile_filename = os.path.basename(biofile)
    log_biofile_message(function_name, "INFO", biofile_filename, f"Start processing biofile.")
        
    # Récupérer les settings
    path_biofiles = settings["path_biofiles"]
    max_retries = settings["get_biofile_max_retries"]
    delay = settings["get_biofile_delay"]
    recipients = settings["recipients"]   
    
    # Récupération du biofile (si pas présent au bout de X tentatives... alerte et stop process)
    if not wait_for_biofile(biofile, max_retries, delay):
        content = f"Failed to process biofile '{biofile_filename}'.\n\nBiofile '{biofile_filename}' does not exist in: {path_biofiles}."
        send_mail_alert(recipients, content)
        log_biofile_message(function_name, "ERROR", biofile_filename, f"Biofile does not exist in: {path_biofiles}")
        return False
    
    # Biofile found
    log_biofile_message(function_name, "INFO", biofile_filename, f"Biofile found. Continue.")
        
    # Get informations about biofile
    try:
        biofile_type = get_biofile_type(biofile)    # REVOIR CETTE PARTIE: commenta voir le biofile_type ??
        assembly = biofile_infos["assembly"]
        accession_id = settings["accessions"][assembly]
    except ValueError as e:
        log_biofile_message(function_name, "ERROR", biofile_filename, f"{e}")
        send_mail_alert(settings["recipients"], f"{str(e)}")
        return False
        
    
    # Verifier le checksum du JSON et celui calculé du biofile
    md5_biofile = md5(biofile)
    md5_from_json = biofile_infos.get("checksum")
    if not check_md5sum(md5_biofile, md5_from_json):
        log_biofile_message(function_name, "ERROR", biofile_filename, f"MD5 checksum mismatch for biofile: {biofile_filename}.")
        return False
    
    # Si checksum identiques : POST biofile
    kwargs = {
        "settings": settings,
        "biofile": biofile,
        "biofile_filename": biofile_filename,
        "diagho_api": diagho_api,
        "biofile_type": biofile_type,
        "assembly": assembly,
        "accession_id": accession_id,
        "checksum": md5_biofile
    }
    checksum = api_post_biofile(**kwargs).get("checksum")
    
    # Vérifier que le checksum du biofile posté est le même que celui du biofile
    if not check_md5sum(checksum, md5_biofile):
        log_biofile_message(function_name, "ERROR", biofile_filename, f"MD5 checksum mismatch for biofile: {biofile_filename}")
        return False
    log_biofile_message(function_name, "INFO", biofile_filename, f"Checksums are identical. Continue.")
        
    # check le statut de chargement
    time.sleep(20) # nécessaire pour l'instant car bug initial (statut en FAILURE)
    
    attempt = 1
    loading_status = check_loading_status(attempt, **kwargs)
    
    # Envoi d'un mail si le biofile n'est pas chargé correctement
    if loading_status: # enlever ça plus tard, garder juste le cas d'erreur
        content = f"Biofile has been loaded successfully in Diagho.\n\nBiofile: {biofile_filename}"
        send_mail_info(recipients, content)
    if not loading_status:
        content = f"Failed to load biofile in Diagho.\n\nBiofile: {biofile_filename}"
        send_mail_alert(recipients, content)
    
    # Move biofile in backup folder
    backup_path = settings.get("path_backup_biofiles")
    destination_path = os.path.join(backup_path, biofile_filename)
    shutil.move(biofile, destination_path)
    log_biofile_message(function_name, "INFO", biofile_filename, f"Move biofile to {backup_path}.")
    
    return True
        
    



   
def check_api_response(response, **kwargs):
    """
    Vérifie la réponse de l'API après le POST de la config et envoie des notifications en fonction du statut.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    recipients = kwargs.get('recipients')
    json_file = kwargs.get('json_file')
    
    log_message(function_name, "INFO", f"response.status_code = {response.status_code}")

    # Si OK
    if response.status_code == 201:
        log_message(function_name, "SUCCESS", f"{os.path.basename(json_file)}: configuration file was posted in Diagho successfully")
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
        log_message(function_name, "ERROR", f"{os.path.basename(json_file)}: error in POST configuration")
        log_message(function_name, "ERROR", f"{json_response}")