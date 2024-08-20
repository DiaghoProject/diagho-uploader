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

from subprocess import Popen, PIPE
from pandas import DataFrame
from pathlib import Path
from dateutil import parser


from datetime import datetime

# Import des fonctions
from functions import *


import unicodedata
import sys

sys.getdefaultencoding()
    


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
            


# Create JSON file : FAMILIES
def diagho_create_json_families(input_file, output_file):
    """
    Crée un fichier JSON contenant les informations sur les familles.
    
    Parameters:
    - input_file: chemin du fichier JSON d'entrée contenant les informations des échantillons
    - output_file: chemin du fichier JSON de sortie à générer
    
    """
    # Charger les données à partir du fichier JSON d'entrée
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Initialisation des structures de données
    dict_families = {}
    dict_index_case_by_family = {}
    
    # Parcourir chaque échantillon (sample) dans les données
    for sample_id, sample_data in data.items():
        
        # Récupérer les informations du sample
        v_sample_id = sample_data.get('sample', '')
        v_person_id = sample_data.get('person_id', '')
        v_family_id = sample_data.get('family_id', '')
        v_sex = sample_data.get('sex', '').lower()
        v_last_name = sample_data.get('last_name', '')
        v_first_name = sample_data.get('first_name', '')
        
        ## Gestion des caractères spéciaux dans le prénom
        v_first_name = replace_special_characters(v_first_name)
        
        dob_str = sample_data.get('date_of_birth', '')
        v_date_of_birth = parse_date(dob_str)  # Fonction pour parser la date
        
        v_mother_id = sample_data.get('mother_id', '')
        v_father_id = sample_data.get('father_id', '')
        
        v_is_index = sample_data.get('is_index', False)
        
        # Cas où le patient est tout seul : il est son propre cas index
        if not v_father_id or not v_mother_id:
            v_is_index = True
        
        # Gestion du cas index
        if v_is_index:
            v_index_case_id = v_person_id
            dict_index_case_by_family[v_family_id] = v_index_case_id
        
        v_person_note = sample_data.get('note', '')
        
        # Créer le dictionnaire représentant la personne
        dict_person = {
            "identifier": v_person_id,
            "sex": v_sex,
            "firstName": v_first_name,
            "lastName": v_last_name,
            "birthday": v_date_of_birth,
            "motherIdentifier": v_mother_id,
            "fatherIdentifier": v_father_id,
            "note": v_person_note
        }
        
        # Supprimer les valeurs vides du dictionnaire de la personne
        dict_person = remove_empty_string_values(dict_person)
        
        # Créer ou mettre à jour la famille dans le dictionnaire des familles
        if v_family_id not in dict_families:
            # Créer une nouvelle famille
            dict_families[v_family_id] = {
                "identifier": v_family_id,
                "persons": [dict_person]
            }
        else:
            # Ajouter la personne à une famille existante
            dict_families[v_family_id]["persons"].append(dict_person)
    
    # Écrire le fichier JSON final
    write_final_JSON_file(dict_families, "families", output_file)


# Create JSON file : FILES
def diagho_create_json_files(input_file, output_file, vcfs_directory):
    """
    Crée un fichier JSON contenant les informations sur les fichiers VCF et les échantillons associés.
    
    Parameters:
    - input_file: chemin du fichier JSON d'entrée contenant les informations des échantillons
    - output_file: chemin du fichier JSON de sortie à générer
    - vcfs_directory: répertoire où se trouvent les fichiers VCF
    
    """
    # Charger les données d'entrée depuis le fichier JSON
    with open(input_file, 'r') as f:
        data = json.load(f)
        
    # Initialisation des structures de données
    dict_files = {}
        
    # Pour chaque échantillon dans les données
    for sample_id, sample_info in data.items():
        
        # Récupérer les informations du sample
        v_sample_id = sample_info['sample']
        v_person_id = sample_info['person_id']
        v_family_id = sample_info['family_id']
        
        # Obtenir les informations du fichier VCF correspondant au pattern de la famille
        file_info = get_VCF_info(v_family_id, vcfs_directory)
        
        if file_info:
            filename = file_info['filename']
            path = file_info['path']
            checksum = md5(path)
        else:
            filename = ""
            checksum = ""
        
        # Créer le dictionnaire pour le sample
        dict_sample = {
            "name": v_sample_id,
            "person": v_person_id,
        }
        
        # Si le fichier VCF n'est pas encore dans le dictionnaire des fichiers
        if filename not in dict_files:
            dict_files[filename] = {
                "filename": filename,
                "samples": [dict_sample],
                "checksum": checksum
            }
        else:
            # Ajouter le sample au fichier VCF existant
            dict_files[filename]["samples"].append(dict_sample)
            # Mettre à jour le checksum si nécessaire
            if dict_files[filename]["checksum"] != checksum:
                dict_files[filename]["checksum"] = checksum
                
    # Écrire le résultat dans un fichier JSON de sortie
    write_final_JSON_file(dict_files, "files", output_file)


