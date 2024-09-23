#!/usr/bin/python3
# -*- coding: latin-1 -*-

import argparse
import csv
import dateutil
import hashlib
import json
import pandas as pd
import subprocess
import sys
import xml.etree.ElementTree as ET
import shutil
import glob
import os
import unicodedata
import sys

from subprocess import Popen, PIPE
from pandas import DataFrame
from pathlib import Path
from dateutil import parser
from datetime import datetime

# Import des fonctions
from functions import *

sys.getdefaultencoding()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert a TSV file to a JSON file.")
    parser.add_argument('--input_file', type=str, help="Path to the input file (TSV or JSON simple).")
    parser.add_argument('--output_directory', type=str, help="Path to the output directory.")
    parser.add_argument('--output_prefix', type=str, help="Prefix of the output JSON files.")
    parser.add_argument('--vcfs_directory', type=str, help="Path to the VCFs directory.")
    args = parser.parse_args()
    
    input_file = args.input_file
    output_directory = args.output_directory
    output_prefix = args.output_prefix
    vcfs_directory = args.vcfs_directory
    
    # STEP 1 : Create simple JSON file
    file_json_simple = os.path.join(output_directory, output_prefix + ".simple.json")
    print(f"Create simple JSON file: {file_json_simple}" )
    diagho_tsv2json(input_file, file_json_simple) 
   
    
    # ####################################################
    # # STEP 2
    # ####################################################
    # ## Familles
    # output_file = os.path.join(output_directory, output_prefix + ".families.json")
    # diagho_create_json_families(file_json_simple, output_file)
        
    # ## VCF Files
    # output_file = os.path.join(output_directory, output_prefix + ".files.json")
    # diagho_create_json_files(file_json_simple, output_file, vcfs_directory)
        
    # ## Interprétations
    # output_file = os.path.join(output_directory, output_prefix + ".interpretations.json")
    # diagho_create_json_interpretations(file_json_simple, output_file, vcfs_directory)
    
    
    # ####################################################
    # # STEP 3
    # ####################################################
    # # Combine les 3 fichiers JSON
    # file_families = os.path.join(output_directory, output_prefix + ".families.json")
    # file_vcfs = os.path.join(output_directory, output_prefix + ".files.json")
    # file_interpretations = os.path.join(output_directory, output_prefix + ".interpretations.json")
    # output_file = os.path.join(output_directory, output_prefix + ".FINAL.json")
    
    # combine_json_files(file_families, file_vcfs, file_interpretations, output_file)




# tsv2json
def diagho_tsv2json(input_file, output_file, lowercase_keys=False, encoding='latin1'): 
    """
    Converts a TSV (Tab-Separated Values) file to a JSON file for Diagho.
    
    Parameters
    ----------
    input_file : str
        The path to the input TSV file.
    output_file : str
        The path to the output JSON file.
    
    Returns
    -------
    None
    """
    
    try:
        remove_trailing_empty_lines(input_file,encoding)
        headers = validate_tsv_file(input_file, encoding)       
        
        with open(input_file, 'r', encoding=encoding) as file:
            file.readline()  # Skip the first line (header line)
            
            dict_final = {}
            for line in file:
                fields = line.strip().split('\t')
                sample_id = fields[headers.index('sample')]
                dict_sample = {headers[i]: fields[i] for i in range(len(headers))}
                dict_final[sample_id] = dict_sample
        
        with open(output_file, 'w', encoding='utf-8') as output_file:
            output_file.write(json.dumps(dict_final, indent=4))
    
    except ValueError as e:
        print(f"Error: {str(e)}")          
            




if __name__ == '__main__':
    main()
    