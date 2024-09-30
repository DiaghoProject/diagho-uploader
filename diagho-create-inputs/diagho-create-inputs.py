#!/usr/bin/python3

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
    parser.add_argument('--biofiles_directory', type=str, help="Path to the Biofiles directory.")
    args = parser.parse_args()

    input_file = args.input_file
    output_directory = args.output_directory
    output_prefix = args.output_prefix
    biofiles_directory = args.biofiles_directory

    ## TODO #21 En fonction du type de fichier en entrée : créer le JSON simple
    input_file_type = get_file_type(input_file)
    if input_file_type == 'tsv':
        # STEP 1 : Create simple JSON file
        print(f"Create simple JSON file" )
        file_json_simple = os.path.join(output_directory, output_prefix + ".simple.json")
        print(f"Write file: {file_json_simple}" )
        diagho_tsv2json(input_file, file_json_simple)

    else:
        # le fichier d'input est le JSON simple
        file_json_simple = input_file

    # STEP 2 : Create each JSON files
    # Families
    print(f"\nCreate JSON file for families" )
    output_file_families = os.path.join(output_directory, output_prefix + ".families.json")
    diagho_create_json_families(file_json_simple, output_file_families)

    # Biofiles
    print(f"\nCreate JSON file for biofiles" )
    output_file_biofiles = os.path.join(output_directory, output_prefix + ".biofiles.json")
    diagho_create_json_biofiles(file_json_simple, output_file_biofiles, biofiles_directory)

    # Interpretations
    print(f"\nCreate JSON file for interpretations" )
    output_file_interpretations = os.path.join(output_directory, output_prefix + ".interpretations.json")
    diagho_create_json_interpretations(file_json_simple, output_file_interpretations, biofiles_directory)


    # STEP 3 : Combine the 3 JSON files
    print(f"\nCreate combined JSON file" )
    output_file = os.path.join(output_directory, output_prefix + ".FINAL.json")
    combine_json_files(output_file_families, output_file_biofiles, output_file_interpretations, output_file)

    # STEP 4 : Remove tmp JSON files
    print(f"\nRemove tmp JSON files" )
    os.remove(file_json_simple)
    os.remove(output_file_families)
    os.remove(output_file_biofiles)
    os.remove(output_file_interpretations)




# diagho_tsv2json
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

        # Validate header
        required_headers = ['filename', 'checksum', 'file_type', 'sample', 'bam_path', 'family_id', 'person_id', 'father_id',
                    'mother_id', 'sex', 'is_affected', 'last_name', 'first_name', 'date_of_birth', 'hpo',
                    'interpretation_title', 'is_index', 'project', 'assignee', 'priority', 'filter_tag', 'note', 'assembly', 'data_title']
        if validate_tsv_headers(input_file, required_headers):
            print("TSV headers are valid.")
        else:
            print("TSV headers are invalid.")

        # Read TSV file into a pandas DataFrame
        df = pd.read_csv(input_file, delimiter='\t', encoding=encoding, dtype=str)  # dtype=str to keep empty fields


        # Replace empty strings with None (optional, can be skipped if you prefer empty strings)
        df = df.where(pd.notnull(df), "")

        print(df)

        # Convert DataFrame to dictionary with sample_id as key
        # dict_final = df.set_index('sample', drop=False).to_dict(orient='index')
        dict_final = df.to_dict(orient='index')
        pretty_print_json_string(dict_final)

        # Write the resulting dictionary to the output JSON file
        with open(output_file, 'w', encoding='utf-8') as output_file:
            json.dump(dict_final, output_file, indent=4, ensure_ascii=False)

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

        # Gestion des caractères spéciaux dans le prénom
        # v_first_name = replace_special_characters(v_first_name)

        # Date de naissance
        dob_str = sample_data.get('date_of_birth', '')
        v_date_of_birth = parse_date(dob_str)  # Fonction pour parser la date

        # id des parents
        v_mother_id = sample_data.get('mother_id', '')
        v_father_id = sample_data.get('father_id', '')

        # cas index
        v_is_index = sample_data.get('is_index', False)

        # Gestion du cas index
        if v_is_index:
            # on récupère le person_id du cas index et on l'ajoute au dict_index_case_by_family
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
        dict_person = remove_empty_keys(dict_person)

        # Créer ou mettre à jour la famille dans le dictionnaire des familles

        # Vérifier si la famille existe déjà
        if v_family_id in dict_families:
            persons = dict_families[v_family_id]["persons"]

            # Vérifier si la personne avec cet 'identifier' existe déjà
            if not any(person["identifier"] == dict_person["identifier"] for person in persons):
                dict_families[v_family_id]["persons"].append(dict_person)
        else:
            # Si la famille n'existe pas, on la crée avec cette personne
            dict_families[v_family_id] = {
                "identifier": v_family_id,
                "persons": [dict_person]
                }

    # Écrire le fichier JSON final
    write_final_JSON_file(dict_families, "families", output_file)


