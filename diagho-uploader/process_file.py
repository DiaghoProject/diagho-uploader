#!/usr/bin/python3

import json
import pandas as pd
import os
import multiprocessing

import time


from functions import * 
from functions_diagho_api import *

import logging
logging.basicConfig(
    level=logging.INFO,                     # Définir le niveau de log minimum
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # Format du message
    handlers=[
        logging.FileHandler('app.log'),     # Enregistrer les logs dans un fichier
        logging.StreamHandler()             # Afficher les logs sur la console
    ]
)

# Cherche le fichier JSON (famille ou interprétations) correspondant au fichier JSON files en cours
def find_json_file(directory, search_value=None, file_type=None):
    """
    Cherche un fichier JSON dans le répertoire spécifié en fonction du type de fichier et le valeur à chercher.

    Args:
        directory (str): Le répertoire où chercher les fichiers.
        search_value (str): Valeur à rechercher (checksum ou personnes de la famille).
        file_type (str): Type de fichier à rechercher ("family" ou "interpretation").

    Returns:
        str: Le chemin du fichier trouvé, ou un message d'erreur si aucun fichier n'est trouvé.
    """
    if not os.path.isdir(directory):
        raise ValueError(f"Le répertoire spécifié '{directory}' n'existe pas ou n'est pas un répertoire valide.")
    
    if file_type not in ["family", "interpretation"]:
        return "Type de fichier non supporté. Utilisez 'family' ou 'interpretation'."
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        if not filename.endswith(f'.{file_type}.json'):
            continue
        
        # Lecture du fichier JSON
        try:
            print("fichier à tester:", file_path)
            with open(file_path, 'r') as file:
                data = json.load(file)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Erreur lors de la lecture de {filename}: {e}")
            continue
        
        # Si family
        if file_type == "family":
            if not search_value:
                return "Les personnes doivent être fournies."
            
            families = data.get("families", [])
            if not families:
                continue
            
            for person in families[0].get('persons', []):
                print("person:", person.get("identifier"))
                if person.get("identifier") in search_value:
                    print("Family file found:", filename)
                    return file_path
                
        # Si interpretations
        elif file_type == "interpretation":
            interpretations = data.get("interpretations", [])
            if not interpretations:
                continue
            
            for data_samples in interpretations[0].get('datas', []):
                for sample in data_samples.get("samples", []):
                    if sample.get("checksum") == search_value:
                        print("Interpretations file found:", filename)
                        return file_path
        else:            
            return "Aucun fichier correspondant trouvé."


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
    
    
def process_biofile(config, biofile):
    recipients = config['emails']['recipients']
    get_biofile_max_retries = config['check_biofile']['max_retries']
    get_biofile_delay = config['check_biofile']['delay']
    
    # Tant que le biofile n'existe pas...
    # On boucle toutes les X secondes pendant un certain nombre de fois max
    # attempt = 1
    # while not os.path.exists(biofile) and attempt <= get_biofile_max_retries:
    #     logging.warning(f"Biofile {biofile} not found, attempt {attempt}")
    #     print("Wait biofile:", biofile, " ... tentative n°", attempt)
    #     time.sleep(get_biofile_delay)
    #     attempt += 1
        
    # # Si le biofile n'existe pas : alerte   
    # if not os.path.exists(biofile):
    #     content = f"Biofile: {biofile} does not exist."
    #     logging.error(content)
    #     send_mail_alert(recipients, content)
    #     return
    
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Biofile trouvé")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    print(f"Biofile {biofile} found.")
    logging.info(f"Biofile {biofile} found.")
        
    # Récupérer le checksum du biofile
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Calcul du checksum")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    checksum_current_biofile = md5(biofile)    
    print(f"Checksum : {checksum_current_biofile}")
        
       

