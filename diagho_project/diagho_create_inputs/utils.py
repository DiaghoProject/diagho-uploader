import csv
import datetime
import hashlib
import inspect
import json
import logging
import os
import pandas as pd
from datetime import datetime

from common.logger_config import logger
from common.log_utils import log_message


        
def remove_trailing_empty_lines(file_path, encoding):
    """
    Removes trailing empty lines from a text file.
    """
    # Lire le fichier et sauvegarder les lignes non vides
    with open(file_path, 'r', encoding=encoding) as file:
        lines = [line for line in file if line.strip()]
    
    # Réécrire le fichier sans les lignes vides à la fin
    with open(file_path, 'w', encoding=encoding) as file:
        file.writelines(lines)
        
        
        
def validate_tsv_headers(input_file, required_headers, encoding='latin1'):
    """
    Validate the headers of a TSV file to ensure it contains all required columns.
    """
    function_name = inspect.currentframe().f_code.co_name
    # Read only the headers (first row) from the TSV file
    try:
        df = pd.read_csv(input_file, delimiter='\t', encoding=encoding, nrows=0)
        tsv_headers = list(df.columns)

        # Find missing columns
        missing_headers = [header for header in required_headers if header not in tsv_headers]
        
        # Find unexpected columns
        unexpected_headers = [header for header in tsv_headers if header not in required_headers]
        
        if missing_headers:
            log_message(function_name, "ERROR", f"Error: Missing required columns: {missing_headers}")
            return False
        if unexpected_headers:
            log_message(function_name, "ERROR", f"Warning: Unexpected columns present: {unexpected_headers}")
            return False
        
        # Otherwise, return True indicating the headers are valid
        return True
    
    except Exception as e:
        log_message(function_name, "ERROR", f"Error reading the file: {str(e)}")
        return False
    
    
