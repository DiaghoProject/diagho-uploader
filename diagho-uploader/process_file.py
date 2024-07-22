#!/usr/bin/python3

import json
import pandas as pd
import os

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
    else:
        print(f"JSON file...")
    
    # 1- Récup les filenames
    dict_filenames = {}
    dict_filenames = get_filenames(file)
    pretty_print_json_string(dict_filenames)
    
    filenames = dict_filenames.keys()
    print(">>> FILENAMES : ", filenames)
    
    # 2- Pour chaque filename : vérifier s'il existe dans le répertoire BIOFILES
    for filename in filenames:
        file_target = path_biofiles + "/" + filename
        if os.path.exists(file_target):
            print("Le BIOFILE : ", file_target, " existe.")
        else:
            print("Le BIOFILE : ", file_target, " n'existe pas.")
    
    # 3- Si oui :
    
    # 3.1- Si c'est un VCF
    
    # 3.2- Si c'est un BED :
    
    # 4- Si non :
    ## Ne rien faire
    

def get_filenames(json_input):
    input_data = pd.read_json(json_input)
    dict_filenames = {}
    for file in input_data['files']:
        filename = file['filename']
        checksum = file['filename']
        dict_filenames[filename] = {
            "checksum" : checksum
        }
        
    return dict_filenames