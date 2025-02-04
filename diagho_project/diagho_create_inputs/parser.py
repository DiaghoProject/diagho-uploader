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
import logging

from subprocess import Popen, PIPE
from pandas import DataFrame
from pathlib import Path
from dateutil import parser
from datetime import datetime

import yaml

# Logs
from common.logger_config import logger2

from common.file_utils import *

from diagho_create_inputs.utils import *
from common.config_loader import load_configuration



# Pour encodage fichiers de sortie
sys.getdefaultencoding()






def create_json_files(input_file, output_file, output_prefix="tmp"):
    """
    Creation of all JSON files.

    Args:
        input_file (str): TSV file
        output_file (str): final JSON file
        output_prefix (str): prefixe pour les fichiers (optionnal)
    """
    
    
    # Charger la configuration depuis config.yaml
    config_file = "config/config.yaml"
    with open(config_file, "r") as file:
        config = yaml.safe_load(file)
        
    # Load settings
    log_message("LOAD_CONFIGURATION", "INFO", f"Load config_file: {config_file}")
    settings = load_configuration(config)
    path_biofiles = settings["path_biofiles"]
        

    logger2.info(f"-------------------------------------------------------------------------------")
    logger2.info(f"Input file: {input_file}")
    
    
    
    # Définir les fichiers JSON à créer
    output_directory = os.path.dirname(output_file)
    
    output_json_simple = os.path.join(output_directory, output_prefix + ".simple.json")
    output_file_families = os.path.join(output_directory, output_prefix + ".families.json")
    output_file_biofiles = os.path.join(output_directory, output_prefix + ".biofiles.json")
    output_file_interpretations = os.path.join(output_directory, output_prefix + ".interpretations.json")
    
    
    try:
        # Test si file_input existe
        if not os.path.exists(input_file):
            log_message("CREATE_JSON", "ERROR", f"File not found: {input_file}")
            raise FileNotFoundError(f"File not found: {input_file}.")
        # Si le fichier existe : oncontinue les traitements
    
        # Créer le JSON simple
        try:
            diagho_tsv2json(input_file, output_json_simple)
            
        except Exception as e:
            log_message("CREATE_JSON", "ERROR", f"Erreur détectée dans 'diagho_tsv2json': {e}.")
            exit(1)
        
        
        # Créer les 3 fichiers JSON
        
        # Familles
        try:
            diagho_create_json_families(output_json_simple, output_file_families)
        except Exception as e:
            log_message("CREATE_JSON", "ERROR", f"Erreur détectée dans 'diagho_create_json_families': {e}.")
            exit(1)
        
        # Biofiles
        try:
            diagho_create_json_biofiles(output_json_simple, output_file_biofiles, path_biofiles)
        except Exception as e:
            log_message("CREATE_JSON", "ERROR", f"Erreur détectée dans 'diagho_create_json_biofiles': {e}.")
            exit(1)
            
        # Interpretations
        try:
            diagho_create_json_interpretations(output_json_simple, output_file_interpretations, path_biofiles)
        except Exception as e:
            log_message("CREATE_JSON", "ERROR", f"Erreur détectée dans 'diagho_create_json_interpretations': {e}.")
            exit(1)
        
        # Combine the 3 JSON files
        combine_json_files(output_file_families, output_file_biofiles, output_file_interpretations, output_file)
    
    except FileNotFoundError:
        log_message("CREATE_JSON", "ERROR", f"File not found: {input_file}. Exit.")
        
        
        
        

    
    

    # # Remove tmp JSON files
    # print(f"\nRemove tmp JSON files" )
    # os.remove(file_json_simple)
    # os.remove(output_file_families)
    # os.remove(output_file_biofiles)
    # os.remove(output_file_interpretations)





