import inspect
import json
import pandas as pd
import sys
import os
import sys
import yaml

from utils.api import api_get_project_from_slug
from utils.config_loader import load_configuration
from utils.logger import log_message
from utils.mail import *
from utils.tabulated_validator import *

# Pour encodage fichiers de sortie
sys.getdefaultencoding()


def create_json_files(input_file, output_file, diagho_api, settings):
    """
    Creation of the JSON bulkCreation file.

    Args:
        input_file (str): TSV input file
        output_file (str): JSON output file
        diagho_api (dict): endpoints
        
    """
    function_name = inspect.currentframe().f_code.co_name
    
    # Load configuration file
    CONFIG_FILE = os.getenv("CONFIG_PATH", "config/config.yaml")
    with open(CONFIG_FILE, "r") as file:
        config = yaml.safe_load(file)
        
    # Load settings
    settings = load_configuration(config)
    path_biofiles = settings["path_biofiles"]
    recipients = settings["recipients"]
    
    log_message(function_name, "DEBUG", f"Start create_json on file: {input_file}")
    
    # Test if input_file not found
    if not os.path.exists(input_file):
        log_message(function_name, "ERROR", f"File not found: {input_file}")
        raise FileNotFoundError(f"File not found: {input_file}.")
    
    # Initialisation of the initial dictionnary
    data_init = {}
    try:
        data_init = diagho_tsv2json(input_file, settings)
    except Exception as e:
        log_message(function_name, "ERROR", f"{input_file} : Erreur détectée dans 'diagho_tsv2json': {e}.")
        raise
    
    # Initialisation of the final dictionnary
    output_data = {}
    
    kwargs = {
        'data_init': data_init,
        'path_biofiles': path_biofiles,
        'diagho_api': diagho_api,
        'settings': settings
    }
    
    # Sub-dictionnary for families
    try:
        output_data["families"] = get_families(**kwargs)
    except Exception as e:
        log_message(function_name, "ERROR", f"Erreur détectée dans 'get_families': {e}")
        send_mail_alert(recipients, f"Erreur détectée dans 'get_families': \n{e}")
        raise
        
    # Sub-dictionnary for biofiles
    try:
        output_data["files"] = get_biofiles(**kwargs)
    except Exception as e:
        log_message(function_name, "ERROR", f"Erreur détectée dans 'get_biofiles': {e}")
        send_mail_alert(recipients, f"Erreur détectée dans 'get_biofiles': \n{e}")
        raise
            
    # Sub-dictionnary for interpretations
    try:
        output_data["interpretations"] = get_interpretations(**kwargs)
    except Exception as e:
        log_message(function_name, "ERROR", f"Erreur détectée dans 'get_interpretations': {e}")
        send_mail_alert(recipients, f"Erreur détectée dans 'get_interpretations': \n{e}")
        raise
    
    with open(output_file,'w', encoding='utf-8') as formatted_file:
        json.dump(output_data, formatted_file, ensure_ascii=False, indent=4)
    log_message(function_name, "INFO", f"Write JSON: {output_file}")
    

def diagho_tsv2json(input_file, settings, encoding='utf-8'):
    """
    Converts a TSV (Tab-Separated Values) file to a JSON file.
    """
    function_name = inspect.currentframe().f_code.co_name
    recipients = settings["recipients"]
    
    log_message(function_name, "DEBUG", f"Processing input_file: {input_file}")
    
    # Remove empty rows
    remove_trailing_empty_lines(input_file, encoding='utf-8')
    
    # Required columns (parsing will fail if missing one of them)
    required_headers = ['filename', 'checksum', 'file_type', 'sample', 'bam_path', 'family_id', 'person_id', 'father_id','mother_id', 'sex', 'is_affected', 'last_name', 'first_name', 'date_of_birth', 'hpo', 'interpretation_title', 'is_index', 'project', 'assignee', 'priority', 'person_note', 'assembly', 'data_title']

    # Validate values in columns
    try:
        validate_tsv_columns(input_file, required_headers)
    except TSVValidationError as e:
        send_mail_alert(recipients, f"Erreur de validation TSV : \n{e}")
        raise
    except Exception as e:
        send_mail_alert(recipients, f"Fonction '{function_name}': Autre erreur : {e}")
        raise

    # Load TSV file into a pandas DataFrame
    df = pd.read_csv(input_file, delimiter='\t', encoding=encoding, dtype=str)  # dtype=str to keep empty fields
        
    # Keep empty strings
    df = df.where(pd.notnull(df), "")

    # Convert DataFrame to dictionary
    dict_final = df.to_dict(orient='index')
    
    return dict_final


