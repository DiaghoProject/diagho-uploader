#!/usr/bin/python3

import json
import pandas as pd
import os
import hashlib
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



def diagho_process_file(file, config):
    """
    Process file.

    Arguments:
        file: input JSON or TSV file
        config: config file
    """
    
    print(f"Process file: {file}")
    
    # Get informations from config file
    recipients = config['emails']['recipients']
    path_biofiles = config['input_biofiles']
    get_biofile_max_retries = config['check_biofile']['max_retries']
    get_biofile_delay = config['check_biofile']['delay']
    
    url_diagho_api_healthcheck = config['diagho_api']['healthcheck']
    url_diagho_api_login = config['diagho_api']['login']
    username = config['diagho_api']['username']
    password = config['diagho_api']['password']
    
    # TEST DIAGHO API :
    if not diagho_api_test(url_diagho_api_healthcheck):
        content = "Failed to connect to Diagho API. Exit."
        send_mail_alert(recipients, content)
        return
    
    diagho_api_post_login(url_diagho_api_login, username, password)
    
    access_token = get_access_token('tokens.json')
    print("access_token:", access_token)
    
    

    
    # Si TSV : parser tsv2json
    if file.endswith('.tsv'):
        print(f"TSV file...")
        print(f"Parser tsv2json for file: {file}")
        ## TODO #1 If input file == TSV : parser tsv2json
        
        # On obtient un JSON "simple"
        
    else:
        print(f"JSON file...")
        
    # Check JSON : vérifier si fichier bien formaté
    check_json_format(file)
    if check_json_format(file) == False:
        content = "Failed to process JSON input file."
        send_mail_alert(recipients, content)
        return
    
    # Get filenames from JSON file
    dict_files = {}
    dict_files = get_files_infos(file)
    pretty_print_json_string(dict_files)
    
    # Foreach filename : vérifier s'il existe dans le répertoire path_biofiles
    for filename in dict_files:
        biofile = path_biofiles + "/" + filename
        checksum = dict_files[filename]["checksum"]
        persons = dict_files[filename]["persons"]
        
        print("\nBIOFILE:")
        print("   >> Filename:", filename)
        print("   >> Checksum:", checksum)
        print("   >> persons:", persons)
        
        # Tant que le biofile n'existe pas...
        # On boucle toutes les X secondes pendant Y minutes
        attempt = 1
        while not os.path.exists(biofile) and attempt <= get_biofile_max_retries:
            print("Wait biofile:", biofile, " ... tentative n°", attempt)
            time.sleep(get_biofile_delay)
            attempt += 1
            
        
        # If file exists:
        if os.path.exists(biofile):
            print("   ---> Biofile: ", biofile, " exists.")  
            
            # Get MD5 from current biofile
            checksum_current_biofile = md5(biofile)    
    
            # If file == VCF:
            if biofile.endswith('.vcf') or biofile.endswith('.vcf.gz'):
                
                
                ## POST
                ## TODO #2 API post biofile VCF
                
                # 1. POST du biofile
                diagho_api_post_biofile(biofile, checksum)
                
                # 2. GET md5 du POST
                checksum_from_api = diagho_api_get_md5sum(biofile)
                
                # 3. Comparer les checksums
                check_md5 = check_md5sum(checksum_from_api, checksum_current_biofile)
                
                # 4. Si checksum sont identiques : on continue
                if check_md5:
                    # Check loading status
                    max_retries = config['check_loading']['max_retries']
                    delay = config['check_loading']['delay']
                    loading_status = check_loading_status(max_retries, delay, attempt=0)
                    
                    # En fonction du statut :
                    if loading_status:
                        # ==> loading_status == Success
                        
                        # Mail
                        content = "Loading File = SUCCESS"
                        send_mail_info(recipients, content)
        
                        ## POST config
                        # 1- Récup les configfiles correspondants en utilisant les "persons"
                        # families
                        # interpretation
                        # files
                        
                        # 2- POST l'un après l'autre des fichiers 
                        file_families = "file_families"
                        file_files = "file_files"
                        file_interpretations = "file_interpretations"
                        
                        diagho_api_post_config(file_families)
                        diagho_api_post_config(file_files)
                        diagho_api_post_config(file_interpretations)
                    
                    else:
                        # ==> loading_status == Fail
                        content = "Loading File = FAIL"
                        send_mail_alert(recipients, content)
                        return
                        
                else:
                    # md5 non valide : ALERTE
                    content = "MD5 = FAIL"
                    send_mail_alert(recipients, content)
                    
            
            # If file == BED:
            elif biofile.endswith('.bed'):
                print("   BIOFILE type: BED")
                
                ## POST
                ## TODO #3 API post biofile BED                
                
            else:
                print("BIOFILE: wrong format.")
                content = "BIOFILE: wrong format."
                send_mail_alert(recipients, content)            
        else:
            # Le biofile attendu n'existe pas. 
            print("Le BIOFILE : ", biofile, " n'existe pas.")
            content = "Le BIOFILE : ", biofile, " n'existe pas."
            send_mail_alert(recipients, content)
            
            logging.error(f"Biofile: {biofile} doesn't exist.")


    

