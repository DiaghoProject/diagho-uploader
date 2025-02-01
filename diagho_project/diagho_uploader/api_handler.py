import json
import requests
import os
import time
import inspect
import yaml
import re
import sys

import logging

# Problem SSL certificate
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



def handle_api_error(function_name, error, logger_name, custom_message=None):
    """
    Gère les erreurs de l'API en loggant l'erreur et renvoyant un message d'erreur.
    """
    logger = logging.getLogger(logger_name)
    logger.error(f"FUNCTION: {function_name} - Error: {custom_message or str(error)}")
    return {"error": custom_message or str(error)}


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
        error_message = f"API healthcheck: KO - HTTP Error: {http_err}"
    except requests.exceptions.RequestException as req_err:
        error_message = f"API healthcheck: KO - Request Error: {req_err}"
    
    # Si erreur : renvoie le message  
    # logging.getLogger("API_HEALTHCHECK").error(error_message)
    handle_api_error("api_healthcheck", error_message, "API_STORE_TOKENS")
    raise ValueError(error_message)


def validate_credentials(config):
    """
    Validates the login credentials in the configuration file.
    """
    logger = logging.getLogger("API_CREDENTIALS")
    username = config.get('diagho_api', {}).get('username', None)
    password = config.get('diagho_api', {}).get('password', None)

    if not username or not password:
        logger.info(f"Username or password is missing.")
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
        return handle_api_error("store_tokens", e, "API_STORE_TOKENS")


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
        return handle_api_error("get_access_token", e, "API_GET_ACCESS_TOKEN")

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
        return handle_api_error("api_get_connected_user", e, "API_GET_CONNECTED_USER")
    except json.JSONDecodeError:
        return handle_api_error("api_get_connected_user", "API response invalid", "API_GET_CONNECTED_USER")
    except Exception as e:
        return handle_api_error("api_get_connected_user", e, "API_GET_CONNECTED_USER")

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
            return handle_api_error("api_post_login", e, "API_POST_LOGIN")