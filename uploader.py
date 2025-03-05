import shutil
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from datetime import datetime

from tabulated2json import create_json_files
from utils.api import *
from utils.file import *
from utils.config_loader import *
from utils.mail import *
from utils.logger import *


def diagho_upload_file(**kwargs): # pragma: no cover
    """
    Process input file (JSON) : load biofiles in Diagho and load JSON file.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    # Args
    config = kwargs.get("config")
    config_file = kwargs.get("config_file")
    file_path = kwargs.get("file_path")   
    
    log_message(function_name, "DEBUG", f"START UPLOADER : Input file: {file_path}")

    # Load settings
    settings = load_configuration(config)
    path_biofiles = settings["path_biofiles"]
    recipients = settings["recipients"]
    
    # Get API endpoints
    diagho_api = get_api_endpoints(config)
    
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
    
    # Si le fichier d'input est un fichier tabulé : créer le JSON
    if file_path.endswith((".tsv", ".csv", ".txt")):
        log_message(function_name, "INFO", f"Process tabulated file to create JSON.")
        
        # Répertoire pour traitement 'create_json'
        output_directory = os.path.join(os.path.dirname(file_path), "tsv2json")
        os.makedirs(output_directory, exist_ok=True)
        
        # Fichier JSON à créer
        output_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}.json"
        output_file = os.path.join(output_directory, output_filename)
        output_prefix = os.path.splitext(os.path.basename(file_path))[0]
        try:
            create_json_files(file_path, output_file, diagho_api, output_prefix)
        except Exception as e:
            message = f"{e}"
            log_message(function_name, "ERROR", f"Erreur détectée: {e}.")
            send_mail_alert(recipients, message)
            return
        
        # Valider que le JSON est bien écrit
        if not os.path.exists(output_file):
            log_message(function_name, "ERROR", f"JSON file not found: {output_file}")
            raise FileNotFoundError(f"File not found: {output_file}.")
        
        log_message(function_name, "DEBUG", f"File: {file_path} --> {output_file}")
        
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
    
    # # Check Diagho API
    # try:
    #     api_healthcheck(diagho_api)
    # except ValueError as e:
    #     send_mail_alert(recipients, f"API healthcheck error : {e}")
    #     return
    
    # # API login
    # try:
    #     result = api_login(config, diagho_api)
    #     if result.get("error"):
    #         error_message = result.get("error")
    #         send_mail_alert(recipients, f"API login error: {error_message} ")
    #         return
    # except ValueError as e:
    #     send_mail_alert(recipients, f"API login error: {e}")
    #     return
    
    
    # Traitements parallèles :
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        
        # Get filenames of the biofiles
        biofiles = json_data["files"]
        filenames = [item.get("filename") for item in biofiles if "filename" in item]
        log_message(function_name, "DEBUG", f"{os.path.basename(json_file)} - Process each biofile: {filenames}")
        
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
    log_message("PROCESS_BIOFILE", "INFO", f"All biofiles have been loaded in Diagho: {filenames}")

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
def process_biofile_task(settings, biofile, biofile_infos, diagho_api): # pragma: no cover
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
    log_biofile_message(function_name, "DEBUG", biofile_filename, f"Start processing biofile.")
        
    # Récupérer les settings
    path_biofiles = settings["path_biofiles"]
    max_retries = settings["get_biofile_max_retries"]
    delay = settings["get_biofile_delay"]
    recipients = settings["recipients"]   
    
    # Récupération du biofile (si pas présent au bout de X tentatives... alerte et stop process)
    if not wait_for_biofile(biofile, max_retries, delay):
        send_mail_alert(recipients, f"Failed to process biofile '{biofile_filename}'.\n\nBiofile '{biofile_filename}' does not exist in: {path_biofiles}.")
        log_biofile_message(function_name, "ERROR", biofile_filename, f"Biofile does not exist in: {path_biofiles}")
        return False
    
    # Biofile found
    log_biofile_message(function_name, "DEBUG", biofile_filename, f"Biofile found. Continue.")
        
    # Get informations about biofile
    try:
        biofile_type = get_biofile_type(biofile)    # TODO: REVOIR CETTE PARTIE: commenta voir le biofile_type ??
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
    log_biofile_message(function_name, "DEBUG", biofile_filename, f"Checksums are identical. Continue.")
        
    # check le statut de chargement
    # TODO: à tester avec la 0.4.0 et remove
    time.sleep(20) # nécessaire pour l'instant car bug initial (statut en FAILURE)
    
    attempt = 1
    loading_status = check_loading_status(attempt, **kwargs)
    
    # Envoi d'un mail si le biofile n'est pas chargé correctement
    if loading_status: # enlever ça plus tard, garder juste le cas d'erreur
        send_mail_info(recipients, f"Biofile has been loaded successfully in Diagho.\n\nBiofile: {biofile_filename}")
    if not loading_status:
        send_mail_alert(recipients, f"Failed to load biofile in Diagho.\n\nBiofile: {biofile_filename}")
    
    # Move biofile in backup folder
    backup_path = settings.get("path_backup_biofiles")
    destination_path = os.path.join(backup_path, biofile_filename)
    shutil.move(biofile, destination_path)
    log_biofile_message(function_name, "DEBUG", biofile_filename, f"Move biofile to {backup_path}.")
    
    return True