def get_files_infos(json_input):
    """
    Description.

    Arguments:

    Returns:
        
    """
    input_data = pd.read_json(json_input)
    dict_files = {}
    for file in input_data['files']:
        filename = file['filename']
        checksum = file['checksum']
        samples = file['samples']
        persons = []
        for sample in samples:
            person_id = sample["person"]
            persons.append(person_id)
        dict_files[filename] = {
            "checksum" : checksum,
            "persons" : persons
        }
    return dict_files

    
def md5(filepath):
    """
    Calculate MD5sum for file.

    Arguments:
        filepath : absolute path of the file

    Returns:
        hash_md5 
    """
    hash_md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
    
def check_md5sum(checksum1, checksum2):
    """
    Check MD5sum.

    Arguments:
        checksum1 : 
        checksum2 : 

    Returns:
        bool : True/False
    """
    # Vérifier que les deux sommes MD5 ont la même longueur (32 caractères pour MD5)
    if len(checksum1) != 32 or len(checksum2) != 32:
        raise ValueError("Les sommes de contrôle MD5 doivent avoir 32 caractères.")
    
    # Comparer les deux sommes MD5
    return checksum1.lower() == checksum2.lower()


def check_loading_status(max_retries=10, delay=5, attempt=0):
    """
    Vérification du statut de chargement.

    Arguments:
        max_retries: nombre de tentatives max.
        delay: déli (en secondes) entre chaque tentative.
        attempt=0

    Returns:
        True : si le fichier est chargé
        False : si échec de chargement
        
    """
    print("check_loading_status")
    
    if attempt >= max_retries:
        print("Nombre maximal de tentatives atteint. Abandon.")
        return None

    # Get loading status :
    status = diagho_api_get_loadingstatus()
    
    print(f"\nTentative {attempt + 1}: Statut de chargement = {status}")

    # Test des statuts :
    if status == 0:
        return False 
    elif status == 3:
        return True
    elif status == 1 or status == 2 or status == 4:
        print(f"Attente de {delay} secondes...\n")
        time.sleep(delay)
        return check_loading_status(max_retries, delay, attempt + 1)
    else:
        print(f"Statut inconnu: {status}. Abandon.")
        return None




def get_configfiles():
    """
    Description.

    Arguments:

    Returns:
        
    """
    print("get_configfiles")



def check_json_format(file_path):
    """
    Description.

    Arguments:

    Returns:
        
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            json.load(file)
        logging.info(f"File: '{file_path}' is well-formatted.")
        return True
    except json.JSONDecodeError as e:
        logging.error(f"File: '{file_path}' is not well-formatted: {e}")
        return False
    except FileNotFoundError:
        logging.error(f"File: '{file_path}' was not found.")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred while checking the file '{file_path}': {e}")
        return False