# Fonction principale : process JSON file
def diagho_process_file(file, config):
    """
    Traite un fichier JSON ou TSV : import du biofile dans Diagho + import des configurations associées.

    Args:
        file (str): Chemin vers le fichier d'entrée (JSON ou TSV).
        config (dict): Configuration contenant les paramètres nécessaires pour le traitement.

    Returns:
        None
    """
    print(f"Processing file: {file}")
    logging.info(f"Processing file: {file}")
    
    # Configuration et URLs
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("1. Chargement de la config")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    pretty_print_json_string(config)
    recipients = config['emails']['recipients']
    path_biofiles = config['input_biofiles']
    get_biofile_max_retries = config['check_biofile']['max_retries']
    get_biofile_delay = config['check_biofile']['delay']
    
    # Vérification de l'API Diagho
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("2. Test connexion API")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    if not diagho_api_test(config):
        content = "Failed to connect to Diagho API. Exit."
        send_mail_alert(recipients, content)
        logging.error(content)
        return
    
    # Connexion à l'API
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("3. Login API")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    # Login
    diagho_api_login(config)
    
    # Récup le token
    access_token = get_access_token(config)
    print(f"Access token: {access_token}")
    logging.info(f"Access token: {access_token}")
    
    # Traitement du fichier
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("4. Test format du fichier : TSV ou JSON")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    if file.endswith('.tsv'):
        print(f"TSV file detected. Parsing TSV to JSON for file: {file}")
        logging.info(f"TSV file detected. Parsing TSV to JSON for file: {file}")
        # TODO: #10 Parser TSV en JSON
    elif file.endswith('.json'):
        print(f"JSON file detected: {file}")
        logging.info(f"JSON file detected: {file}")
    else:
        content = f"Unsupported file format for file: {file}"
        print(content)
        logging.error(content)
        send_mail_alert(recipients, content)
        return
    
    # Vérification du format JSON
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("5. Si JSON : test du formattage du fichier")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    if not check_json_format(file):
        content = "Failed to process JSON input file."
        logging.error(content)
        send_mail_alert(recipients, content)
        return
    
    # Extraction des informations de fichier
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("6. Récupérer les infos du fichier JSON 'files'")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    dict_files = get_files_infos(file)
    pretty_print_json_string(dict_files)
    
    # Foreach filename : vérifier s'il existe dans le répertoire path_biofiles
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("7. Pour chaque filename...")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    for filename, file_info in dict_files.items():
        biofile = os.path.join(path_biofiles, filename)
        checksum = file_info["checksum"]
        persons = file_info["persons"]
        
        print(f"filename           : {filename}")
        print(f"Processing biofile : {biofile}")
        print(f"Persons            : {persons}")

        logging.info(f"Processing biofile: {biofile}")

        # Tant que le biofile n'existe pas...
        # On boucle toutes les X secondes pendant un certain nombre de fois max
        attempt = 1
        while not os.path.exists(biofile) and attempt <= get_biofile_max_retries:
            logging.warning(f"Biofile {biofile} not found, attempt {attempt}")
            print("Wait biofile:", biofile, " ... tentative n°", attempt)
            time.sleep(get_biofile_delay)
            attempt += 1
        
        # Si le biofile n'existe pas : alerte   
        if not os.path.exists(biofile):
            content = f"Biofile: {biofile} does not exist."
            logging.error(content)
            send_mail_alert(recipients, content)
            continue
        
        # process_biofile(config, biofile)
        
        print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("8. Biofile trouvé")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        print(f"Biofile {biofile} found.")
        logging.info(f"Biofile {biofile} found.")
        
        # Récupérer le checksum du biofile
        print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("8. Calcul du checksum")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        checksum_current_biofile = md5(biofile)
        
        print(f"Checksum : {checksum_current_biofile}")
        
        # Si c'est un VCF :
        if biofile.endswith('.vcf') or biofile.endswith('.vcf.gz'):
            print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("9. Process VCF")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
            process_vcf_file(biofile, checksum_current_biofile, config, recipients, file, persons)
            
        # Si c'est un BED :
        elif biofile.endswith('.bed'):
            logging.info(f"Processing BED file: {biofile}")
            # TODO: #11 Implémenter le traitement pour les fichiers BED
            process_bed_file(biofile, checksum_current_biofile, config, recipients, file, persons)
            
        else:
            content = f"BIOFILE: wrong format for file: {biofile}."
            logging.error(content)
            send_mail_alert(recipients, content)
    
    print(f"All biofiles have been loaded in Diagho")
    
    # Upload JSON file  
    file_to_import = file
    print("import file config: ", file_to_import)
    diagho_api_post_config(config['diagho_api']['config'], file_to_import, config)
        

