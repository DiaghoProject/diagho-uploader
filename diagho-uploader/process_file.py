#!/usr/bin/python3

import json
import pandas as pd
import os
import hashlib
import time

import random

# import logging



from functions import * 


# logging.basicConfig(
#     level=logging.DEBUG,                     # Définir le niveau de log minimum
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # Format du message
#     handlers=[
#         logging.FileHandler('app.log'),     # Enregistrer les logs dans un fichier
#         logging.StreamHandler()             # Afficher les logs sur la console
#     ]
# )


def diagho_process_file(file, path_biofiles):
    """
    Process file.

    Arguments:
        file : input  JSON file
        path_biofiles: path to the directory where there are the biofiles (VCF or BED)
    """
    print(f"Process file: {file}")
    
    # Si TSV : parser tsv2json
    if file.endswith('.tsv'):
        print(f"TSV file...")
        print(f"Parser tsv2json for file: {file}")
        ## TODO #1 If input file == TSV : parser tsv2json
        
    else:
        print(f"JSON file...")
    
    # 1- Récup les filenames
    dict_files = {}
    dict_files = get_files_infos(file)
    pretty_print_json_string(dict_files)
    
    # 2- Pour chaque filename : vérifier s'il existe dans le répertoire BIOFILES
    for filename in dict_files:
        biofile = path_biofiles + "/" + filename
        checksum = dict_files[filename]["checksum"]
        persons = dict_files[filename]["persons"]
        
        print("\nBIOFILE:")
        print("   >> Filename:", filename)
        print("   >> Checksum:", checksum)
        print("   >> persons:", persons)
        
        # 3- Si oui :
        if os.path.exists(biofile):
            print("   ---> Le BIOFILE : ", biofile, " existe.")  
            
            ## Get MD5 from biofile
            checksum_current_biofile = md5(biofile)
            print("   >> checksum_current_biofile", checksum_current_biofile)         
    
            # 3.1- Si c'est un VCF :
            if biofile.endswith('.vcf') or biofile.endswith('.vcf.gz'):
                
                ## POST
                ## TODO #2 API post biofile VCF
                
                # 1. POST du biofile
                diagho_api_post_biofile(biofile, checksum)
                
                # 2. GET md5 du POST
                checksum_from_api = diagho_api_get_md5sum(biofile)
                
                # 3. Comparer les checksums
                check_md5 = check_md5sum(checksum_from_api, checksum_current_biofile)
                
                # 4. Si checksum sont identiques :
                if check_md5:
                    print("MD5 = PASS")
                    # Ce sont bien les mêmes fichiers
                     
                    # get loading status
                    # loading_code = diagho_api_get_loadingstatus()
                    
                    # check loading status
                    with open('config/config.yaml', 'r') as file:
                        config = yaml.safe_load(file)
                    max_retries = config['check_loading']['max_retries']
                    delay = config['check_loading']['delay']
                    loading_status = check_loading_status(max_retries, delay, attempt=0)
                    
                    # En fonction du statut :
                    # SUCCESS :
                    if loading_status:
                        recipients = "benedicte.nouyou@chu-rennes.fr"
                        subject = "TEST Diagho-Uploader"
                        content = "Loading File = SUCCESS"
                        send_mail(recipients, subject, content)
        
                        ## POST config
                        # 1- Récup les configfiles correspondants
                        # families
                        # interpretation
                        # files
                    
                    # FAIL :
                    else:
                        # Alerte
                        recipients = "benedicte.nouyou@chu-rennes.fr"
                        subject = "TEST Diagho-Uploader"
                        content = "Loading File = FAIL"
                        send_mail(recipients, subject, content)
                        
                else:
                    # md5 non valide
                    # Alerte
                    recipients = "benedicte.nouyou@chu-rennes.fr"
                    subject = "TEST Diagho-Uploader"
                    content = "MD5 = FAIL"
                    send_mail(recipients, subject, content)
                    
            
            # 3.2- Si c'est un BED :
            elif biofile.endswith('.bed'):
                print("   BIOFILE type: BED")
                
                ## POST
                ## TODO #3 API post biofile BED                
                
            else:
                print("BIOFILE: wrong format.")
                
                             
        else:
            print("Le BIOFILE : ", biofile, " n'existe pas.")
            # 4- Si non :
            ## Ne rien faire
    

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
    Description.

    Arguments:

    Returns:
        
    """
    print("check_loading_status")
    
    status = diagho_api_get_loadingstatus()
    print("STATUS:", status)
    
    if attempt >= max_retries:
        print("Nombre maximal de tentatives atteint. Abandon.")
        return None

    status = diagho_api_get_loadingstatus()
    print(f"Tentative {attempt + 1}: Statut de chargement = {status}")

    if status == 0:
        return False 
    elif status == 3:
        return True
    elif status == 1 or status == 2 or status == 4:
        print(f"Attente de {delay} secondes avant la tentative {attempt + 2}")
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


    
#------------------------------------------------------------------
# Functions for API queries

def diagho_api_post_biofile(biofile_filename, biofile_checksum):
    """
    Description.

    Arguments:

    Returns:
        
    """
    print("API POST - Biofile : ", biofile_filename, biofile_checksum)
    
def diagho_api_get_md5sum(biofile):
    """
    Description.

    Arguments:

    Returns:
        
    """
    print("API GET - MD5SUM for biofile:", biofile)
    ## Pour les tests:
    return "139361d8c92fd7bba1e26fbe89ebf5eb"

def diagho_api_get_loadingstatus():
    """
    Description.

    Arguments:

    Returns:
        
    """
    print("diagho_api_get_loadingstatus")
    ## Pour les tests ------------------
    loading_status = random.randint(1, 4)
    ##----------------------------------
    return loading_status

def diagho_api_post_config(config_file):
    """
    Description.

    Arguments:

    Returns:
        
    """
    print("diagho_api_post_config")