def validate_tsv_columns(file_path, required_headers, encoding="utf-8"):
    """
    Valide chaque colonne du fichier TSV selon des conditions spécifiques.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    with open(file_path, newline='', encoding='iso-8859-1') as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter='\t')
        tsv_headers = reader.fieldnames

        # Vérifier que toutes les colonnes requises sont présentes (normalement pas besoin si vérif du header avant)
        missing_columns = [col for col in required_headers if col not in tsv_headers]
        if missing_columns:
            log_message(function_name, "ERROR", f"Missing columns: {missing_columns}")
            return False

        # Vérification des valeurs présentes dans chaque ligne
        for line_num, row in enumerate(reader, start=2):  # Start=2 car l'en-tête est à la ligne 1
            for col in required_headers:
                if col in row and row[col].strip():  # Vérifier seulement si la valeur est non vide
                    if not validate_column_value(col, row[col]):  # Vérification personnalisée
                        log_message(function_name, "ERROR", f"Valeur invalide dans la colonne '{col}' à la ligne {line_num}: {row[col]}")
                        return False
                
        # Si tout est bon
        log_message(function_name, "INFO", f"File '{file_path}' is valid.")
        return True



def validate_column_value(column_name, value):
    """
    Valide la valeur d'une colonne en fonction de conditions spécifiques.
    """
    # Conditions spécifiques pour certaines colonnes
    if column_name == 'filename':
        return value != ""
    # elif column_name == 'checksum':
    #     return value != ""
    elif column_name == 'file_type':
        allowed_file_types = ['SNV', 'CNV']
        return value in allowed_file_types
    elif column_name == 'date_of_birth':
        try:
            # Vérifier que la date est au format YYYY-MM-DD
            # datetime.strptime(value, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    elif column_name == 'assembly':
        allowed_assemblies = ['GRCh37', 'GRCh38', 'T2T']
        return value in allowed_assemblies
    elif column_name == 'sample':
        return value != ""
    elif column_name == 'bam_path':
        if value != "":
            return True
            # return os.path.exists(value)  # pb de path Windows/Linux
        else:
            return False
    elif column_name == 'family_id':
        return value != ""
    elif column_name == 'person_id':
        return value != ""
    elif column_name == 'sample':
        allowed_sex = ['female', 'male', 'unknown']
        return value in allowed_sex
    elif column_name == 'is_affected':
        allowed_is_affected = ['0', '1']
        return str(value) in allowed_is_affected
    elif column_name == 'interpretation_title':
        return value != ""
    elif column_name == 'is_index':
        allowed_is_index = ['0', '1']
        return str(value) in allowed_is_index
    elif column_name == 'project':
        return value != ""
    else:
        return True  # Si aucune condition spécifique n'est définie, accepter par défaut
    
    
    
    
    
def parse_date(date_str):
    """
    Parses a date string in the format 'DD/MM/YYYY' and returns it in the format 'YYYY-MM-DD'.
    
    """
    # Define the expected date format
    date_format = '%d/%m/%Y'
    try:
        dob_obj = datetime.strptime(date_str, date_format)
        # Convert the parsed date object to the desired output format
        formatted_date = dob_obj.strftime("%Y-%m-%d")
        return formatted_date
    except ValueError:
        return ""
    

def remove_empty_keys(d):
    """
    Supprime les clés avec des valeurs vides (None ou "") dans un dictionnaire.

    """    
    if not isinstance(d, dict):
        return d  # Si ce n'est pas un dict, retourner la valeur telle quelle
    cleaned_dict = {}
    for k, v in d.items():
        if isinstance(v, dict):
            # Appliquer la fonction récursivement sur les sous-dictionnaires
            nested_dict = remove_empty_keys(v)
            if nested_dict:  # Ajouter le sous-dictionnaire seulement s'il n'est pas vide
                cleaned_dict[k] = nested_dict
        elif v not in [None, ""]:  # Filtrer les valeurs vides
            cleaned_dict[k] = v
    return cleaned_dict



def write_JSON_file(data_dict, key_name, output_file, encoding='utf-8'):
    """
    Writes the values of a dictionary to a JSON file under a specified key.
    
    """
    function_name = inspect.currentframe().f_code.co_name
    # Fonction pour écrire le dictionnaire de données dans un fichier JSON
    with open(output_file, 'w', encoding=encoding) as f:
        json.dump({key_name: list(data_dict.values())}, f, ensure_ascii=False, indent=4)
    log_message(function_name, "SUCCESS", f"Write file: {output_file}")
    
    
    
def md5(filepath):
    """
    Computes the MD5 hash of a file.
    
    """
    function_name = inspect.currentframe().f_code.co_name
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        error_msg = f"File not found: {filepath}"
        log_message(function_name, "ERROR", error_msg)
        raise
    except IOError as e:
        error_msg = f"IO error while reading {filepath}: {e}"
        log_message(function_name, "ERROR", error_msg)
        raise
    except Exception as e:
        error_msg = f"Unexpected error while computing MD5 for {filepath}: {e}"
        log_message(function_name, "ERROR", error_msg)
        raise


def get_or_compute_checksum(sample_data, sample_id, biofiles_directory=None):
    """
    Récupère le checksum d'un fichier depuis `sample_data` ou le calcule si nécessaire.
    
    """
    function_name = inspect.currentframe().f_code.co_name
    checksum = sample_data.get("checksum")

    if not checksum:
        filename = sample_data.get("filename")
        log_message(function_name, "WARNING", f"Sample: {sample_id} - Checksum not found for file: {filename}")

        if biofiles_directory:
            log_message(function_name, "WARNING", f"Sample: {sample_id} - Calculating MD5 for file: {filename}")
            try:
                file_path = os.path.join(biofiles_directory, filename)
                checksum = md5(file_path)
            except Exception as e:
                log_message(function_name, "ERROR", f"{e}.")
                raise
        else:
            log_message(function_name, "ERROR", f"Sample: {sample_id} - Can't calculate MD5 for file: {filename}.")
            raise ValueError(f"Can't calculate MD5 for file: {filename}.")

    return checksum



# Charger un fichier json
def load_data_from_config_file(file):
    """Charge la configuration depuis un fichier JSON."""
    function_name = inspect.currentframe().f_code.co_name
    try: 
        if not os.path.exists(file):
            raise FileNotFoundError(f"File not found: {file}.")
        log_message(function_name, "INFO", f"Import 'excludeColumns' from file: {os.path.abspath(file)}")
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        log_message(function_name, "WARNING", f"File not found: {file}.")
        return ""
