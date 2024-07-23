#!/usr/bin/python3

import json
from bs4 import BeautifulSoup
import requests
import random   # pour les tests


# GET /api/v1/healthcheck 
def diagho_api_test(url, exit_on_error=False):
    """
    Tests the health of the API by performing a GET request to the URL.

    Args:
        url (str): The URL of the API to test.
        exit_on_error (bool): Whether to exit the program on HTTP error. Default is False.

    Returns:
        bool: True if the request is successful (status code 200), False otherwise.
    """
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~")
    print("API : healthcheck")
    print("~~~~~~~~~~~~~~~~~~~~~~~~")
    try:
        response = requests.get(url)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        print(">>> OK")
        return True
    except requests.exceptions.HTTPError as http_err:
        print(">>> ERROR: HTTP error occurred.")
        print(f"Status code: {response.status_code}")
        print(f"Error details: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(">>> ERROR: Request exception occurred.")
        print(f"Error details: {req_err}")
    finally:
        if exit_on_error:
            raise SystemExit("Exiting due to API health check failure.")
    return False


# POST api/v1/auth/login/
def store_tokens(tokens, filename='tokens.json'):
    """
    Stocke les tokens dans un fichier JSON.

    Args:
        tokens (dict): Dictionnaire contenant les tokens à stocker.
        filename (str): Nom du fichier où les tokens seront stockés. Par défaut 'tokens.json'.
    """
    with open(filename, 'w') as file:
        json.dump(tokens, file, indent=4)
        
def load_tokens(filename='tokens.json'):
    """
    Charge les tokens depuis un fichier JSON.

    Args:
        filename (str): Nom du fichier où les tokens sont stockés. Par défaut 'tokens.json'.

    Returns:
        dict: Dictionnaire contenant les tokens chargés.
    """
    with open(filename, 'r') as file:
        tokens = json.load(file)
    return tokens

def get_access_token(filename='tokens.json'):
    """
    Charge les tokens depuis un fichier JSON.

    Args:
        filename (str): Nom du fichier où les tokens sont stockés. Par défaut 'tokens.json'.

    Returns:
        dict: Dictionnaire contenant les tokens chargés.
    """
    with open(filename, 'r') as file:
        tokens = json.load(file)
        access_token = tokens['access']
    return access_token
        
def diagho_api_post_login(url, username, password):
    """
    Effectue une requête POST pour se connecter à l'API et stocke la réponse dans un fichier JSON.

    Args:
        url (str): L'URL de l'API de connexion.
        username (str): Le nom d'utilisateur.
        password (str): Le mot de passe.

    Returns:
        dict: La réponse JSON de l'API contenant les tokens d'accès.
    """
    print("diagho_api_post_login:", url, username, password)
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json'
    }
    payload = {
        'username': username,
        'password': password
    }
    print("payload:", payload)
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        response_json = response.json()
        store_tokens(response_json)  # Stocker la réponse dans un fichier JSON
        print("Tokens stored successfully.")
        return response.json()  # Assuming the response is in JSON format
    else:
        response.raise_for_status()  # Raise an HTTPError if the response code is not 200



# POST api/v1/bio_files/files/
def diagho_api_post_biofile(biofile_filename, biofile_checksum):
    """
    Description.

    Arguments:

    Returns:
        
    """
    print("API POST - Biofile : ", biofile_filename, biofile_checksum)
    
    

# GET api/v1/bio_files/files/ --> checksum
def diagho_api_get_md5sum(biofile, url):
    """
    Description.

    Arguments:

    Returns:
        
    """
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',  # Remplacez par votre token d'accès
        'Accept': 'application/json'
    }
    try:
        # Effectuer la requête GET avec les en-têtes spécifiés
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Vérifie si la requête a réussi (statut 200)
        # Retourner la réponse JSON ou le texte brut si ce n'est pas du JSON
        try:
            return response.json()
        except ValueError:
            return response.text
    except requests.exceptions.HTTPError as err:
        return {"error": str(err)}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    
    
    ## Pour les tests:
    return "139361d8c92fd7bba1e26fbe89ebf5eb"

# GET api/v1/bio_files/files/ --> loading
def diagho_api_get_loadingstatus(url, checksum):
    """
    Description.

    Arguments:

    Returns:
        
    """
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',  # Remplacez par votre token d'accès
        'Accept': 'application/json'
    }
    try:
        url = url + "?checksum=" + checksum
        # Effectuer la requête GET avec les en-têtes spécifiés
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Vérifie si la requête a réussi (statut 200)
        # Retourner la réponse JSON ou le texte brut si ce n'est pas du JSON
        try:
            results = response.json().get('results', [])
            return results[0].get('loading')
        except ValueError:
            return {"error": str(e)}
    except requests.exceptions.HTTPError as err:
        return {"error": str(err)}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    
    ## Pour les tests ------------------
    loading_status = random.randint(1, 4)
    ##----------------------------------
    return loading_status

# POST api/v1/configurations/configurations/
def diagho_api_post_config(config_file):
    """
    Description.

    Arguments:

    Returns:
        
    """
    print("diagho_api_post_config:",config_file)