def process_vcf_file(biofile, checksum_current_biofile, config, recipients, files_file, persons):
    """
    Processus de traitement pour les fichiers VCF.

    Args:
        biofile (str): Chemin vers le fichier biofile.
        checksum_current_biofile (str): Checksum calculé du fichier biofile.
        config (dict): Configuration du système.
        recipients (list): Liste des destinataires des alertes par email.
        file (str): Fichier d'entrée initial.
        persons (list): Liste des identifiants de personnes liées au fichier.

    Returns:
        None
    """
    print(f"\nStart function : process_vcf\n")
    
    url_diagho_api_biofiles = config['diagho_api']['biofiles']
    url_diagho_api_loading_status = config['diagho_api']['loading_status']
    accession_id = config['accessions']['vcf']
    
    # Post du biofile + récupérer le chekcsum
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("10. POST du Biofile")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")

    checksum_from_api = diagho_api_post_biofile(url_diagho_api_biofiles, biofile, accession_id, config).get('checksum')
    print(f"Checksum renvoyé par l'API : {checksum_from_api}")
    
    # Si l'upload ne fonctionne pas : alerte
    if not checksum_from_api or checksum_from_api is None:
        content = "Failed to upload biofile and obtain checksum from API."
        logging.error(content)
        print(content)
        send_mail_alert(recipients, content)
        return
    
    # Vérification du checksum du fichier uploadé avec le checksum calculé avant
    # Si OK : continuer
    if not check_md5sum(checksum_from_api, checksum_current_biofile):
        content = "MD5 checksum mismatch."
        logging.error(content)
        send_mail_alert(recipients, content)
        print(f"{content}")
        return
    
    # if check_md5sum(checksum_from_api, checksum_current_biofile):
    print(f"Les checksum sont identiques")
        
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("11. Check du Loading Status")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    
    max_retries = config['check_loading']['max_retries']
    delay = config['check_loading']['delay']
    loading_status = check_loading_status(config, url_diagho_api_loading_status, checksum_current_biofile, max_retries, delay)
        
    if loading_status:
        content = "Loading File = SUCCESS"
        logging.info(content)
        send_mail_info(recipients, content)
        print(f"{content}")
            
        time.sleep(10)
            
            # Traitement des fichiers de configuration
            # pretty_print_json_string(persons)
            # family_file = find_json_file(config['input_data'], persons, "family")
            # interp_file = find_json_file(config['input_data'], checksum_current_biofile, "interpretation")
            
            # file_to_import = files_file
            # print("import file config: ", file_to_import)
            # diagho_api_post_config(config['diagho_api']['config'], file_to_import, config)
            
            # logging.info(f"Found family file: {family_file}")
            # logging.info(f"Found interpretation file: {interp_file}")
            
            # if family_file:
            #     diagho_api_post_config(config['diagho_api']['config'], family_file, config)
            #     time.sleep(10)
            #     copy_and_remove_file(family_file, config['backup_data_files'])
            # if files_file:
            #     diagho_api_post_config(config['diagho_api']['config'], files_file, config)
            #     time.sleep(10)
            #     # copy_and_remove_file(files_file, config['backup_data_files'])
            # if interp_file:
            #     diagho_api_post_config(config['diagho_api']['config'], interp_file, config)
            #     time.sleep(10)
            #     copy_and_remove_file(interp_file, config['backup_data_files'])
            
    else:
        content = "Loading File = FAIL"
        logging.error(content)
        send_mail_alert(recipients, content)
    # else:
    #     content = "MD5 checksum mismatch."
    #     logging.error(content)
    #     send_mail_alert(recipients, content)
               

