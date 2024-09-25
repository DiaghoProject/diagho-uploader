#!/usr/bin/python3

import json
import hashlib
import subprocess
import inspect
import dateutil
import os
import pandas as pd
from subprocess import Popen, PIPE
from datetime import datetime
from dateutil import parser


# Supprime les lignes vides du fichier
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


# Valide le header du fichier TSV
def validate_tsv_headers(input_file, required_headers, encoding='latin1'):
    """
    Validate the headers of a TSV file to ensure it contains all required columns.
    
    Parameters
    ----------
    input_file : str
        The path to the input TSV file.
    required_headers : list
        The list of required column headers.
    encoding : str, optional
        The encoding of the input TSV file. Default is 'latin1'.
    
    Returns
    -------
    bool
        True if the TSV file has all the required headers, False otherwise.
    """
    # Read only the headers (first row) from the TSV file
    try:
        df = pd.read_csv(input_file, delimiter='\t', encoding=encoding, nrows=0)
        tsv_headers = list(df.columns)

        # Find missing columns
        missing_headers = [header for header in required_headers if header not in tsv_headers]
        # Find unexpected columns
        unexpected_headers = [header for header in tsv_headers if header not in required_headers]
        
        if missing_headers:
            print(f"Error: Missing required columns: {missing_headers}")
        if unexpected_headers:
            print(f"Warning: Unexpected columns present: {unexpected_headers}")
        
        # If there are missing required headers, return False
        if missing_headers:
            return False
        # Otherwise, return True indicating the headers are valid
        return True
    
    except Exception as e:
        print(f"Error reading the file: {str(e)}")
        return False        

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
        
        headers = first_line.split('\t')
        
        # print(headers)
        if len(headers) < 2:
            raise Exception("Invalid TSV format: Expected tab-separated headers.")
        
        num_columns = len(headers)
        
        line_num = 1
        for line in file:
            line_num += 1
            fields = line.split('\t')
            if len(fields) != num_columns:
                raise Exception(f"Line {line_num} does not match the number of columns in the header.")
            
            # Optionally, add more validations as needed
            # TODO #13 Add validation of the TSV header according to template
            expected_header = ['filename', 'checksum', 'file_type', 'sample', 'bam_path', 'family_id', 'person_id', 'father_id', 'mother_id', 'sex', 'is_affected', 'last_name', 'first_name', 'date_of_birth', 'hpo', 'interpretation_title', 'is_index', 'project', 'assignee', 'priority', 'filter_tag', 'note']
            
            if headers != expected_header:
                raise Exception(f"Header does not match the expected template.")
            
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

# Pretty print json string
def pretty_print_json_string(string):
    """
    Pretty print a JSON string.

    Arguments:
        json_str : str : The JSON string to be pretty printed.
    """
    try:
        json_string = json.dumps(string)
        json_dict = json.loads(json_string)
        print(json.dumps(json_dict, indent = 1))
    except json.JSONDecodeError as e:
        print(f"Invalid JSON string: {e}")
     

def remove_empty_keys(d):
    """
    Supprime les clés avec des valeurs vides (None ou "") dans un dictionnaire.

    Args:
        d (dict): Le dictionnaire à nettoyer.

    Returns:
        dict: Le dictionnaire nettoyé.
    """
    return {k: v for k, v in d.items() if v not in [None, ""]}



def write_final_JSON_file(data_dict, key_name, output_file, encoding='utf-8'):
    """
    Writes the values of a dictionary to a JSON file under a specified key.

    Args:
        data_dict (dict): The dictionary containing the data to be written.
        key_name (str): The key under which the data will be stored in the JSON file.
        output_file (str): The path to the output JSON file.
    """
    # Fonction pour écrire le dictionnaire de données dans un fichier JSON
    with open(output_file, 'w', encoding=encoding) as f:
        json.dump({key_name: list(data_dict.values())}, f, ensure_ascii=False, indent=4)
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


def get_file_type(input_file):
    """
    Determines the type of the input file based on its extension.
    
    Parameters
    ----------
    input_file : str
        The path to the input file.
    
    Returns
    -------
    str
        The file type: 'tsv', 'json', or 'unknown'.
    """
    file_extension = os.path.splitext(input_file)[1].lower()  # Get the file extension and convert to lowercase
    
    if file_extension == '.tsv':
        return 'tsv'
    elif file_extension == '.json':
        return 'json'
    else:
        return 'unknown'