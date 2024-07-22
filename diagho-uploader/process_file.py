#!/usr/bin/python3

import json
import pandas as pd
import os
import hashlib



from functions import * 



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
        
        ## Get MD5 from biofile
        biofile_actual_checksum = md5(biofile)
        print("   >> biofile_actual_checksum", biofile_actual_checksum)
        
        
        
        # 3- Si oui :
        if os.path.exists(biofile):
            print("---> Le BIOFILE : ", biofile, " existe.")           
    
            # 3.1- Si c'est un VCF :
            if biofile.endswith('.vcf') or biofile.endswith('.vcf.gz'):
                print("   BIOFILE type: VCF")
                
                ## POST
                ## TODO #2 API post biofile VCF
                print("API - POST VCF")
                
                # POST du biofile
                diagho_api_post_biofile(biofile, checksum)
                
                # GET md5 du POST
                diagho_api_get_md5sum(biofile)
                
            
            # 3.2- Si c'est un BED :
            elif biofile.endswith('.bed'):
                print("   BIOFILE type: BED")
                
                ## POST
                ## TODO #3 API post biofile BED
                print("API - POST BED")
                
                diagho_api_post_biofile(biofile, checksum)
                
                diagho_api_get_md5sum(biofile)
                
                
            else:
                print("BIOFILE: wrong format.")
                
                             
        else:
            print("Le BIOFILE : ", biofile, " n'existe pas.")
    
            # 4- Si non :
            ## Ne rien faire
    

def get_files_infos(json_input):
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


def diagho_api_post_biofile(biofile_filename, biofile_checksum):
    print("API - POST biofile : ", biofile_filename, biofile_checksum)
    
    ## TODO check loading
    
def diagho_api_get_md5sum(biofile):
    print("Get MD5SUM for biofile:", biofile)
    
def md5(filepath):
    """
    md5 for file.

    Parameters
    ----------
    
    """
    hash_md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
    
def check_md5sum():
    print("check_md5sum")
    
def check_loading(biofile, loading_code):
    print("Check LOADING")
    
    ## Si FAIL :
    if loading_code == 0:
        ## 
        print("   >>> LOADING == 0 ... FAIL")
        
        # ALERT
    
    ## Si SUCCESS :
    elif loading_code == 3:
        ## 
        print("   >>> LOADING == 3 ... SUCCESS")
        
        ## POST config
        # 1- Récup les configfiles correspondants
        # families
        # interpretation
        # files
        
        
        # 2- POST config
    
    ## Si autre situation :
    else:
        ## 
        print("   >>> LOADING != 0 && LOADING != 3 ... Autre situation")
        

def get_configfiles():
    print("get_configfiles")

def diagho_api_post_config(config_file):
    print("diagho_api_post_config")
    
