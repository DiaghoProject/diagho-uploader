#!/usr/bin/python3

import json
from bs4 import BeautifulSoup
import requests
import os
import time
import inspect
import yaml

from functions import * 


config_file = "config/config.yaml"

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def alert(content: str):
    config = load_config(config_file)
    recipients = config['emails']['recipients']
    send_mail_alert(recipients, content)

# GET /api/v1/healthcheck 
def diagho_api_test(config_file, exit_on_error=False):
    """
    Tests the health of the API by performing a GET request to the URL.

    Args:
        url (str): The URL of the API to test.
        exit_on_error (bool): Whether to exit the program on HTTP error. Default is False.

    Returns:
        bool: True if the request is successful (status code 200), False otherwise.
    """
    config = load_config(config_file)
    url = config['diagho_api']['healthcheck']
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


def diagho_api_login(config_file):
    """
    Gère le processus de connexion à l'API Diagho.

    Cette fonction vérifie si l'utilisateur est déjà connecté en utilisant un access token.
    Si l'utilisateur n'est pas connecté, elle appelle diagho_api_post_login pour se connecter.

    Args:
        config_file (str): Chemin vers le fichier de configuration contenant les informations de connexion.

    Returns:
        dict: Un dictionnaire contenant le statut de la connexion ou les erreurs éventuelles.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    try:
        # Charger les informations de configuration
        config = load_config(config_file)
        username = config['diagho_api']['username']
        password = config['diagho_api']['password']
        
        # Validation des identifiants
        if not username or not password:
            content = f"FUNCTION: {function_name}:\n\nError: Username or password is missing"
            alert(content)
            return {"error": "Username or password is missing"}
        
        # Obtenir l'access token actuel
        access_token = get_access_token()
        
        # Vérifier si l'utilisateur est déjà connecté
        if diagho_api_get_connected_user(config_file, access_token):
            print("User already connected.")
            return {"status": "User already connected"}
        else:
            # Tenter une nouvelle connexion
            return diagho_api_post_login(config_file)
        
    except FileNotFoundError:
        content = f"FUNCTION: {function_name}:\n\nError: Configuration file not found"
        alert(content)
        return {"error": "Configuration file not found"}
    except KeyError as e:
        content = f"FUNCTION: {function_name}:\n\nError: Missing key in configuration - {str(e)}"
        alert(content)
        return {"error": f"Missing key in configuration: {str(e)}"}
    except Exception as e:
        content = f"FUNCTION: {function_name}:\n\nUnexpected Error: {str(e)}"
        alert(content)
        return {"error": f"Unexpected error: {str(e)}"}
        
    

# GET /api/v1/accounts/users/me/
def diagho_api_get_connected_user(config_file, access_token):
    """
    Vérifie si l'utilisateur connecté à l'API est le même que celui spécifié dans la configuration.

    Args:
        url (str): URL de l'API pour obtenir les informations de l'utilisateur connecté.
        config_file (str): Chemin vers le fichier de configuration contenant le nom d'utilisateur attendu.

    Returns:
        bool: True si l'utilisateur connecté correspond à celui du fichier de configuration, sinon False.
        
    Raises:
        Exception: Si une erreur se produit lors de la récupération des informations utilisateur ou de la configuration.
    """
    config = load_config(config_file)
    url = config['diagho_api']['get_user']
    if not access_token:
        return {"error": "No access token available"}
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Vérifie si la requête a réussi
        user_data = response.json()
        user_username = user_data.get('username')
        
        config = load_config(config_file)
        username = config['diagho_api']['username']
        
        if user_username == username:
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la connexion à l'API: {e}")
        return False
    except KeyError as e:
        print(f"Clé manquante dans la configuration ou les données de l'utilisateur: {e}")
        return False
    except json.JSONDecodeError:
        print("Erreur de décode JSON. Réponse de l'API non valide.")
        return False
    except Exception as e:
        print(f"Une erreur inattendue s'est produite: {e}")
    

# POST api/v1/auth/login/
def store_tokens(tokens, filename='tokens.json'):
    """
    Stocke les tokens dans un fichier JSON.

    Args:
        tokens (dict): Dictionnaire contenant les tokens à stocker.
        filename (str): Nom du fichier où les tokens seront stockés. Par défaut 'tokens.json'.
    """
    if not isinstance(tokens, dict):
        return {"error": "'tokens' must be a dictionary"}
    
    try:
        with open(filename, 'w') as file:
            json.dump(tokens, file, indent=4)
    except IOError as e:
        return {"error": f"IOError: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}

       
def get_access_token(filename='tokens.json'):
    """
    Charge les tokens depuis un fichier JSON.

    Args:
        filename (str): Nom du fichier où les tokens sont stockés. Par défaut 'tokens.json'.

    Returns:
        dict: Dictionnaire contenant les tokens chargés.
    """
    if not os.path.isfile(filename):
        print("Token not found... Re-authentification...")
        config = load_config(config_file)
        url = config['diagho_api']['login']
        diagho_api_post_login(config_file)
        
    try:
        with open(filename, 'r') as file:
            tokens = json.load(file)
            if 'access' not in tokens:
                return {"error": "'access' token not found in file"}
            access_token = tokens['access']
            return access_token
    except json.JSONDecodeError:
        return {"error": "File is not a valid JSON"}
    except KeyError:
        return {"error": "'access' key not found in tokens"}
    except Exception as e:
        return {"error": str(e)}
        
def diagho_api_post_login(config_file):
    """
    Requête POST pour se connecter à l'API et stocke la réponse dans un fichier JSON.

    Args:
        url (str): URL de l'API de connexion.
        config_file (str): Chemin vers le fichier de configuration contenant les informations de connexion.


    Returns:
        dict: réponse JSON de l'API contenant les tokens d'accès.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    config = load_config(config_file)
    username = config['diagho_api']['username']
    password = config['diagho_api']['password']
    url = config['diagho_api']['login']
    
    # Validation des paramètres
    if not username or not password:
        content = f"FUNCTION: {function_name}:\n\nError: Username or password is missing"
        alert(content)
        return {"error": "Username or password is missing"}
    
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json'
    }
    payload = {
        'username': username,
        'password': password
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Lève une exception si le code de statut n'est pas 200
        
        try:
            response_json = response.json()
            store_tokens(response_json)  # Stocker les tokens dans un fichier JSON
            return response_json
        except ValueError:
            content = f"FUNCTION: {function_name}:\n\nError: Response is not in JSON format"
            alert(content)
            return {"error": "Response is not in JSON format"}
        except Exception as e:
            content = f"FUNCTION: {function_name}:\n\nError: Failed to store tokens - {str(e)}"
            alert(content)
            return {"error": "Failed to store tokens"}
        
    except requests.exceptions.HTTPError as err:
        content = f"FUNCTION: {function_name}:\n\nHTTP Error: {str(err)}"
        alert(content)
        return {"error": str(err)}
    except requests.exceptions.RequestException as e:
        content = f"FUNCTION: {function_name}:\n\nRequest Error: {str(e)}"
        alert(content)
        return {"error": str(e)}
    except Exception as e:
        content = f"FUNCTION: {function_name}:\n\nUnexpected Error: {str(e)}"
        alert(content)
        return {"error": str(e)}


# POST api/v1/bio_files/files/
def diagho_api_post_biofile(url, file_path, accession_id):
    """
    Requête POST pour se uploader un bio_file.

    Args:
        url (str): URL de l'API.
        file_path (str): fichier à uploader.
        accession_id (int): PK de l'accession à utiliser.

    Returns:
        checksum: si upload OK, retourne le checksum du fichier uploadé.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    access_token = get_access_token()
    if not access_token:
        return {"error": "No access token available"}
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    if not os.path.isfile(file_path):
        return {"error": "File not found"}
    
    files = {
        'file': (os.path.basename(file_path), open(file_path, 'rb'), 'application/octet-stream')
    }
    data = {
        'accession': accession_id
    }
    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()  # Vérifie si la requête a réussi (statut 200)
        time.sleep(3) # sleep 3s 
        try:
            response_json = response.json()
            checksum = response_json.get('checksum')
            if checksum:
                return {"checksum": checksum}
            else:
                content = f"FUNCTION: {function_name}:\n\nError: No checksum in response"
                alert(content)
                return {"error": "No checksum in response"}
        except ValueError:
            content = f"FUNCTION: {function_name}:\n\nError: Response is not in JSON format"
            alert(content)
            return {"error": "Response is not in JSON format"}
    except requests.exceptions.HTTPError as err:
        content = f"FUNCTION: {function_name}:\n\nHTTP Error: {str(err)}"
        alert(content)
        return {"error": str(err)}  # Retourner une erreur HTTP si la requête échoue
    except requests.exceptions.RequestException as e:
        content = f"FUNCTION: {function_name}:\n\nRequest Error: {str(e)}"
        alert(content)
        return {"error": str(e)}
    except Exception as e:
        content = f"FUNCTION: {function_name}:\n\nUnexpected Error: {str(e)}"
        alert(content)
        return {"error": str(e)}


# GET api/v1/bio_files/files/ --> loading
def diagho_api_get_loadingstatus(url, checksum):
    """
    GET pour obtenir le loading_status du fichier (checksum).

    Arguments:
        url (str): URL de l'API.
        checksum (str): valeur du checksum à inclure comme paramètre de requête dans l'URL.

    Returns:
        dict: Contenant la valeur du champ 'loading' ou un message d'erreur.
        
    """
    function_name = inspect.currentframe().f_code.co_name
    
    access_token = get_access_token()
    if not access_token:
        return {"error": "No access token available"}
    
    headers = {
        'Authorization': f'Bearer {access_token}', 
        'Accept': 'application/json'
    }
    
    # Construire l'URL avec le paramètre checksum
    url_with_params = f"{url}?checksum={checksum}"
    
    try:
        response = requests.get(url_with_params, headers=headers)
        response.raise_for_status()  # Vérifie si la requête a réussi (statut 200)
        
        try:
            results = response.json().get('results', [])
            if not results:
                content = f"FUNCTION: {function_name}:\n\nError: No results found in response"
                alert(content)
                return {"error": "No results found in response"}
            
            loading = results[0].get('loading')
            if loading is None:
                content = f"FUNCTION: {function_name}:\n\nError: 'loading' field not found in results"
                alert(content)
                return {"error": "'loading' field not found in results"}
            
            return {"loading": loading}
        except ValueError:
            content = f"FUNCTION: {function_name}:\n\nError: Response is not in JSON format"
            alert(content)
            return {"error": str(e)}
    except requests.exceptions.HTTPError as err:
        content = f"FUNCTION: {function_name}:\n\nHTTP Error: {str(err)}"
        alert(content)
        return {"error": str(err)}
    except requests.exceptions.RequestException as e:
        content = f"FUNCTION: {function_name}:\n\nRequest Error: {str(e)}"
        alert(content)
        return {"error": str(e)}
    except Exception as e:
        content = f"FUNCTION: {function_name}:\n\nUnexpected Error: {str(e)}"
        alert(content)
        return {"error": str(e)}


# POST api/v1/configurations/configurations/
def diagho_api_post_config(url, file):
    """
    Requête POST pour se uploader un config_file (JSON).
    
    Args:
        url (str): URL de l'API.
        file (str): fichier JSON de config à uploader.

    Returns:
        dict: réponse JSON de l'API.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    access_token = get_access_token()
    if not access_token:
        return {"error": "No access token available"}
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }            
    try:
        with open(file, 'r') as json_file:
            try:
                json_data = json.load(json_file)
            except json.JSONDecodeError:
                content = f"FUNCTION: {function_name}:\n\nError: Config file '{file}' is not valid JSON"
                alert(content)
                return {"error": "Config file is not valid JSON"}
            
        response = requests.post(url, headers=headers, json=json_data)
        response.raise_for_status()  # Vérifie si la requête a réussi (statut 200)
        
        try:
            # return response.json()  # Retourner la réponse JSON
            # return response.status_code
            return {"status_code": response.status_code, "json_response": response.json()}
        except ValueError:
            content = f"FUNCTION: {function_name}:\n\nError: Response is not in JSON format"
            alert(content)
            return {"error": "Response is not in JSON format"}
    except requests.exceptions.HTTPError as err:
        content = f"FUNCTION: {function_name}:\n\nHTTP Error: {str(err)}"
        alert(content)
        return {"error": str(err)}  # Retourner une erreur HTTP si la requête échoue
    except requests.exceptions.RequestException as e:
        content = f"FUNCTION: {function_name}:\n\nRequest Error: {str(e)}"
        alert(content)
        return {"error": str(e)}  # Retourner une erreur de requête si un autre problème survient
    