# Create JSON file : INTERPRETATION
def diagho_create_json_interpretations(input_file, output_file, vcfs_directory):
    """
    Crée un fichier JSON contenant les informations d'interprétation pour chaque famille.
    
    Parameters:
    - input_file: chemin du fichier JSON d'entrée contenant les informations des échantillons
    - output_file: chemin du fichier JSON de sortie à générer
    - vcfs_directory: répertoire où se trouvent les fichiers VCF
    
    """
    # Charger les données d'entrée depuis le fichier JSON
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Initialisation des structures de données
    dict_interpretations = {}
    dict_index_case_by_family = {}
    
    # Pour chaque échantillon dans les données
    for sample, sample_data in data.items():
        
        # Récupérer les informations du sample
        v_sample_id = sample_data.get('sample', '')
        v_person_id = sample_data.get('person_id', '')
        v_family_id = sample_data.get('family_id', '')
        v_mother_id = sample_data.get('mother_id', '')
        v_father_id = sample_data.get('father_id', '')
        v_is_index = sample_data.get('is_index', 0)
        v_person_note = sample_data.get('note', '')
        v_project = sample_data.get('project', '')
        v_priority = sample_data.get('priority', '')
        v_is_affected = sample_data.get('is_affected', '')
        v_is_affected_boolean = (v_is_affected == "Affected" or v_is_affected == 1)
        v_assignee = sample_data.get('assignee', '')
                
        # Cas où le patient est tout seul : il est son propre cas index
        if (v_is_index == "" or v_is_index == 0) and not v_father_id and not v_mother_id:
            v_is_index = 1
        
        # Cas index
        if int(v_is_index) == 1:
            v_index_case_id = v_person_id
            dict_index_case_by_family[v_family_id] = v_index_case_id        
        
        # Obtenir les informations du fichier VCF correspondant au pattern de la famille
        file_info = get_VCF_info(v_family_id, vcfs_directory)
        if file_info:
            filename = file_info['filename']
            path = file_info['path']
            checksum = md5(path)
        else:
            filename = ""
            checksum = ""
        
        # Créer le dictionnaire pour le sample
        dict_sample_interpretation = {
            "name": v_sample_id,
            "isAffected": v_is_affected_boolean,
            "checksum": checksum
        }
        
        # Insertion de la famille dans le dict_interpretations
        if v_family_id not in dict_interpretations:
            dict_interpretations[v_family_id] = {
                "family": v_family_id,
                "indexCase": "",
                "project": "",
                "title": "",
                "assignee": v_assignee,
                "priority": v_priority,
                "datas": []
            }
        
        # Initialiser ou récupérer la liste des samples dans le dict_data
        if not dict_interpretations[v_family_id]['datas']:
            list_samples_interpretation = []
        else:
            for data_entry in dict_interpretations[v_family_id]['datas']:
                list_samples_interpretation = data_entry['samples']
        
        # Ajouter le sample courant à la liste
        list_samples_interpretation.append(dict_sample_interpretation)
                
        # Mettre à jour dict_data avec la liste des samples
        dict_data = {
            "type": 0,  # TODO #1 Modifier le type si besoin 
            "samples": list_samples_interpretation
        }
                
        # Mettre à jour le dict_interpretations avec dict_data
        dict_interpretations[v_family_id]['datas'] = [dict_data]
        
        # Définir le titre de l'interprétation et le cas index
        if v_family_id in dict_index_case_by_family and dict_index_case_by_family[v_family_id]:
            v_index_case = dict_index_case_by_family[v_family_id]
            if v_person_note:
                v_interpretation_title = f"{v_index_case} - {v_person_note}"
            else:
                v_interpretation_title = f"{v_index_case}"
            dict_interpretations[v_family_id]['indexCase'] = v_index_case
            dict_interpretations[v_family_id]['title'] = v_interpretation_title
        
        # Récupérer le slug du projet
        v_project_slug = v_project.lower().replace(" ", "-")
        dict_interpretations[v_family_id]['project'] = v_project_slug
        
        # Supprimer les valeurs de chaîne de caractères vides
        dict_interpretations[v_family_id] = remove_empty_string_values(dict_interpretations[v_family_id])
    
    # Écrire le résultat dans un fichier JSON de sortie
    write_final_JSON_file(dict_interpretations, "interpretations", output_file)


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
    with open(output_file,'w') as formatted_file: 
        json.dump(combined_data, formatted_file, indent=4)
    print(f"Write file: {output_file}")

    
    
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
    
    ####################################################
    # STEP 1
    ####################################################
    ## Créer le json simple
    file_json_simple = os.path.join(output_directory, output_prefix + ".simple.json")
    diagho_tsv2json(input_file, file_json_simple) 
   
    
    ####################################################
    # STEP 2
    ####################################################
    ## Familles
    output_file = os.path.join(output_directory, output_prefix + ".families.json")
    diagho_create_json_families(file_json_simple, output_file)
        
    ## VCF Files
    output_file = os.path.join(output_directory, output_prefix + ".files.json")
    diagho_create_json_files(file_json_simple, output_file, vcfs_directory)
        
    ## Interprétations
    output_file = os.path.join(output_directory, output_prefix + ".interpretations.json")
    diagho_create_json_interpretations(file_json_simple, output_file, vcfs_directory)
    
    
    ####################################################
    # STEP 3
    ####################################################
    # Combine les 3 fichiers JSON
    file_families = os.path.join(output_directory, output_prefix + ".families.json")
    file_vcfs = os.path.join(output_directory, output_prefix + ".files.json")
    file_interpretations = os.path.join(output_directory, output_prefix + ".interpretations.json")
    output_file = os.path.join(output_directory, output_prefix + ".FINAL.json")
    
    combine_json_files(file_families, file_vcfs, file_interpretations, output_file)

if __name__ == '__main__':
    main()
