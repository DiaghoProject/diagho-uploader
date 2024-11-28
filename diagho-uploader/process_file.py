#!/usr/bin/python3

import json
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from functions import * 
from functions_diagho_api import *


# Récupérer les infos dans le fichier JSON files
def get_files_infos(json_input):
    """
    Extrait les informations à partir du fichier JSON.

    Args:
        json_input (str): Chemin vers un fichier JSON ou une chaîne JSON contenant les informations de fichier.

    Returns:
        dict: Dictionnaire contenant les informations de fichier, où chaque clé est un nom de fichier et chaque valeur est un dictionnaire
              contenant le checksum et une liste des identifiants de personnes associés.
    """
    try:
        # input_data = pd.read_json(json_input)
        with open(json_input, 'r') as json_file:
            input_data = json.load(json_file)
        
        # Récup des infos dans un dict
        dict_files = {}
        for file in input_data['files']:
            filename = file['filename']
            checksum = file['checksum']
            assembly = file['assembly']
            samples = file['samples']
            persons = []
            print(filename)
            for sample in samples:
                persons.append(sample["person"])
            dict_files[filename] = {
                "checksum" : checksum,
                "assembly" : assembly,
                "persons" : persons
            }
        # TODO #28 Warning s'il manque des infos 
        pretty_print_json_string(dict_files)
        return dict_files

    except ValueError as e:
        print(f"Erreur lors de la lecture du JSON: {e}")
        return {}

# Gère le traitement d'un biofile
def process_biofile_task(config, biofile, biofile_type, checksum_current_biofile, file, assembly, json_input, diagho_api):
    """Fonction qui gère le traitement d'un fichier bio (VCF ou BED)"""
    logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, biofile,f"Starting biofile processing: {biofile}"))
    process_biofile(config, biofile, biofile_type, checksum_current_biofile, file, assembly, json_input, diagho_api)       
    
# Création d'un message de logging plus clair
def log_message(json_file, biofile, message):
    if not biofile:
        return f"{json_file} - {message}"
    return f"{json_file} : {biofile} - {message}"

