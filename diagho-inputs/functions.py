#!/usr/bin/python3
# -*- coding: latin-1 -*-

import json
import hashlib
import subprocess
import inspect
import dateutil
import os
from subprocess import Popen, PIPE
from datetime import datetime
from dateutil import parser



def remove_trailing_empty_lines(file_path, encoding):
    """
    Removes trailing empty lines from a text file.

    This function reads the specified file and removes any empty lines 
    at the end of the file. Only non-empty lines are retained.

    Args:
        file_path (str): The path to the file to be processed.
        encoding (str): The encoding used to read and write the file.
    """
    # Lire le fichier et sauvegarder les lignes non vides
    with open(file_path, 'r', encoding=encoding) as file:
        lines = [line for line in file if line.strip()]
    
    # Réécrire le fichier sans les lignes vides à la fin
    with open(file_path, 'w', encoding=encoding) as file:
        file.writelines(lines)
        

def validate_tsv_file(input_file, encoding='latin1'):
    """
    Validates the format of a TSV (Tab-Separated Values) file.
    
    Parameters
    ----------
    input_file : str
        The path to the input TSV file.
    encoding : str, optional
        The encoding of the file. Default is 'latin1'.
    
    Returns
    -------
    headers : list
        A list of headers (column names) extracted from the TSV file.
    """
    dos2unix(input_file, encoding)  # Convert the input file from DOS to UNIX format
    
    with open(input_file, 'r', encoding=encoding) as file:
        first_line = file.readline().strip()
        if not first_line:
            raise Exception("TSV file is empty.")
            # raise ValueError("TSV file is empty.")
        
        headers = first_line.split('\t')
        
        print(headers)
        if len(headers) < 2:
            raise Exception("Invalid TSV format: Expected tab-separated headers.")
            # raise ValueError("Invalid TSV format: Expected tab-separated headers.")
        
        num_columns = len(headers)
        
        line_num = 1
        for line in file:
            line_num += 1
            fields = line.split('\t')
            if len(fields) != num_columns:
                raise Exception(f"Line {line_num} does not match the number of columns in the header.")
                # raise ValueError(f"Line {line_num} does not match the number of columns in the header.")
            
            # Optionally, add more validations as needed
            # TODO #13 Add validation of the TSV header according to template
            expected_header = ['filename', 'checksum', 'file_type', 'sample', 'bam_path', 'family_id', 'person_id', 'father_id', 'mother_id', 'sex', 'is_affected', 'last_name', 'first_name', 'date_of_birth', 'hpo', 'interpretation_title', 'is_index', 'project', 'assignee', 'priority', 'filter_tag', 'note']
            
            if headers != expected_header:
                raise Exception(f"Header does not match the expected template.")
                # raise ValueError(f"Header does not match the expected template.")
            
    return headers

    
def dos2unix(file_path, encoding='latin1'):
    """
    Converts a file with DOS (CRLF) line endings to UNIX (LF) line endings.
    
    Parameters
    ----------
    file_path : str
        The path to the file to be converted.
    
    Returns
    -------
    None
    """
    with open(file_path, 'r', encoding=encoding) as file:
        content = file.read()
    content = content.replace('\r\n', '\n')
    with open(file_path, 'w', encoding=encoding) as file:
        file.write(content)




def parse_date(date_str):
    """
    Parses a date string in the format 'DD/MM/YYYY' and returns it in the format 'YYYY-MM-DD'.
    
    This function attempts to parse the provided date string using the specified date format.
    If the parsing is successful, it converts the date to the 'YYYY-MM-DD' format.
    If the parsing fails, an empty string is returned.
    
    Args:
        date_str (str): The date string to be parsed.
        
    Returns:
        str: The formatted date string in 'YYYY-MM-DD' format if parsing is successful, 
             otherwise an empty string.
    """
    # Define the expected date format
    date_format = '%d/%m/%Y'
    
    try:
        # Parse the date string according to the specified format
        dob_obj = datetime.strptime(date_str, date_format)
        # Convert the parsed date object to the desired output format
        formatted_date = dob_obj.strftime("%Y-%m-%d")
        return formatted_date
    except ValueError:
        # If parsing fails, return an empty string
        return ""


def remove_empty_string_values(dict_data):
    """
    Supprime les clés d'un dictionnaire si leurs valeurs sont des chaînes vides.

    Args:
        dict_data (dict): Le dictionnaire à traiter.

    Returns:
        dict: Un nouveau dictionnaire sans les clés ayant des valeurs de chaînes vides.
    """
    # Fonction pour supprimer les valeurs vides (chaînes vides) d'un dictionnaire
    return {key: value for key, value in dict_data.items() if value != ""}



