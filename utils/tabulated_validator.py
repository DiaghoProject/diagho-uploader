import csv
import datetime
import inspect
import json
import os
from datetime import datetime
import shutil
import chardet
import pandas as pd

from utils.logger import *
from utils.file import md5

class TSVValidationError(Exception):
    """Exception personnalisée pour les erreurs de validation TSV."""
    pass

        
def remove_trailing_empty_lines(file_path, encoding):
    """
    Removes trailing empty lines from a text file.
    """
    function_name = inspect.currentframe().f_code.co_name

    # Lire le fichier et sauvegarder les lignes non vides
    with open(file_path, 'r', encoding=encoding) as file:
        lines = [line for line in file if line.strip()]
    
    # Réécrire le fichier sans les lignes vides à la fin
    with open(file_path, 'w', encoding=encoding) as file:
        file.writelines(lines)
            
    
def validate_tsv_columns(file_path, required_headers):
    """
    Valide chaque colonne du fichier TSV selon des conditions spécifiques.
    """
    function_name = inspect.currentframe().f_code.co_name
        
    # Lire le fichier TSV
    df = pd.read_csv(file_path, sep="\t", encoding=detect_encoding(file_path), dtype=str)
            
    # Vérifier la présence des colonnes requises
    missing_columns = [col for col in required_headers if col not in df.columns]
    if missing_columns:
        log_message(function_name, "ERROR", f"Missing columns: {missing_columns}")
        raise TSVValidationError(f"Missing columns: {missing_columns}")
    
    # Vérification des valeurs présentes dans chaque ligne
    for col in required_headers:
        invalid_rows = df[df[col].apply(lambda x: not validate_column_value(col, str(x)))]  # Convertir en str pour éviter les NaN
        if not invalid_rows.empty:
            row_num = invalid_rows.index[0] + 2  # Ligne réelle (+2 car pandas indexe à partir de 0 et l'en-tête est à la ligne 1)
            value = invalid_rows[col].iloc[0]
            message = f"Valeur invalide dans la colonne '{col}' à la ligne {row_num}: {value}"
            log_message(function_name, "ERROR", message)
            raise TSVValidationError(message)
        
    log_message(function_name, "DEBUG", f"File '{file_path}' is valid.")
    return True

def validate_column_value(column_name, value):
    """
    Valide la valeur d'une colonne en fonction de conditions spécifiques.
    """
    # Conditions spécifiques pour certaines colonnes
    if column_name == 'filename':
        return value != ""
    elif column_name == 'file_type':
        allowed_file_types = ['SNV', 'CNV']
        return value in allowed_file_types
    elif column_name == 'assembly':
        allowed_assemblies = ['GRCh37', 'GRCh38', 'T2T']
        return value in allowed_assemblies
    elif column_name == 'sample':
        return value != ""
    elif column_name == 'family_id':
        return value != ""
    elif column_name == 'person_id':
        return value != ""
    elif column_name == 'sex':
        allowed_sex = ['female', 'male', 'unknown', 'F', 'M']
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
        return True  # Si aucune condition spécifique n'est définie : true
    
    
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
            # Si sous-dictionnaire : appliquer la fonction récursivement sur les sous-dictionnaires
            nested_dict = remove_empty_keys(v)
            if nested_dict:  # Ajouter le sous-dictionnaire seulement s'il n'est pas vide
                cleaned_dict[k] = nested_dict
        elif v not in [None, ""]:  # Filtrer les valeurs vides
            cleaned_dict[k] = v
    return cleaned_dict


def get_or_compute_checksum(sample_data, sample_id, biofiles_directory=None):
    """
    Récupère le checksum d'un fichier depuis 'sample_data' ou le calcule si nécessaire.
    """
    function_name = inspect.currentframe().f_code.co_name
    checksum = sample_data.get("checksum")

    if not checksum:
        filename = sample_data.get("filename")
        log_message(function_name, "INFO", f"Sample: {sample_id} - Checksum not found for file: {filename}")

        if biofiles_directory:
            log_message(function_name, "DEBUG", f"Sample: {sample_id} - Calculating MD5 for file: {filename}")
            try:
                file_path = os.path.join(biofiles_directory, filename)
                checksum = md5(file_path)
            except Exception as e:
                log_message(function_name, "ERROR", f"Function '{function_name}': can't calculate MD5 for file: {filename}: {e}")
                raise ValueError(f"Function '{function_name}': can't calculate MD5 for file: {filename}: {e}.")
        else:
            log_message(function_name, "ERROR", f"Sample: {sample_id} - Can't calculate MD5 for file: {filename}")
            raise ValueError(f"Can't calculate MD5 for file: {filename}.")

    return checksum



def detect_encoding(file_path):
    """
    Detection of the encoding of the file. If 'latin-1' convert it to 'utf-8'.
    """
    function_name = inspect.currentframe().f_code.co_name
    logging.getLogger("chardet").setLevel(logging.INFO)
    with open(file_path, "rb") as f:
        raw_data = f.read(4096)
        result = chardet.detect(raw_data)
        encoding = result["encoding"]
        
    log_message(function_name, "DEBUG", f"Encoding detected: {encoding}.")
    return encoding
    


def detect_and_convert_tsv(file_path):
    """
    Detection of the encoding of the file. If 'latin-1' convert it to 'utf-8'.
    """
    function_name = inspect.currentframe().f_code.co_name
    logging.getLogger("chardet").setLevel(logging.INFO)
    
    with open(file_path, "rb") as f:
        raw_data = f.read(4096)
        result = chardet.detect(raw_data)
        encoding = result["encoding"]
    
    # Si encodage = ISO-8859-1 ou latin-1 : conversion en UTF-8
    if encoding and encoding.lower() in ["iso-8859-1", "latin-1"]:
        log_message(function_name, "DEBUG", f"Encoding detected: {encoding}, need to encode in 'UTF-8'.")
        temp_file_path = file_path + ".tmp"
        with open(file_path, "r", encoding="ISO-8859-1") as f_in, open(temp_file_path, "w", encoding="utf-8") as f_out:
            for line in f_in:
                f_out.write(line)
        # Remplace le fichier original par le nouveau fichier
        shutil.move(temp_file_path, file_path)
        log_message(function_name, "DEBUG", f"File '{file_path}' has been converted in 'UTF-8'.")
        return file_path
    else:
        return file_path