def diagho_tsv2json(input_file, output_file, lowercase_keys=False, encoding='latin1'):
    """
    Converts a TSV (Tab-Separated Values) file to a JSON file.
    
    """
    log_message("TSV2JSON", "INFO", f"Processing input_file: {input_file}")
    try:
        remove_trailing_empty_lines(input_file, encoding='latin1')
        
        # Validate header
        required_headers = ['filename', 'checksum', 'file_type', 'sample', 'bam_path', 'family_id', 'person_id', 'father_id','mother_id', 'sex', 'is_affected', 'last_name', 'first_name', 'date_of_birth', 'hpo', 'interpretation_title', 'is_index', 'project', 'assignee', 'priority', 'person_note', 'assembly', 'data_title']

        # Validate TSV header
        if not validate_tsv_headers(input_file, required_headers):
            log_message("VALIDATE_TSV_HEADER", "ERROR", f"Invalid header. Exit.")
            raise ValueError(f"Invalid header in file: {input_file}")
        
        if not validate_tsv_columns(input_file, required_headers):
            log_message("VALIDATE_TSV_HEADER", "ERROR", f"Invalid values in file. Exit.")
            raise ValueError(f"Invalid values in file: {input_file}")

        # Read TSV file into a pandas DataFrame
        df = pd.read_csv(input_file, delimiter='\t', encoding=encoding, dtype=str)  # dtype=str to keep empty fields
        
        # Keep empty strings
        df = df.where(pd.notnull(df), "")

        # Convert DataFrame to dictionary
        dict_final = df.to_dict(orient='index')
        
        # Write the resulting dictionary to the output JSON file
        with open(output_file, 'w', encoding='utf-8') as out_file:
            json.dump(dict_final, out_file, indent=4, ensure_ascii=False)
        log_message("TSV2JSON", "SUCCESS", f"Write file: {output_file}")

    except ValueError as e:
        log_message("TSV2JSON", "ERROR", f"Error: {str(e)}")
        raise



# Create JSON file : FAMILIES
def diagho_create_json_families(input_file, output_file):
    """
    Crée un fichier JSON contenant les informations sur les familles.

    """
    log_message("JSON_FAMILIES", "INFO", "---------- Start create JSON file for FAMILIES.")
    # Charger les données à partir du fichier JSON d'entrée
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Initialisation des structures de données
    dict_families = {}
    dict_index_case_by_family = {}

    # Parcourir chaque échantillon (sample) dans les données
    for index, sample_data in data.items():
        
        # Récupérer les informations du sample
        sample_id = sample_data.get('sample', '')
        person_id = sample_data.get('person_id', '')
        family_id = sample_data.get('family_id', '')
        sex = sample_data.get('sex', '').lower()
        last_name = sample_data.get('last_name', '')
        first_name = sample_data.get('first_name', '')
        date_of_birth = parse_date(sample_data.get('date_of_birth', ''))  # mettre la date au bon format
        person_note = sample_data.get('person_note', '')
        
        # id des parents
        mother_id = sample_data.get('mother_id', '')
        father_id = sample_data.get('father_id', '')
        
        # Gestion du cas index
        is_index = sample_data.get('is_index', False)
        if is_index:
            # on récupère le person_id du cas index et on l'ajoute au dict_index_case_by_family
            index_case_id = person_id
            dict_index_case_by_family[family_id] = index_case_id

        # Créer le dictionnaire représentant la personne
        dict_person = {
            "identifier": person_id,
            "sex": sex,
            "firstName": first_name,
            "lastName": last_name,
            "birthday": date_of_birth,
            "motherIdentifier": mother_id,
            "fatherIdentifier": father_id,
            "note": person_note
        }

        # Supprimer les valeurs vides du dictionnaire de la personne
        dict_person = remove_empty_keys(dict_person)

        # Créer ou mettre à jour la famille dans le dictionnaire des familles
        # Vérifier si la famille existe déjà
        if family_id in dict_families:
            persons = dict_families[family_id]["persons"]
            # Vérifier si la personne avec cet 'identifier' existe déjà, si elle n'existe pas, on l'ajoute
            if not any(person["identifier"] == dict_person["identifier"] for person in persons):
                dict_families[family_id]["persons"].append(dict_person)
                log_message("JSON_FAMILIES", "INFO", f"Existing family: {family_id} + Add person: {person_id}")
        else:
            # Si la famille n'existe pas, on la crée avec cette personne
            dict_families[family_id] = {
                "identifier": family_id,
                "persons": [dict_person]
                }
            log_message("JSON_FAMILIES", "INFO", f"Create family: {family_id} + Add person: {person_id}")

    # Écrire le fichier JSON final
    write_JSON_file(dict_families, "families", output_file)
    
    
