import json
import requests
import os
import time
import inspect
import yaml
import re
import sys

# import logging
from common.logger_config import logger 

# Problem SSL certificate
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from common.log_utils import *



def api_healthcheck(diagho_api, exit_on_error=False):
    """
    Tests the health of the API by performing a GET request to the healthcheck endpoint.
    """
    url = diagho_api['healthcheck']
    
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        return True # Succès
    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP Error: {http_err}"
    except requests.exceptions.RequestException as req_err:
        error_message = f"Request Error: {req_err}"
    log_error("API_HEALTHCHECK", error_message)
    raise ValueError(error_message)


def validate_credentials(config):
    """
    Validates the login credentials in the configuration file.
    """
    username = config.get('diagho_api', {}).get('username', None)
    password = config.get('diagho_api', {}).get('password', None)

    if not username or not password:
        log_error("API_CREDENTIALS", f"Username or password is missing.")
        raise ValueError("Username or password is missing")
    return username, password


def store_tokens(tokens, filename='tokens.json'):
    """
    Store tokens in JSON file.
    """
    if not isinstance(tokens, dict):
        return {"error": "'tokens' must be a dictionary"}
    try:
        with open(filename, 'w') as file:
            json.dump(tokens, file, indent=4)
    except Exception as e:
        return log_error("API_STORE_TOKEN", f"{str(e)}")


def get_access_token(filename='tokens.json'):
    """
    Get access token from file or re-authent.
    """
    logger = logging.getLogger("API_GET_ACCESS_TOKEN")
    if not os.path.isfile(filename):
        logger.warning("Token not found.")
        return {"error": "'access' token not found"}    
    try:
        with open(filename, 'r') as file:
            tokens = json.load(file)
        if 'access' not in tokens:
            return {"error": "'access' token not found in file"}
        return tokens['access']
    except Exception as e:
        return log_error("API_GET_TOKEN", f"{str(e)}")

def api_login(config, diagho_api):
    """
    Handles the login process to the Diagho API.
    """
    logger = logging.getLogger("API_LOGIN")

    # Validate credentials
    username, password = validate_credentials(config)
        
    # Obtain the current access token
    access_token = get_access_token()
    
    kwargs = {
        "access_token": access_token,
        "config": config,
        "diagho_api": diagho_api
    }
    # If access_token not found : authentification
    if "error" in access_token:
        print("access_token not found : authentification...")
        return api_post_login(**kwargs)
    else:
        # Access_token found
        # Check if the user is already logged in
        if api_get_connected_user(**kwargs):
            logger.info(f"User '{username}' already connected.")
            return {"status": "User already connected"}
        # Otherwise, attempt to log in
        logger.info(f"Attempting login for user '{username}'.")
        return api_post_login(**kwargs)

    
def api_get_connected_user(**kwargs):
    """
    Check if user is already connected. 
    """
    config = kwargs.get("config")
    access_token = kwargs.get("access_token")
    diagho_api = kwargs.get("diagho_api")
    
    url = diagho_api['get_user']
    if not access_token:
        return {"error": "No access token available"}
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        user_data = response.json()
        if user_data.get('username') == config['diagho_api']['username']:
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        return log_error("API_GET_CONNECTED_USER", f"{str(e)}")
    except json.JSONDecodeError:
        return log_error("API_GET_CONNECTED_USER", f"API response invalid")
    except Exception as e:
        return log_error("API_GET_CONNECTED_USER", f"{str(e)}")

# Post login to API
def api_post_login(**kwargs):
    """
    Envoie une requête POST pour se connecter à l'API et stocke la réponse contenant les tokens.
    """ 
    logger = logging.getLogger("API_POST_LOGIN")
    config = kwargs.get("config")
    diagho_api = kwargs.get("diagho_api")
    
    username = config['diagho_api']['username']
    password = config['diagho_api']['password']
    url = diagho_api['login']
    
    headers = {'accept': '*/*', 'Content-Type': 'application/json'}
    payload = {'username': username, 'password': password}
    
    max_attempts = 3
    
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, verify=False)
            response.raise_for_status()
            response_json = response.json()
            store_tokens(response_json)
            return response_json  # Authent OK
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt}/{max_attempts} failed: {str(e)}")
            if attempt < max_attempts:
                time.sleep(5)  # Attente avant la prochaine tentative
            else:
                logger.error("Max login attempts reached.")
                return {"error": f"Authentication failed after {max_attempts} attempts"}
        except Exception as e:
            return log_error("API_POST_LOGIN", f"{str(e)}")        