def get_families(**kwargs):
    """
    Get informations about families.

    Returns:
        list: list of dictionnaries (one dict per family)
    """
    function_name = inspect.currentframe().f_code.co_name
    log_message(function_name, "DEBUG", "Start : GET_FAMILIES.")
    
    # Get args
    data = kwargs.get("data_init")

    # Dictionnaries initilisation
    dict_families = {}
    dict_index_case_by_family = {}

    # Foreach sample in data
    for index, sample_data in data.items():
        
        # Get information for the sample
        sample_id = sample_data.get('sample', '')
        person_id = sample_data.get('person_id', '')
        family_id = sample_data.get('family_id', '')
        sex = sample_data.get('sex', '').strip().lower()
        sex = {'m': 'male', 'f': 'female'}.get(sex, sex)
        last_name = sample_data.get('last_name', '')
        first_name = sample_data.get('first_name', '')
        date_of_birth = parse_date(sample_data.get('date_of_birth', ''))  # change date format
        person_note = sample_data.get('person_note', '')
        
        # Parents id
        mother_id = sample_data.get('mother_id', '')
        father_id = sample_data.get('father_id', '')
        
        # Index Case
        is_index = sample_data.get('is_index', False)
        if is_index:
            # Get the person_id of the index case and add it to 'dict_index_case_by_family'
            index_case_id = person_id
            dict_index_case_by_family[family_id] = index_case_id

        # Create dictionnary for the person
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

        # Remove empty key/value
        dict_person = remove_empty_keys(dict_person)

        # Create or update the family in the dictionnary
        if family_id in dict_families:  # Check if family already exists
            persons = dict_families[family_id]["persons"]
            # Check if the current person already exists in the family, if doesn't exist, add it
            if not any(person["identifier"] == dict_person["identifier"] for person in persons):
                dict_families[family_id]["persons"].append(dict_person)
                log_message(function_name, "DEBUG", f"Existing family: {family_id} + Add person: {person_id}")
        else:
            # If the family doesn't exist, create it and add teh current person
            dict_families[family_id] = {
                "identifier": family_id,
                "persons": [dict_person]
                }
            log_message(function_name, "DEBUG", f"Create family: {family_id} + Add person: {person_id}")
    list_families = [value for value in dict_families.values()]
    return list_families
    
    
def get_biofiles(**kwargs):
    """
    Get informations about biofiles and samples.

    Returns:
        list: list of dictionnaries (one dict per biofile)
    """
    function_name = inspect.currentframe().f_code.co_name
    log_message(function_name, "DEBUG", "Start : GET_BIOFILES.")
    
    # Get args
    data = kwargs.get("data_init")
    biofiles_directory = kwargs.get("path_biofiles", None)

    # Initialisation
    dict_biofiles = {}

    # Foreach sample
    for index, sample_data in data.items():

        # Get information of the sample
        sample_id = sample_data.get('sample', '')
        person_id = sample_data.get('person_id', '')
        family_id = sample_data.get('family_id', '')
        bam_path = sample_data.get('bam_path', '')
        assembly = sample_data.get('assembly', '')
        filename = sample_data.get('filename', '')
        
        
        # Get the checksum of the biofile or calculate it
        try:
            checksum = get_or_compute_checksum(sample_data, sample_id, biofiles_directory)
        except Exception as e:
            raise ValueError(e)
        log_message(function_name, "DEBUG", f"Sample: {sample_id} - Filename: {filename} - Checksum: {checksum}")

        # Create dictionnary for the sample
        dict_sample = {
            "name": sample_id,
            "person": person_id,
            "bamPath": bam_path
        }
        # Remove empty key/value
        dict_sample = remove_empty_keys(dict_sample)

        # If the current biofile does not exist in the dict_biofile, add it with the current sample
        if filename not in dict_biofiles:
            dict_biofiles[filename] = {
                "filename": filename,
                "samples": [dict_sample],
                "checksum": checksum,
                "assembly": assembly
            }
        else:
            # If the current biofile already exists, add the current sample
            dict_biofiles[filename]["samples"].append(dict_sample)
    list_biofiles = [value for value in dict_biofiles.values()]
    return list_biofiles