def diagho_create_json_biofiles(input_file, output_file, biofiles_directory=None):
    """
    Crée un fichier JSON contenant les informations sur les fichiers Biofiles et les échantillons associés.

    """
    log_message("JSON_BIOFILES", "INFO", "---------- Start create JSON file for BIOFILES.")
    # Charger les données d'entrée depuis le fichier JSON
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Initialisation des structures de données
    dict_biofiles = {}

    # Pour chaque échantillon dans les données
    for index, sample_data in data.items():

        # Récupérer les informations du sample
        sample_id = sample_data.get('sample', '')
        person_id = sample_data.get('person_id', '')
        family_id = sample_data.get('family_id', '')
        bam_path = sample_data.get('bam_path', '')
        assembly = sample_data.get('assembly', '')
        filename = sample_data.get('filename', '')
        
        
        # Récupère le checksum du fichier d'entrée ou le calcule si non renseigné et si le dossier des biofiles est fourni
        checksum = get_or_compute_checksum(sample_data, sample_id, biofiles_directory)
        
        log_message("JSON_BIOFILES", "INFO", f"Sample: {sample_id} - Filename: {filename} - Checksum: {checksum}")

        # Créer le dictionnaire pour le sample
        dict_sample = {
            "name": sample_id,
            "person": person_id,
            "bamPath": bam_path
        }
        # Supprimer les valeurs vides du dictionnaire
        dict_sample = remove_empty_keys(dict_sample)

        # Si le biofile n'est pas encore dans le dict_biofiles, on l'ajoute
        if filename not in dict_biofiles:
            dict_biofiles[filename] = {
                "filename": filename,
                "samples": [dict_sample],
                "checksum": checksum,
                "assembly": assembly
            }
        else:
            # Si le biofile est existant : ajouter le sample au biofile
            dict_biofiles[filename]["samples"].append(dict_sample)

    # Écrire le résultat dans un fichier JSON de sortie
    write_JSON_file(dict_biofiles, "files", output_file)


