#!/usr/bin/python3

import json
import pandas as pd
import os
import time

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
        input_data = pd.read_json(json_input)
        
        # Récup des infos dans un dict
        dict_files = {}
        for file in input_data['files']:
            filename = file['filename']
            checksum = file['checksum']
            samples = file['samples']
            persons = []
            for sample in samples:
                persons.append(sample["person"])
            dict_files[filename] = {
                "checksum" : checksum,
                "persons" : persons
            }
        return dict_files

    except ValueError as e:
        print(f"Erreur lors de la lecture du JSON: {e}")
        return {}
       

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
    
    # Create logfile
    setup_logger()
    logging.getLogger("START_PROCESSING").info(f"New file detected.")
    logging.getLogger("START_PROCESSING").info(f"Processing file: {file}")
    
    # Load configuration and URLs
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Load configuration")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    recipients = config['emails']['recipients']
    path_biofiles = config['input_biofiles']
    get_biofile_max_retries = config['check_biofile']['max_retries']
    get_biofile_delay = config['check_biofile']['delay']
    
    # Check Diagho API
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("API healthcheck")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    if not diagho_api_healthcheck(config):
        logging.getLogger("API_HEALTHCHECK").error(f"Failed to connect to Diagho API. Exit.")
        return
        
    # API Login
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("API Login")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    diagho_api_login(config)
    
    # Get access tocken
    access_token = get_access_token(config)
    print(f"Access token: {access_token}")
    
    # Process input file
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Test file format : TSV or JSON")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    if file.endswith('.tsv'):
        logging.getLogger("START_PROCESSING").info(f"TSV file detected. Parsing TSV to JSON for file: {file}")
        # TODO: #10 Parser TSV en JSON
    elif file.endswith('.json'):
        logging.getLogger("START_PROCESSING").info(f"JSON file detected: {file}")
    else:
        logging.getLogger("START_PROCESSING").info(f"Unsupported file format for file: {file}")
        return
    
    # Check JSON format
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Test JSON file format")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    if not check_json_format(file):
        content = "Failed to process JSON input file."
        logging.getLogger("CHECK_FORMAT").error(content)
        send_mail_alert(recipients, content)
        return
    
    # Extract informations about biodiles from input_file
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Get biodiles informations")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    dict_biofiles = get_files_infos(file)
    
    # Foreach filename...
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Foreach Biofile...")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    for filename, file_info in dict_biofiles.items():
        biofile = os.path.join(path_biofiles, filename)
        checksum = file_info["checksum"]
        persons = file_info["persons"]
        
        print(f"filename           : {filename}")
        print(f"Processing biofile : {biofile}")
        print(f"Persons            : {persons}")

        logging.getLogger("PROCESSING_BIOFILE").info(f"Processing biofile: {biofile}")

        # Tant que le biofile n'existe pas...
        # On boucle toutes les X secondes pendant un certain nombre de fois max
        attempt = 1
        while not os.path.exists(biofile) and attempt <= get_biofile_max_retries:
            logging.getLogger("PROCESSING_BIOFILE").warning(f"Biofile {biofile} not found... attempt {attempt}")
            time.sleep(get_biofile_delay)
            attempt += 1
        
        # Si le biofile n'existe pas : alerte   
        if not os.path.exists(biofile):
            logging.getLogger("PROCESSING_BIOFILE").error(f"Biofile: {biofile} does not exist.")
            continue

        print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("Biofile found")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        print(f"Biofile {biofile} found.")
        logging.getLogger("PROCESSING_BIOFILE").info(f"Biofile found: {biofile}")
        
        # Calculate biofile checksum
        print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("Calculate biofile checksum")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        checksum_current_biofile = md5(biofile)
        
        print(f"Checksum : {checksum_current_biofile}")
        logging.getLogger("PROCESSING_BIOFILE").info(f"Calculated checksum: {checksum_current_biofile}")
        
        # Si c'est un VCF :
        if biofile.endswith('.vcf') or biofile.endswith('.vcf.gz'):
            print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("Process VCF")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
            biofile_type = "SNV"
            process_biofile(config, biofile, biofile_type, checksum_current_biofile, file)
            
        # Si c'est un BED :
        elif biofile.endswith('.bed'):
            print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("Process BED")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
            process_bed_file(biofile, checksum_current_biofile, config, recipients, file, persons)
            
        else:
            content = f"BIOFILE: wrong format for file: {biofile}."
            send_mail_alert(recipients, content)

    logging.getLogger("PROCESSING_BIOFILE").info(f"All biofiles have been loaded in Diagho")
    
    # Upload JSON file  
    file_to_import = file
    print("import file config: ", file_to_import)
    logging.getLogger("IMPORT_CONFIGURATIONS").info(f"Import JSON: {file}")
    # diagho_api_post_config(config['diagho_api']['config'], file_to_import, config)