def api_post_biofile(**kwargs):
    """
    Requête POST pour uploader un biofile s'il n'existe pas déjà.
    Retourne son checksum.
    """ 
    settings = kwargs.get("settings")
    diagho_api = kwargs.get("diagho_api")
    biofile = kwargs.get("biofile")
    biofile_type = kwargs.get("biofile_type")
    assembly = kwargs.get("assembly")
    accession_id = kwargs.get("accession_id")
    checksum = kwargs.get("checksum")
    
    # Récupérer l'info en fonction du type de biofile
    def handle_biofile_type(biofile_type, assembly, accession_id):
        if biofile_type == "SNV":
            return {'accession': accession_id}
        elif biofile_type == "CNV":
            return {'assembly': assembly}
        return None
    
    # Récupérer l'URL du POST en fonction du type de biofile
    def get_url_post_biofile(biofile_type):
        if biofile_type == "SNV":
            return diagho_api['post_biofile_snv']
        elif biofile_type == "CNV":
            return diagho_api['post_biofile_cnv']
        return None
    
    # Fonction pour logguer les erreurs
    def log_error(message):
        logging.getLogger("API_POST_BIOFILE").error(message)
    
    # Validation du biofile
    filename = os.path.basename(biofile)
    if not os.path.isfile(biofile):
        log_error(f"{filename} - Biofile not found: {biofile}")
        return {"error": "Biofile not found"}
    
    # Get access token
    access_token = get_access_token()
    
    headers = {'Authorization': f'Bearer {access_token}'}

    # Handle biofile type and parameter (assembly name or accession_id)
    data = handle_biofile_type(biofile_type, assembly, accession_id)
    if not data:
        log_error(f"{filename} - Invalid biofile_type.")
        return {"error": "Unknown Biofile type"}
    
    # Check if biofile already exists
    url_get_biofile = diagho_api['get_biofile']
    url_with_params = f"{url_get_biofile}/?checksum={checksum}"
    logging.getLogger("API_POST_BIOFILE").info(f"{filename} - Test if Biofile is already uploaded.")
    
    try:
        response = requests.get(url_with_params, headers=headers, verify=False)
        response.raise_for_status()
        biofile_exist = response.json().get('count')
        if biofile_exist > 0:
            logging.getLogger("API_POST_BIOFILE").info(f"{filename} - Biofile already uploaded.")
            # On retourne le checksum
            return {"checksum": checksum}
    except requests.exceptions.RequestException as e:
        log_error(f"{filename} - Error checking biofile existence: {str(e)}")
        return {"error": str(e)}
    
    # Upload biofile if not found
    try:
        files = {'file': (filename, open(biofile, 'rb'), 'application/octet-stream')}
        url = get_url_post_biofile(biofile_type)
        response = requests.post(url, headers=headers, files=files, data=data, verify=False)
        response.raise_for_status()
        response_json = response.json()
        if isinstance(response_json, dict):
            # On récupère le checksum du biofile posté
            checksum = response_json.get('checksum')
            logging.getLogger("API_POST_BIOFILE").info(f"{filename} - POST Biofile completed. Checksum: {checksum}")
            # On retourne le checksum
            return {"checksum": checksum}
        log_error(f"{filename} - Error with POST biofile response.")
        return {"error": "Error with POST biofile response."}
    except (requests.exceptions.RequestException, ValueError) as e:
        log_error(f"{filename} - Error uploading biofile: {str(e)}")
        return {"error": f"Error uploading biofile: {str(e)}"}
    
    
def api_get_loadingstatus(**kwargs):
    """
    GET pour obtenir le loading_status du fichier (checksum).
    """
    diagho_api = kwargs.get("diagho_api")
    checksum = kwargs.get("checksum")
    
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}', 
        'Accept': 'application/json'
    }

    # Construire l'URL avec le paramètre checksum
    url = diagho_api['loading_status']
    url_with_params = f"{url}?checksum={checksum}"
    
    # Fonction pour logguer les erreurs
    def log_error(message):
        logging.getLogger("API_GET_LOADING_STATUS").error(message)
    
    try:
        response = requests.get(url_with_params, headers=headers, verify=False)
        response.raise_for_status()
        results = response.json().get('results', [])
        if not results:
            return {"error": "No results found in response"}
        
        # Récupérer le statut
        loading = results[0].get('loading')
        if loading is None:
            return {"error": "'loading' field not found in results"}
        
        # Retourner le statut
        return {"loading": loading}

    except requests.exceptions.RequestException as e:
        log_error(str(e))
        return {"error": str(e)}
    except ValueError:
        log_error("Response is not in JSON format")
        return {"error": "Response is not in JSON format"}
    except Exception as e:
        log_error(str(e))
        return {"error": str(e)}


def api_post_config(**kwargs):
    """
    Requête POST pour uploader un fichier de configuration JSON.
    """
    diagho_api = kwargs.get("diagho_api")
    file = kwargs.get("file")
    
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Charger le fichier JSON
    try:
        with open(file, 'r') as json_file:
            json_data = json.load(json_file)
    except json.JSONDecodeError:
        return log_error("POST_JSON", f"Config file '{file}' is not valid JSON")
    
    # POST config
    try:
        url = diagho_api['post_config']
        response = requests.post(url, headers=headers, json=json_data, verify=False)
        response.raise_for_status()
        log_info("POST_JSON", f"JSON file '{json_file}' posted successfully.")
        return response
    except requests.exceptions.RequestException as e:
        return log_error("POST_JSON", str(e))