def write_final_JSON_file(data_dict, key_name, output_file):
    """
    Writes the values of a dictionary to a JSON file under a specified key.

    Args:
        data_dict (dict): The dictionary containing the data to be written.
        key_name (str): The key under which the data will be stored in the JSON file.
        output_file (str): The path to the output JSON file.
    """
    # Fonction pour écrire le dictionnaire de données dans un fichier JSON
    with open(output_file, 'w') as f:
        json.dump({key_name: list(data_dict.values())}, f, indent=4)
    print(f"Write file: {output_file}")
        
        

def replace_special_characters(string):
    """
    Replaces specific special characters in a string with their designated replacements.

    Args:
        string (str): The input string that may contain special characters.

    Returns:
        str: The string with special characters replaced by their substitutes.
    """
    # Remplacement spécifique des caractères spéciaux
    replacements = {
        '\u008c': 'OE'
    }
    for key, value in replacements.items():
        string = string.replace(key, value)
    
    return string







#################################################################################################
## 
## FONCTIONS POUR LES VCFS
##
#################################################################################################

def get_VCF_info(pattern, directory):
    """
    Fonction pour récupérer les informations du fichier VCF correspondant au pattern donné.
    À adapter en fonction de la logique de recherche des fichiers VCF dans votre système.
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if pattern in file and file.endswith('.vcf.gz'):
                return {
                    'filename': file,
                    'path': os.path.join(root, file)
                }
    return None


def get_filename(familyID, directory):
    """Get filename.

    Parameters
    ----------
    
    """
    process = subprocess.Popen(('find', directory, '-type', 'f', '-name *', familyID, '*'))
    process.communicate()

def get_absolutePathFile(fname, directory):
    """The absolute path for file.

    Parameters
    ----------
    
    """
    process = subprocess.Popen(('find', directory, '-type', 'f', '-name', fname))
    process.communicate()

    

# Calcul MD5
def md5(filepath):
    """
    Calcule le hash MD5 d'un fichier.

    Arguments:
        filepath (str): Chemin absolu du fichier.

    Returns:
        str: Le hash MD5 du fichier sous forme de chaîne hexadécimale, ou None en cas d'erreur. 
    """
    function_name = inspect.currentframe().f_code.co_name
    
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (IOError, FileNotFoundError) as e:
        content = f"FUNCTION: {function_name}:\n\nErreur lors de l'ouverture ou de la lecture du fichier : {e}"
        print(f"Erreur lors de l'ouverture ou de la lecture du fichier : {e}")
        return None
    


def split_families_with_root(json_file, output_dir):
    with open(json_file, 'r') as f:
        json_data = json.load(f)
        
    # Assure que le répertoire de sortie existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Parcours chaque famille dans le JSON
    for family in json_data['families']:
        # Génère le nom de fichier en utilisant l'identifiant de la famille
        filename = f"{family['identifier']}.family.json"
        file_path = os.path.join(output_dir, filename)
        
        # Enveloppe chaque famille dans une structure avec la clé "families"
        family_data = {"families": [family]}
        
        # Écrit les données de la famille dans un fichier JSON
        with open(file_path, 'w') as file:
            json.dump(family_data, file, indent=4)
        print(f"Famille {family['identifier']} sauvegardée dans {file_path}")


def split_files_with_root(json_file, output_dir):
    with open(json_file, 'r') as f:
        json_data = json.load(f)
        
    # Assure que le répertoire de sortie existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Parcours chaque famille dans le JSON
    for file in json_data['files']:
        # Génère le nom de fichier en utilisant l'identifiant de la famille
        cut_filename = file['filename'].split('.', 2)
        small_filename = '.'.join(cut_filename[:2]).strip()
        filename = f"{small_filename}.file.json"
        file_path = os.path.join(output_dir, filename)
        
        # Enveloppe chaque famille dans une structure avec la clé "families"
        file_data = {"file": [file]}
        
        # Écrit les données de la famille dans un fichier JSON
        with open(file_path, 'w') as file_out:
            json.dump(file_data, file_out, indent=4)
        print(f"Fichier {file['filename']} sauvegardé dans {file_path}")

def split_interpretations_with_root(json_file, output_dir):
    with open(json_file, 'r') as f:
        json_data = json.load(f)
        
    # Assure que le répertoire de sortie existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Parcours chaque famille dans le JSON
    for interpretation in json_data['interpretations']:
        # Génère le nom de fichier en utilisant l'identifiant de la famille
        filename = f"{interpretation['project']}.{interpretation['indexCase']}.interpretation.json"
        file_path = os.path.join(output_dir, filename)
        
        # Enveloppe chaque famille dans une structure avec la clé "families"
        interpretation_data = {"interpretations": [interpretation]}
        
        # Écrit les données de la famille dans un fichier JSON
        with open(file_path, 'w') as file:
            json.dump(interpretation_data, file, indent=4)
        print(f"Interpretation {interpretation['title']} sauvegardée dans {file_path}")
    