def get_interpretations(**kwargs):
    """
    Get informations about interpretations.

    Returns:
        list: list of dictionnaries (one dict per interpretation)
    """
    function_name = inspect.currentframe().f_code.co_name
    log_message(function_name, "DEBUG", "Start GET_INTERPRETATIONS.")
    
    # Get args
    data = kwargs.get("data_init")
    biofiles_directory = kwargs.get("path_biofiles", None)
    diagho_api = kwargs.get("diagho_api")
    settings = kwargs.get("settings")

    # Initialisation
    dict_interpretations = {}

    # Foreach sample
    for index, sample_data in data.items():

        # Get information for the sample
        sample_id = sample_data.get('sample', '')
        is_index = sample_data.get('is_index', '')
        index_id = sample_data.get('person_id', '') if (is_index and is_index != "0") else ""
        biofile_type = sample_data.get('file_type', None)
        if not biofile_type:
            log_message(function_name, "INFO", f"Biofile_type is empty for sample: {sample_id} --> Default to 'SNV'.")
            biofile_type = "SNV"
        
        # Get project_slug from config file
        project = sample_data.get('project', '')
        project_mapping = settings['projects']
        project_slug = project_mapping.get(project, project.lower().replace(" ", "-"))
        kwargs = {
            "diagho_api": diagho_api,
            "project_slug": project_slug,
            }
        project_exist = api_get_project_from_slug(**kwargs) # return project_slug if project exists
        if not project_exist:
            log_message(function_name, "ERROR", f"Error for sample '{sample_id}': project '{project}' does not exist.")
            raise ValueError(f"Error for sample '{sample_id}': project '{project}' does not exist.")        
        
        priority = sample_data.get('priority', 2)
        is_affected = sample_data.get('is_affected', '')
        is_affected_boolean = (is_affected == "Affected" or str(is_affected) == "1" or is_affected == "true"  or is_affected == "True")
        assignee = sample_data.get('assignee', '')
        interpretation_title = sample_data.get('interpretation_title', '')
        data_title = sample_data.get('data_title', '')
        
        # Get the checksum of the biofile or calculate it
        checksum = get_or_compute_checksum(sample_data, sample_id, biofiles_directory)

        # Create dictionnary
        interpretation = {
                "indexCase": index_id,
                "project": project_slug,
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
            
            log_message(function_name, "DEBUG", f"New interpretation {interpretation_title}, with sample: {sample_id}")
        else:
            log_message(function_name, "DEBUG", f"Existing interpretation {interpretation_title}, with sample: {sample_id}")
            # Met à jour les informations ou échoue en cas d'incohérences
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
                    log_message(function_name, "ERROR", f"Conflict detected for '{key}' of '{interpretation_title}': Existing value: '{value}', New value: '{interpretation[key]}'")
                    raise ValueError(f"Conflict detected for '{key}' of '{interpretation_title}': Existing value: '{value}', New value: '{interpretation[key]}'")

            dict_interpretations[interpretation_title]["datas_tuples"].append(v_data_tuple)

    for interpretation in dict_interpretations.values():
        # Vérifie qu'il y a bien un cas index
        if not interpretation["indexCase"]:
            error_message = str(f"No Index case specified for :", interpretation["title"])
            log_message(function_name, "ERROR", error_message)
            raise ValueError(f"No Index case specified for", interpretation["title"])

        datas_dict = {}

        # Créer les objets sample
        for title, file_type, sample in interpretation["datas_tuples"]:
            composite_key = (title, file_type)
            
            # Charger les colonnes à exclure
            exclude_columns = settings['excludeColumns']
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
                    
    dict_interpretations = remove_empty_keys(dict_interpretations)    
    list_interpretations = [value for value in dict_interpretations.values()]
    return list_interpretations