# Create JSON file : FILES
def diagho_create_json_biofiles(input_file, output_file, biofiles_directory):
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
    dict_biofiles = {}

    # Pour chaque échantillon dans les données
    for sample_id, sample_data in data.items():

        # Récupérer les informations du sample
        v_sample_id = sample_data.get('sample', '')
        v_person_id = sample_data.get('person_id', '')
        v_family_id = sample_data.get('family_id', '')
        v_bam_path = sample_data.get('bam_path', '')
        assembly = sample_data.get('assembly', '')
        filename = sample_data.get('filename', '')
        # Récupère le checksum du fichier d'entrée ou le calcul si non renseigné
        checksum = sample_data.get('checksum') or md5(os.path.join(biofiles_directory, sample_data.get('filename')))

        # Créer le dictionnaire pour le sample
        dict_sample = {
            "name": v_sample_id,
            "person": v_person_id,
            "bamPath": v_bam_path
        }

        # Supprimer les valeurs vides du dictionnaire
        dict_sample = remove_empty_keys(dict_sample)

        # Si le biofile n'est pas encore dans le dict_biofiles
        if filename not in dict_biofiles:
            dict_biofiles[filename] = {
                "filename": filename,
                "samples": [dict_sample],
                "checksum": checksum,
                "assembly": assembly
            }
        else:
            # Ajouter le sample au fichier VCF existant
            dict_biofiles[filename]["samples"].append(dict_sample)

    # Écrire le résultat dans un fichier JSON de sortie
    write_final_JSON_file(dict_biofiles, "files", output_file)


# Create JSON file : INTERPRETATION
def diagho_create_json_interpretations(input_file, output_file, biofiles_directory):
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

    # Initialisation du dictionnaires d'interprétations
    dict_interpretations = {}

    # Pour chaque échantillon dans les données
    for sample, sample_data in data.items():

        # Récupérer les informations du sample
        v_sample_id = sample_data.get('sample', '')
        v_person_id = sample_data.get('person_id', '')
        v_is_index = sample_data.get('is_index', 0)
        v_biofile_type = sample_data.get('file_type', "SNV")
        v_project = sample_data.get('project', '')
        v_priority = sample_data.get('priority', '')
        v_is_affected = sample_data.get('is_affected', '')
        v_is_affected_boolean = (v_is_affected == "Affected" or str(v_is_affected) == "1" or v_is_affected == "true"  or v_is_affected == "True")
        v_assignee = sample_data.get('assignee', '')
        v_interpretation_title = sample_data.get('interpretation_title', '')
        v_data_title = sample_data.get('data_title', '')
        # Récupère le checksum du fichier ou le calcul si non renseigné
        v_checksum = sample_data.get('checksum') or md5(os.path.join(biofiles_directory, sample_data.get('filename')))

        v_interpretation = {
                "indexCase": v_person_id if v_is_index else "",
                "project": v_project,
                "title": v_interpretation_title,
                "assignee": v_assignee,
                "priority": v_priority,
            }

        v_data_tuple = (v_data_title or v_biofile_type, v_biofile_type, {
            "sample": v_sample_id,
            "isAffected": v_is_affected_boolean,
            "checksum": v_checksum,
        })

        if v_interpretation_title not in dict_interpretations:
            dict_interpretations[v_interpretation_title] = v_interpretation
            dict_interpretations[v_interpretation_title]["datas_tuples"] = [v_data_tuple]
        else:
            # Mets à jour les informations ou échoue en cas d'incohérences
            for key, value in dict_interpretations[v_interpretation_title].items():
                if key == "datas_tuples":
                    continue

                current_value = dict_interpretations[v_interpretation_title][key]
                
                if not current_value and value:
                    dict_interpretations[v_interpretation_title][key] = value
                
                if current_value and current_value != value:
                    raise ValueError(f"Conflict detected for '{key}': Existing value: {current_value}, New value: {value}")

            dict_interpretations[v_interpretation_title]["datas_tuples"].append(v_data_tuple)

    for interpretation in dict_interpretations.values():
        # Vérifie qu'il y a bien un cas index
        if not interpretation["indexCase"]:
            raise ValueError(f"No Index case specified for '{interpretation.interpretation_title}")

        datas_dict = {}

        # Créer les objets sample
        for title, file_type, sample in interpretation["datas_tuples"]:
            composite_key = (title, file_type)

            if composite_key not in datas_dict:
                datas_dict[composite_key] = {
                    "title": title,
                    "type": file_type,
                    "samples": []
                }
            
            datas_dict[composite_key]["samples"].append(sample)

        del interpretation["datas_tuples"]
        interpretation["datas"] = list(datas_dict.values())


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
    combined_data = remove_empty_keys(combined_data)
    with open(output_file,'w', encoding='utf-8') as formatted_file:
        json.dump(combined_data, formatted_file, ensure_ascii=False, indent=4)
    print(f"Write combined file: {output_file}")

    ## TODO #26 remettre la fonction pour split par famille


if __name__ == '__main__':
    main()