def process_bed_file(biofile, checksum_current_biofile, config, recipients, files_file, persons):
    """
    Process a BED file.

    Arguments:
        biofile (str): Path to the BED file.
        checksum_current_biofile (str): MD5 checksum of the current BED file.
        config (dict): Configuration dictionary.
        recipients (list): List of email recipients for notifications.
        file (str): Path to the input JSON or TSV file.
        persons (list): List of person identifiers associated with the file.
    """
    logging.info(f"Processing BED file: {biofile}")
    
    url_diagho_api_biofiles = config['diagho_api']['biofiles']
    url_diagho_api_config = config['diagho_api']['config']
    
    # Check if the BED file exists
    if not os.path.exists(biofile):
        content = f"BIOFILE: {biofile} doesn't exist."
        logging.error(content)
        send_mail_alert(recipients, content)
        return
    
    logging.info(f"BED file: {biofile} exists.")
    
    # Get MD5 checksum from the current BED file
    checksum_from_api = diagho_api_post_biofile(url_diagho_api_biofiles, biofile, 1)
    
    # Compare checksums
    check_md5 = check_md5sum(checksum_from_api, checksum_current_biofile)
    
    if check_md5:
        # If checksums are identical, proceed with processing
        logging.info("MD5 checksum matches for BED file.")
        
        # Check loading status
        max_retries = config['check_loading']['max_retries']
        delay = config['check_loading']['delay']
        loading_status = check_loading_status(config, url_diagho_api_biofiles, checksum_from_api, max_retries, delay)
        
        if loading_status:
            # If loading status is successful
            content = "Loading BED file = SUCCESS"
            logging.info(content)
            send_mail_info(recipients, content)
            
            # POST config files
            family_file = find_json_file(config['input_data'], persons, checksum_current_biofile, "family")
            interp_file = find_json_file(config['input_data'], persons, checksum_current_biofile, "interpretation")
            
            logging.info(f"Family file found: {family_file}")
            logging.info(f"Interpretation file found: {interp_file}")
            
            if family_file:
                diagho_api_post_config(config['diagho_api']['config'], family_file)
                copy_and_remove_file(family_file, config['backup_data_files'])
            if files_file:
                diagho_api_post_config(config['diagho_api']['config'], files_file)
                copy_and_remove_file(files_file, config['backup_data_files'])
            if interp_file:
                diagho_api_post_config(config['diagho_api']['config'], interp_file)
                copy_and_remove_file(interp_file, config['backup_data_files'])
        else:
            # If loading status fails
            content = "Loading BED file = FAIL"
            logging.error(content)
            send_mail_alert(recipients, content)
    else:
        # MD5 checksum does not match
        content = "MD5 checksum mismatch for BED file."
        logging.error(content)
        send_mail_alert(recipients, content)


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
    print("check_loading_status")
    print("MAX_RETRIES:", max_retries)
    # Get loading status :
    status = diagho_api_get_loadingstatus(url, checksum, config).get('loading')
    print("Initial status=", status)
    
    while status not in [0, 3]:
        print(f"\nTentative {attempt + 1}: Statut de chargement = {status}")
        logging.warning(f'Attempt {attempt + 1}: loading_status = {status} ... Retry...')
        
        # Attendre avant de réessayer
        print(f"Attente de {delay} secondes...\n")
        time.sleep(delay)
        
        # Récupérer à nouveau le statut de chargement
        status = diagho_api_get_loadingstatus(url, checksum, config).get('loading')
        print("Nouveau statut =", status)
        
        # Incrémenter le compteur de tentatives
        attempt += 1
        
        # Vérifier si le nombre maximal de tentatives est atteint
        if attempt >= max_retries:
            print("Nombre maximal de tentatives atteint. Abandon.")
            logging.error('GET_LOADING_STATUS: Maximum number of attempts reached.')
            return None
        
    # Vérification des statuts finaux
    if status == 0:
        return False
    elif status == 3:
        print("Chargement terminé avec succès.")
        logging.info('Loading completed successfully.')
        return True
    else:
        print(f"Statut inconnu ou non géré: {status}. Abandon.")
        return None