def diagho_create_json_interpretations(input_file, output_file, biofiles_directory):
    """
    Crée un fichier JSON contenant les informations d'interprétation pour chaque famille.

    Parameters:
    - input_file: chemin du fichier JSON d'entrée contenant les informations des échantillons
    - output_file: chemin du fichier JSON de sortie à générer
    - vcfs_directory: répertoire où se trouvent les fichiers VCF

    """
    log_message("JSON_INTERPRETATIONS", "INFO", "---------- Start create JSON file for INTERPRETATIONS.") 
    # Charger les données d'entrée depuis le fichier JSON
    with open(input_file, 'r') as f:
        data = json.load(f)

    # Initialisation du dictionnaires d'interprétations
    dict_interpretations = {}

    # Pour chaque échantillon dans les données
    for index, sample_data in data.items():

        # Récupérer les informations du sample
        sample_id = sample_data.get('sample', '')
        is_index = sample_data.get('is_index', '')
        index_id = sample_data.get('person_id', '') if (is_index and is_index != "0") else ""
        biofile_type = sample_data.get('file_type', None)
        if not biofile_type:
            log_message("JSON_INTERPRETATION", "WARNING", f"Biofile_type is empty for sample: {sample_id} --> Default to 'SNV'.")
            biofile_type = "SNV"
        project = sample_data.get('project', '').lower().replace(" ", "-")
        priority = sample_data.get('priority', 2)
        is_affected = sample_data.get('is_affected', '')
        is_affected_boolean = (is_affected == "Affected" or str(is_affected) == "1" or is_affected == "true"  or is_affected == "True")
        assignee = sample_data.get('assignee', '')
        interpretation_title = sample_data.get('interpretation_title', '')
        data_title = sample_data.get('data_title', '')
        
        # Récupère le checksum du fichier d'entrée ou le calcul si non renseigné
        # checksum = sample_data.get('checksum') or md5(os.path.join(biofiles_directory, sample_data.get('filename')))
        checksum = get_or_compute_checksum(sample_data, sample_id, biofiles_directory)

        # Crée le dictionnaire des interprétations
        interpretation = {
                "indexCase": index_id,
                "project": project,
                "title": interpretation_title,
                "assignee": assignee,
                "priority": priority,
            }
        
        v_data_tuple = (data_title or biofile_type, biofile_type, {
            "name": sample_id,
            "isAffected": is_affected_boolean,
            "checksum": checksum,
        })

        if interpretation_title not in dict_interpretations:
            dict_interpretations[interpretation_title] = interpretation
            dict_interpretations[interpretation_title]["datas_tuples"] = [v_data_tuple]
            
            log_message("JSON_INTERPRETATIONS", "INFO", f"New interpretation {interpretation_title}, with sample: {sample_id}")
        else:
            log_message("JSON_INTERPRETATIONS", "INFO", f"Existing interpretation {interpretation_title}, with sample: {sample_id}")
            # Mets à jour les informations ou échoue en cas d'incohérences
            for key, value in dict_interpretations[interpretation_title].items():
                if key == "datas_tuples":
                    continue

                if key == "priority":
                    if value < interpretation[key]:
                        dict_interpretations[interpretation_title][key] = interpretation[key]
                    continue

                if not value and interpretation[key]:
                    dict_interpretations[interpretation_title][key] = interpretation[key]
                
                if value and interpretation[key] and value != interpretation[key]:
                    raise ValueError(f"Conflict detected for '{key}' of '{interpretation_title}': Existing value: '{value}', New value: '{interpretation[key]}'")

            dict_interpretations[interpretation_title]["datas_tuples"].append(v_data_tuple)

    for interpretation in dict_interpretations.values():
        # Vérifie qu'il y a bien un cas index
        if not interpretation["indexCase"]:
            error_message = str(f"No Index case specified for :", interpretation["title"])
            log_message("JSON_INTERPRETATIONS", "ERROR", error_message)
            raise ValueError(f"No Index case specified for", interpretation["title"])

        datas_dict = {}

        # Créer les objets sample
        for title, file_type, sample in interpretation["datas_tuples"]:
            composite_key = (title, file_type)
            
            # Charger les colonnes à exclure à partir d'un json à part
            config_exclude_columns = load_file("diagho_create_inputs/config_interpretations.json")
            exclude_columns = config_exclude_columns.get("excludeColumns", [])

            if composite_key not in datas_dict:
                datas_dict[composite_key] = {
                    "title": title,
                    "type": file_type,
                    "samples": [],
                    "excludeColumns" : exclude_columns,
                    "pretags": []
                }
                
            # Ajout des pretags en fonction du projet --> enlever depuis màj diagho
            # set_pretags_by_project(interpretation, datas_dict, composite_key)
            
            datas_dict[composite_key]["samples"].append(sample)

        del interpretation["datas_tuples"]
        interpretation["datas"] = list(datas_dict.values())
        
        # Supprimer 'pretags' si aucun pretag
        for data in interpretation["datas"]:
            if "pretags" in data:
                if all(not tag.get("tag") and not tag.get("filter") for tag in data["pretags"]):
                    del data["pretags"]
    
    # Écrire le résultat dans un fichier JSON de sortie
    dict_interpretations = remove_empty_keys(dict_interpretations)    
    write_JSON_file(dict_interpretations, "interpretations", output_file)




def combine_json_files(file_families, file_vcfs, file_interpretations, output_file):

    # Lire le contenu des trois fichiers JSON
    with open(file_families, 'r') as f1:
        data1 = json.load(f1)
    with open(file_vcfs, 'r') as f2:
        data2 = json.load(f2)
    with open(file_interpretations, 'r') as f3:
        data3 = json.load(f3)

    # Combiner les données des trois fichiers en un seul dictionnaire
    combined_data = {**data1, **data2, **data3}

    ## Ecrire le JSON
    combined_data = remove_empty_keys(combined_data)
    with open(output_file,'w', encoding='utf-8') as formatted_file:
        json.dump(combined_data, formatted_file, ensure_ascii=False, indent=4)
    log_message("COMBINE_JSON_FILES", "SUCCESS", f"Write combined file: {output_file}")
