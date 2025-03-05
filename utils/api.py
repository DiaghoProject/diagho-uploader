import json
import requests
import os
import time
import inspect
import yaml
import re
import sys

from utils.logger import *

# Problem SSL certificate
import urllib3
from utils.mail import *

# TODO: à tester
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Charger le fichier de config
CONFIG_FILE = os.getenv("CONFIG_PATH", "config/config.yaml")
with open(CONFIG_FILE, "r") as file:
    config = yaml.safe_load(file)
    
# Définir la variable globale (cf. config.yaml)
ALLOW_INSECURE = config.get("allow_insecure", False)
# Si allow_insecure = true alors tous les Verify=False
VERIFY = not ALLOW_INSECURE 

def get_api_endpoints(config):
    """
    Returns the API endpoints from the configuration file.
    """
    url_diagho_api = config['diagho_api']['url']
    return {
        'healthcheck': f"{url_diagho_api}healthcheck",
        'login': f"{url_diagho_api}auth/login/",
        'get_user': f"{url_diagho_api}accounts/users/me",
        'get_biofile': f"{url_diagho_api}bio_files/files",
        'post_biofile_snv': f"{url_diagho_api}bio_files/files/snv/",
        'post_biofile_cnv': f"{url_diagho_api}bio_files/files/cnv/",
        'post_config': f"{url_diagho_api}configurations/configurations/",
        'get_project': f"{url_diagho_api}projects/projects/"
    }
    # API 0.4.0
    # url_diagho_api = config['diagho_api']['url'].removesuffix('/')
    # return {
    #     'healthcheck': f"{url_diagho_api}/healthcheck",
    #     'login': f"{url_diagho_api}/auth/login",
    #     'get_user': f"{url_diagho_api}/users/me",
    #     'get_biofile': f"{url_diagho_api}/bio-files",
    #     'post_biofile_snv': f"{url_diagho_api}/bio-files/snv",
    #     'post_biofile_cnv': f"{url_diagho_api}/bio-files/cnv",
    #     'post_config': f"{url_diagho_api}/configurations,
    #     'get_project': f"{url_diagho_api}/projects"
    # }
    
def api_healthcheck(diagho_api, exit_on_error=False):
    """
    Tests the health of the API by performing a GET request to the healthcheck endpoint.
    """
    function_name = inspect.currentframe().f_code.co_name
    url = diagho_api['healthcheck']
    
    try:
        response = requests.get(url, verify=VERIFY)
        response.raise_for_status()
        return True # Succès
    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP Error: {http_err}"
    except requests.exceptions.RequestException as req_err:
        error_message = f"Request Error: {req_err}"
    log_message(function_name, "ERROR", error_message)
    raise ValueError(error_message)