def process_biofile(config, biofile, biofile_type, biofile_checksum, json_file):
    """
    Processus de traitement pour les fichiers VCF ou BED.

    Args:
    Returns:
    """
    print(f"\nStart function : process_vcf\n")
    logging.getLogger("PROCESSING_VCF").info(f"Processing VCF biofile: {biofile}")
    
    url_diagho_api_post_biofile_snv = config['diagho_api']['post_biofile_snv']
    url_diagho_api_post_biofile_cnv = config['diagho_api']['post_biofile_cnv']
    url_diagho_api_loading_status = config['diagho_api']['loading_status']
    accession_id = config['accessions']['vcf']
    assembly = config['assembly']['bed']
    
    # Post du biofile + récupérer le chekcsum
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("POST Biofile")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    
    if biofile_type == "SNV":
        checksum_from_api = diagho_api_post_biofile(url_diagho_api_post_biofile_snv, biofile, biofile_type, accession_id, config).get('checksum')
        print(f"Checksum renvoyé par l'API : {checksum_from_api}")
        logging.getLogger("PROCESSING_BIOFILE").info(f"VCF file")
        logging.getLogger("PROCESSING_BIOFILE").info(f"Checksum from API: {checksum_from_api}")
    
    if biofile_type == "CNV":
        checksum_from_api = diagho_api_post_biofile(url_diagho_api_post_biofile_cnv, biofile, biofile_type, assembly, config).get('checksum')
        print(f"Checksum renvoyé par l'API : {checksum_from_api}")
        logging.getLogger("PROCESSING_BIOFILE").info(f"BED file")
        logging.getLogger("PROCESSING_BIOFILE").info(f"Checksum from API: {checksum_from_api}")
        
    # Si l'upload ne fonctionne pas : alerte
    if not checksum_from_api or checksum_from_api is None:
        logging.getLogger("PROCESSING_BIOFILE").error("Failed to upload biofile and obtain checksum from API.")
        return

    # Vérification du checksum du fichier uploadé avec le checksum calculé avant
    if not check_md5sum(checksum_from_api, biofile_checksum):
        logging.getLogger("PROCESSING_BIOFILE").error("MD5 checksum mismatch.")
        return
    
    # if check_md5sum(checksum_from_api, checksum_current_biofile):
    logging.getLogger("PROCESSING_VCF").info(f"Checksums are identical. Continue.")
        
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Check Loading Status")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    
    max_retries = config['check_loading']['max_retries']
    delay = config['check_loading']['delay']
    loading_status = check_loading_status(config, url_diagho_api_loading_status, biofile_checksum, max_retries, delay)
    
    logging.getLogger("PROCESSING_BIOFILE").info(f"Check loading status: {loading_status}")
    
    if loading_status:
        logging.getLogger("PROCESSING_BIOFILE").info(f"Loading Status = SUCCESS")
        time.sleep(10)
    else:
        logging.getLogger("PROCESSING_BIOFILE").info(f"Loading Status = FAIL")




# Check loading status
def check_loading_status(config, url, checksum, max_retries, delay, attempt=0):
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
    logging.getLogger("PROCESSING_BIOFILE").info(f"Loading initial status: {status}")
    
    while status not in [0, 3]:
        print(f"\nTentative {attempt + 1}: Statut de chargement = {status}")
        logging.getLogger("PROCESSING_BIOFILE").warning(f'Attempt {attempt + 1}: loading_status = {status} ... Retry...')

        time.sleep(delay)
        
        # Récupérer à nouveau le statut de chargement
        status = diagho_api_get_loadingstatus(url, checksum, config).get('loading')
        
        # Incrémenter le compteur de tentatives
        attempt += 1
        
        # Vérifier si le nombre maximal de tentatives est atteint
        if attempt >= max_retries:
            print("Nombre maximal de tentatives atteint. Abandon.")
            logging.getLogger("PROCESSING_BIOFILE").error('GET_LOADING_STATUS: Maximum number of attempts reached.')
            return None
        
    # Vérification des statuts finaux
    if status == 0:
        return False
    elif status == 3:
        logging.getLogger("PROCESSING_BIOFILE").info('Loading completed successfully.')
        return True
    else:
        logging.getLogger("PROCESSING_BIOFILE").error(f"Unknown status: {status}. Exit.")
        return None