# Fonction principale : process JSON file
def diagho_process_file(file, config):
    """
    Process input file (JSON or TSV): load biofiles in Diagho + load input file.

    Args:
        file (str): input file (JSON or TSV).
        config (dict): Configuration.

    Returns:
        None
    """
    print(f"Processing file: {file}")
    
    # Mail when new file is detected
    recipients = config['emails']['recipients']
    content = f"Processing file: {file}"
    send_mail_info(recipients, content)
    
    # Create logfile
    json_input = os.path.basename(file)
    logging.info("------------------------------------------------------------")
    logging.getLogger("START_PROCESSING").info(log_message(json_input, "", "New file detected"))
    logging.getLogger("START_PROCESSING").info(log_message(json_input, "", f"Processing file: {file}"))
    
    # Load configuration
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Load configuration")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    recipients = config['emails']['recipients']
    path_biofiles = config['input_biofiles']
    get_biofile_max_retries = config['check_biofile']['max_retries']
    get_biofile_delay = config['check_biofile']['delay']
    
    # Load API endpoints
    url_diagho_api = config['diagho_api']['url']
    diagho_api = {
        'healthcheck': url_diagho_api + 'healthcheck',
        'login': url_diagho_api + 'auth/login/',
        'get_user': url_diagho_api + 'accounts/users/me',
        'get_biofile': url_diagho_api + 'bio_files/files',
        'post_biofile_snv': url_diagho_api + 'bio_files/files/snv/',
        'post_biofile_cnv': url_diagho_api + 'bio_files/files/cnv/',
        'loading_status': url_diagho_api + 'bio_files/files/',
        'config': url_diagho_api + 'configurations/configurations/'
    }
    
    # Check Diagho API
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("API healthcheck")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    if not diagho_api_healthcheck(diagho_api):
        logging.getLogger("API_HEALTHCHECK").error(log_message(json_input, "", f"Failed to connect to Diagho API. Exit."))
        return
        
    # API Login
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("API Login")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    diagho_api_login(config, diagho_api)
        
    # Test file format
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Test file format : TSV or JSON")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    if file.endswith('.tsv'):
        logging.getLogger("START_PROCESSING").info(log_message(json_input, "", f"TSV file detected. Parsing TSV to JSON for file: {file}"))
        # TODO: #10 Parser TSV en JSON
    elif file.endswith('.json'):
        logging.getLogger("START_PROCESSING").info(log_message(json_input, "", f"JSON file detected: {file}"))
    else:
        logging.getLogger("START_PROCESSING").info(log_message(json_input, "", f"Unsupported file format for file: {file}"))
        return
    
    # Check JSON format
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Test JSON file format")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    if not check_json_format(file):
        logging.getLogger("CHECK_FORMAT").error(log_message(json_input, "", f"Failed to process JSON input file: {file}"))
        return
    
    # Extract informations about biofiles from input_file
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Get biofiles informations")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    dict_biofiles = get_files_infos(file)
    
    # Foreach filename...
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Process each Biofile...")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    
    # Paralléliser le traitement des biofiles
    with ThreadPoolExecutor(max_workers=5) as executor:  # Utiliser 5 threads par exemple
        futures = []
        
        for filename, file_info in dict_biofiles.items():
            biofile = os.path.join(path_biofiles, filename)
            checksum = file_info["checksum"]
            assembly = file_info["assembly"]
            print(f"filename           : {filename}")
            print(f"Processing biofile : {biofile}")

            logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, filename, f"Processing biofile: {filename}"))

            # Attendre que le biofile soit présent
            attempt = 1
            while not os.path.exists(biofile) and attempt <= get_biofile_max_retries:
                logging.getLogger("PROCESSING_BIOFILE").warning(log_message(json_input, filename, f"Biofile {biofile} not found... attempt {attempt}"))
                time.sleep(get_biofile_delay)
                attempt += 1
            
            # Si le biofile n'existe pas : alerte   
            if not os.path.exists(biofile):
                logging.getLogger("PROCESSING_BIOFILE").error(log_message(json_input, filename, f"Biofile: {biofile} does not exist."))
                continue

            print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("Biofile found")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
            print(f"Biofile {biofile} found.")
            logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, filename, f"Biofile found: {biofile}"))
        
            # Calculate biofile checksum
            print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("Calculate biofile checksum")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
            checksum_current_biofile = md5(biofile)
            logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, filename, f"Calculated checksum: {checksum_current_biofile}"))
        
             # Créer une tâche pour chaque biofile
            if biofile.endswith('.vcf') or biofile.endswith('.vcf.gz'):
                print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print("Process VCF")
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
                biofile_type = "SNV"
                # process_biofile(config, biofile, biofile_type, checksum_current_biofile, filename)
                futures.append(executor.submit(process_biofile_task, config, biofile, biofile_type, checksum_current_biofile, filename, assembly, json_input, diagho_api))
            elif biofile.endswith('.bed'):
                print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print("Process BED")
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
                biofile_type = "CNV"
                ## TODO #18 Attente correction du endpoint pour import des BED
                # process_biofile(config, biofile, biofile_type, checksum_current_biofile, filename)
                futures.append(executor.submit(process_biofile_task, config, biofile, biofile_type, checksum_current_biofile, filename, assembly, json_input, diagho_api))
            else:
                logging.getLogger("PROCESSING_BIOFILE").error(log_message(json_input, filename, f"BIOFILE: wrong format for file: {biofile}."))
        
        # Attendre que toutes les tâches soient terminées
        for future in futures:
            future.result()
        
    logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, "", f"All biofiles have been loaded in Diagho"))
    
    # Upload JSON file  
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Upload JSON file")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    logging.getLogger("IMPORT_CONFIGURATIONS").info(log_message(json_input, "",f"Import JSON: {file}"))
    response = diagho_api_post_config(diagho_api['config'], file, config)
    
    check_api_response(response, config, json_input, recipients)
    
    
    
    
    