def validate_credentials(config):
    """
    Validates the login credentials in the configuration file.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    username = config.get('diagho_api', {}).get('username', None)
    password = config.get('diagho_api', {}).get('password', None)

    if not username or not password:
        log_message(function_name, "ERROR", f"Username or password is missing.")
        raise ValueError("Username or password is missing")
    return username, password


def store_tokens(tokens, filename='tokens.json'):
    """
    Store tokens in JSON file.
    """
    function_name = inspect.currentframe().f_code.co_name
    if not isinstance(tokens, dict):
        return {"error": "'tokens' must be a dictionary"}
    try:
        with open(filename, 'w') as file:
            json.dump(tokens, file, indent=4)
        log_message(function_name, "DEBUG", "Store access token.")
    except Exception as e:
        return log_message(function_name, "ERROR", f"{str(e)}")


def get_access_token(filename='tokens.json'):
    """
    Get access token from file or re-authent.
    """
    function_name = inspect.currentframe().f_code.co_name
    if not os.path.isfile(filename):
        log_message(function_name, "WARNING", "Token not found.")
        return {"error": "'access' token not found"}    
    try:
        with open(filename, 'r') as file:
            tokens = json.load(file)
        if 'access' not in tokens:
            return {"error": "'access' token not found in file"}
        return tokens['access']
    except Exception as e:
        return log_message(function_name, "ERROR", f"{str(e)}")

def api_login(config, diagho_api):
    """
    Handles the login process to the Diagho API.
    """
    function_name = inspect.currentframe().f_code.co_name
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
        return api_post_login(**kwargs)
    else:
        # Access_token found
        # Check if the user is already logged in
        if api_get_connected_user(**kwargs):
            log_message(function_name, "DEBUG", f"User '{username}' already connected.")
            return {"status": "User already connected"}
        # Otherwise, attempt to log in
        log_message(function_name, "DEBUG", f"Attempting login for user '{username}'.")
        return api_post_login(**kwargs)

    
def api_get_connected_user(**kwargs):
    """
    Check if user is already connected. 
    """
    function_name = inspect.currentframe().f_code.co_name
    
    config = kwargs.get("config")
    access_token = kwargs.get("access_token")
    diagho_api = kwargs.get("diagho_api")
    
    url = diagho_api['get_user']
    if not access_token:
        return {"error": "No access token available"}
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(url, headers=headers, verify=VERIFY)
        response.raise_for_status()
        user_data = response.json()
        if user_data.get('username') == config['diagho_api']['username']:
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        return log_message(function_name, "ERROR", f"{str(e)}")
    except json.JSONDecodeError:
        return log_message(function_name, "ERROR", f"API response invalid")
    except Exception as e:
        return log_message(function_name, "ERROR", f"{str(e)}")

# Post login to API
def api_post_login(**kwargs):
    """
    Sends a POST request to connect to the API and stores the response containing the tokens.
    """
    function_name = inspect.currentframe().f_code.co_name
    
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
            response = requests.post(url, headers=headers, json=payload, verify=VERIFY)
            response.raise_for_status()
            response_json = response.json()
            store_tokens(response_json)
            log_message(function_name, "INFO", f"Authentification successful for: {username}")
            return response_json  # Authent OK
        except requests.exceptions.RequestException as e:
            log_message(function_name, "WARNING", f"Attempt {attempt}/{max_attempts} failed: {str(e)}")
            if attempt < max_attempts:
                time.sleep(5)  # Attente avant la prochaine tentative
            else:
                log_message(function_name, "ERROR", "Max login attempts reached.")
                return {"error": f"Authentication failed after {max_attempts} attempts"}
        except Exception as e:
            return log_message(function_name, "ERROR", f"{str(e)}")        



def api_post_biofile(**kwargs):
    """
    POST request to upload a biofile if it doesn't already exist.
    Returns its checksum.
    """
    function_name = inspect.currentframe().f_code.co_name
    
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
    
    # Validation du biofile
    filename = os.path.basename(biofile)
    if not os.path.isfile(biofile):
        log_message(function_name, "ERROR", f"{filename} - Biofile not found: {biofile}")
        return {"error": "Biofile not found"}
    
    # Get access token
    access_token = get_access_token()
    
    headers = {'Authorization': f'Bearer {access_token}'}

    # Handle biofile type and parameter (assembly name or accession_id)
    data = handle_biofile_type(biofile_type, assembly, accession_id)
    if not data:
        log_message(function_name, "ERROR", f"{filename} - Invalid biofile_type.")
        return {"error": "Unknown Biofile type"}
    
    # Check if biofile already exists
    url_get_biofile = diagho_api['get_biofile']
    url_with_params = f"{url_get_biofile}/?checksum={checksum}"
    log_message(function_name, "DEBUG", f"{filename} - Test if Biofile is already uploaded.")
    
    try:
        response = requests.get(url_with_params, headers=headers, verify=VERIFY)
        response.raise_for_status()
        biofile_exist = response.json().get('count')
        if biofile_exist > 0:
            log_message(function_name, "INFO", f"{filename} - Biofile already uploaded.")
            # On retourne le checksum
            return {"checksum": checksum}
    except requests.exceptions.RequestException as e:
        log_message(function_name, "ERROR", f"{filename} - Error checking biofile existence: {str(e)}")
        return {"error": str(e)}
    
    # Upload biofile if not already uploaded
    try:
        files = {'file': (filename, open(biofile, 'rb'), 'application/octet-stream')}
        url = get_url_post_biofile(biofile_type)
        response = requests.post(url, headers=headers, files=files, data=data, verify=VERIFY)
        response.raise_for_status()
        response_json = response.json()
        if isinstance(response_json, dict):
            # On récupère le checksum du biofile posté
            checksum = response_json.get('checksum')
            log_message(function_name, "INFO", f"{filename} - POST Biofile completed. Checksum: {checksum}")
            # On retourne le checksum
            return {"checksum": checksum}
        log_message(function_name, "ERROR", f"{filename} - Error with POST biofile response.")
        return {"error": "Error with POST biofile response."}
    except (requests.exceptions.RequestException, ValueError) as e:
        log_message(function_name, "ERROR", f"{filename} - Error uploading biofile: {str(e)}")
        return {"error": f"Error uploading biofile: {str(e)}"}


def api_get_loadingstatus(**kwargs):
    """
    GET to obtain the file's loading_status (using 'checksum').
    """
    function_name = inspect.currentframe().f_code.co_name
    
    diagho_api = kwargs.get("diagho_api")
    checksum = kwargs.get("checksum")
    
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}', 
        'Accept': 'application/json'
    }

    # Construire l'URL avec le paramètre checksum
    url = diagho_api['get_biofile']
    url_with_params = f"{url}/?checksum={checksum}"
    
    try:
        response = requests.get(url_with_params, headers=headers, verify=VERIFY)
        response.raise_for_status()
        results = response.json().get('results', [])
        if not results:
            return {"error": "No results found in response"}
        
        # Récupérer le statut
        loading = results[0].get('loading')
        if loading is None:
            return {"error": "'loading' field not found in results"}
        
        # Retourner le statut
        return {"loadingStatus": loading}

    except requests.exceptions.RequestException as e:
        log_message(function_name, "ERROR", f"{str(e)}")
        return {"error": str(e)}
    except ValueError:
        log_message(function_name, "ERROR", "Response is not in JSON format")
        return {"error": "Response is not in JSON format"}
    except Exception as e:
        log_message(function_name, "ERROR", f"{str(e)}")
        return {"error": str(e)}


def api_post_config(**kwargs):
    """
    POST request to upload a JSON configuration file.
    """
    function_name = inspect.currentframe().f_code.co_name
    
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
        log_message(function_name, "ERROR", f"Config file '{file}' is not valid JSON")
        return {"error": f"Config file '{file}' is not valid JSON"}
    
    # POST config
    try:
        url = diagho_api['post_config']
        response = requests.post(url, headers=headers, json=json_data, verify=VERIFY)
        response.raise_for_status()
        log_message(function_name, "INFO", f"JSON file '{file}' posted successfully.")
        return response
    except requests.exceptions.RequestException as e:
        log_message(function_name, "ERROR", str(e))
        return {"error": str(e)}



def check_api_response(response, **kwargs):
    """
    Checks API response after configuration POST and sends notifications based on status.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    recipients = kwargs.get('recipients')
    json_file = kwargs.get('json_file')
    
    log_message(function_name, "INFO", f"response.status_code = {response.status_code}")

    # Si OK
    if response.status_code == 201:
        log_message(function_name, "INFO", f"{os.path.basename(json_file)}: configuration file was posted in Diagho successfully")
        send_mail_info(recipients, f"JSON file: {json_file}\n\nThe JSON configuration file was posted in Diagho successfully")
        return

    # Si KO
    if response.status_code == 400:
        json_response = response.json()
        search_string = "A person with the same identifier already exist, but is present in another family."
        json_string = json.dumps(json_response)

        if search_string in json_string:
            persons_content = json_response.get('errors', {}).get('families', [{}])[4].get('persons', 'N/A')
            alert_message = f"JSON file: {json_file}\n\nA person with the same identifier already exists but is present in another family:\n{persons_content}"
        else:
            alert_message = f"JSON file: {json_file}\n\nError in POST configuration."
        send_mail_alert(recipients, alert_message)
        log_message(function_name, "ERROR", f"{os.path.basename(json_file)}: error in POST configuration")
        log_message(function_name, "ERROR", f"{json_response}")
        
        

def api_get_project_from_slug(**kwargs):
    """
    Get project from slug. 
    """
    function_name = inspect.currentframe().f_code.co_name
    
    diagho_api = kwargs.get("diagho_api")
    project_slug = kwargs.get("project_slug")
    
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}', 
        'Accept': 'application/json'
    }
    
    url = diagho_api['get_project']
    url_with_params = f"{url}{project_slug}"
    
    try:
        response = requests.get(url_with_params, headers=headers, verify=VERIFY)
        response.raise_for_status()
        slug = response.json().get('slug', [])
        return slug

    except requests.exceptions.RequestException as e:
        return log_message(function_name, "ERROR", f"{str(e)}")
    except json.JSONDecodeError:
        return log_message(function_name, "ERROR", f"API response invalid")
    except Exception as e:
        return log_message(function_name, "ERROR", f"{str(e)}")