def process_biofile(config, biofile, biofile_type, biofile_checksum, filename, assembly, json_input,diagho_api):
    """
    Processus de traitement pour les fichiers VCF ou BED.

    Args:
    Returns:
    """
    print(f"\nStart function : process_biofile\n")
    logging.getLogger("PROCESSING_VCF").info(log_message(json_input, filename, f"Processing biofile: {biofile}"))
    
    # URLs
    url_diagho_api_post_biofile_snv = diagho_api['post_biofile_snv']
    url_diagho_api_post_biofile_cnv = diagho_api['post_biofile_cnv']
    url_diagho_api_loading_status = diagho_api['loading_status']
    
    # Get accession_id
    accession_id = config['accessions'][assembly]
    
    
    # Post du biofile + récupérer le chekcsum
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("POST Biofile")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    
    if biofile_type == "SNV":
        checksum_from_api = diagho_api_post_biofile(url_diagho_api_post_biofile_snv, biofile, biofile_type, accession_id, config, diagho_api, biofile_checksum).get('checksum')
        logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, filename, f"VCF file"))
        logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, filename, f"Checksum from API: {checksum_from_api}"))
    
    if biofile_type == "CNV":
        checksum_from_api = diagho_api_post_biofile(url_diagho_api_post_biofile_cnv, biofile, biofile_type, assembly, config, diagho_api, biofile_checksum).get('checksum')
        logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, filename, f"BED file"))
        logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, filename, f"Checksum from API: {checksum_from_api}"))
        
    # Si l'upload ne fonctionne pas : alerte
    if not checksum_from_api or checksum_from_api is None:
        logging.getLogger("PROCESSING_BIOFILE").error(log_message(json_input, filename, f"Failed to upload biofile and obtain checksum from API."))
        return

    # Vérification du checksum du fichier uploadé avec le checksum calculé avant
    if not check_md5sum(checksum_from_api, biofile_checksum):
        logging.getLogger("PROCESSING_BIOFILE").error(log_message(json_input, filename, f"MD5 checksum mismatch."))
        return
    
    # if check_md5sum(checksum_from_api, checksum_current_biofile):
    logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, filename, f"Checksums are identical. Continue."))
        
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Check Loading Status")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    
    time.sleep(120)
    
    max_retries = config['check_loading']['max_retries']
    delay = config['check_loading']['delay']
    attempt = 0
    loading_status = check_loading_status(config, url_diagho_api_loading_status, biofile_checksum, filename, max_retries, delay, attempt, json_input)
    
    if loading_status == 0:
        logging.getLogger("PROCESSING_BIOFILE").error(log_message(json_input, filename, f"Check loading status: {loading_status}"))
    else:
        logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, filename, f"Check loading status: {loading_status}"))
    
    if loading_status:
        logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, filename, f"Loading Status = SUCCESS"))
        time.sleep(10)
        
        # Move biofile in backup folder
        source_path = biofile
        backup_path = config.get("backup_biofiles")
        destination_path = os.path.join(backup_path, filename)
        # Déplacer le fichier
        shutil.move(source_path, destination_path)
        logging.getLogger("PROCESSING_BIOFILE").warning(log_message(json_input, filename, f"Move biofile to {backup_path}"))
    else:
        logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, filename, f"Loading Status = FAIL"))




# Check loading status
def check_loading_status(config, url, checksum, filename, max_retries, delay, attempt, json_input):
    """
    Vérification du statut de chargement.

    Arguments:
        checksum: le checksum du fichier à vérifier.
        max_retries: nombre de tentatives max.
        delay: délai (en secondes) entre chaque tentative.
        attempt: compteur de tentatives actuelles.
        config: fichierd e conf

    Returns:
        True : si le fichier est chargé (status 3)
        False : si échec de chargement (status 0)
        None : en cas de dépassement du nombre de tentatives ou statut inconnu
    """
    # Get loading status :
    status = diagho_api_get_loadingstatus(url, checksum, config).get('loading')
    logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, filename, f"Loading initial status: {status}"))
    
    while status not in [0, 3]:
        logging.getLogger("PROCESSING_BIOFILE").warning(log_message(json_input, filename, f'Attempt {attempt + 1}: loading_status = {status} ... Retry...'))
        time.sleep(delay)
        
        # Récupérer à nouveau le statut de chargement
        status = diagho_api_get_loadingstatus(url, checksum, config).get('loading')
        
        # Incrémenter le compteur de tentatives
        attempt += 1
        
        # Vérifier si le nombre maximal de tentatives est atteint
        if attempt >= max_retries:
            logging.getLogger("PROCESSING_BIOFILE").error(log_message(json_input, filename, f"GET_LOADING_STATUS: Maximum number of attempts reached."))
            return None
        
    # Vérification des statuts finaux
    if status == 0:
        
        # Try again before really failed
        new_attempt = 0
        max_new_attempts = 100
        while new_attempt <= max_new_attempts and status not in [0, 3]:
            status = diagho_api_get_loadingstatus(url, checksum, config).get('loading')
            time.sleep(60)
            new_attempt += 1
            
        if status == 0:      
            return False
        elif status == 3:
            return True
        else:
            return None
        
    elif status == 3:
        logging.getLogger("PROCESSING_BIOFILE").info(log_message(json_input, filename, f"Loading completed successfully."))
        return True
    else:
        logging.getLogger("PROCESSING_BIOFILE").error(log_message(json_input, filename, f"Unknown status: {status}. Exit."))
        return None
