#!/usr/bin/python3

import json
from bs4 import BeautifulSoup
import requests
import os
import time
import inspect
import yaml
import re

from functions import * 




def alert(content: str, config):
    recipients = config['emails']['recipients']
    send_mail_alert(recipients, content)

# GET /api/v1/healthcheck 
def diagho_api_healthcheck(diagho_api, exit_on_error=False):
    """
    Tests the health of the API by performing a GET request to the URL.

    Args:
        url (str): The URL of the API to test.
        exit_on_error (bool): Whether to exit the program on HTTP error. Default is False.

    Returns:
        bool: True if the request is successful (status code 200), False otherwise.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    url = diagho_api['healthcheck']

    try:
        response = requests.get(url)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as http_err:
        logging.getLogger("API_HEALTHCHECK").error(f"API healthcheck: KO - Error details: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logging.getLogger("API_HEALTHCHECK").error(f"API healthcheck: KO - Error details: {req_err}")
    finally:
        if exit_on_error:
            logging.getLogger("API_HEALTHCHECK").error(f"Exiting due to API health check failure.")
            raise SystemExit("Exiting due to API health check failure.")
    return False


def diagho_api_login(config):
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
        username = config['diagho_api']['username']
        password = config['diagho_api']['password']
        
        # Validation des identifiants
        if not username or not password:
            logging.getLogger("API_LOGIN").error(f"FUNCTION: {function_name}:Error: Username or password is missing")
            return {"error": "Username or password is missing"}

        # Obtenir l'access token actuel
        access_token = get_access_token(config)
                
        # Vérifier si l'utilisateur est déjà connecté
        if diagho_api_get_connected_user(config, access_token):
            logging.getLogger("API_LOGIN").info(f"User already connected.")
            return {"status": "User already connected"}
        else:
            # Tenter une nouvelle connexion
            return diagho_api_post_login(config)
        
    except FileNotFoundError:
        logging.getLogger("API_LOGIN").error(f"FUNCTION: {function_name}:Error: Configuration file not found")
        return {"error": "Configuration file not found"}
    except KeyError as e:
        logging.getLogger("API_LOGIN").error(f"FUNCTION: {function_name}:Error: Missing key in configuration - {str(e)}")
        return {"error": f"Missing key in configuration: {str(e)}"}
    except Exception as e:
        logging.getLogger("API_LOGIN").error(f"FUNCTION: {function_name}:Unexpected Error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}
        
    

# GET /api/v1/accounts/users/me/
def diagho_api_get_connected_user(config, access_token, diagho_api):
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
    url = diagho_api['get_user']

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
        
        username = config['diagho_api']['username']
        
        if user_username == username:
            logging.getLogger("API_GET_CONNECTED_USER").info(f"PASS")
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        logging.getLogger("API_GET_CONNECTED_USER").error(f"Erreur lors de la connexion à l'API: {e}")
        return False
    except KeyError as e:
        logging.getLogger("API_GET_CONNECTED_USER").error(f"MIssing key in configuration: {e}")
        return False
    except json.JSONDecodeError:
        logging.getLogger("API_GET_CONNECTED_USER").error(f"API response invalid.")
        return False
    except Exception as e:
        logging.getLogger("API_GET_CONNECTED_USER").error(f"Unexpected error: {e}")

    

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

       
def get_access_token(config, filename='tokens.json'):
    """
    Charge les tokens depuis un fichier JSON.

    Args:
        filename (str): Nom du fichier où les tokens sont stockés. Par défaut 'tokens.json'.

    Returns:
        dict: Dictionnaire contenant les tokens chargés.
    """
    if not os.path.isfile(filename):
        logging.getLogger("API_GET_ACCESS_TOKEN").warning(f"Token not found. Re-authent...")
        diagho_api_post_login(config)
        
    try:
        with open(filename, 'r') as file:
            tokens = json.load(file)
            if 'access' not in tokens:
                logging.getLogger("API_GET_ACCESS_TOKEN").error(f"'access' token not found in file.")
                return {"error": "'access' token not found in file"}
            access_token = tokens['access']
            return access_token
    except json.JSONDecodeError:
        logging.getLogger("API_GET_ACCESS_TOKEN").error(f"File is not a valid JSON")
        return {"error": "File is not a valid JSON"}
    except KeyError:
        logging.getLogger("API_GET_ACCESS_TOKEN").error(f"'access' key not found in tokens")
        return {"error": "'access' key not found in tokens"}
    except Exception as e:
        logging.getLogger("API_GET_ACCESS_TOKEN").error(f"{str(e)}")
        return {"error": str(e)}
        
def diagho_api_post_login(config, diagho_api):
    """
    Requête POST pour se connecter à l'API et stocke la réponse dans un fichier JSON.

    Args:
        url (str): URL de l'API de connexion.
        config_file (str): Chemin vers le fichier de configuration contenant les informations de connexion.


    Returns:
        dict: réponse JSON de l'API contenant les tokens d'accès.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    username = config['diagho_api']['username']
    password = config['diagho_api']['password']
    
    url = diagho_api['login']
    
    # Validation des paramètres
    if not username or not password:
        logging.getLogger("API_POST_LOGIN").error(f"FUNCTION: {function_name}:\n\nError: Username or password is missing")
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
        response.raise_for_status() 
        # TODO #23 tentatives + délai à faire 
        try:
            response_json = response.json()
            store_tokens(response_json)  # Stocker les tokens dans un fichier JSON
            return response_json
        except ValueError:
            logging.getLogger("API_POST_LOGIN").error(f"FUNCTION: {function_name}:Error: Response is not in JSON format")
            return {"error": "Response is not in JSON format"}
        except Exception as e:
            logging.getLogger("API_POST_LOGIN").error(f"FUNCTION: {function_name}:Error: Failed to store tokens - {str(e)}")
            return {"error": "Failed to store tokens"}
        
    except requests.exceptions.HTTPError as err:
        return {"error": str(err)}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


# POST api/v1/bio_files/files/snv/ ou api/v1/bio_files/files/cnv/
def diagho_api_post_biofile(url, biofile_path, biofile_type, param, config, diagho_api):
    """
    Requête POST pour uploader un biofile.

    Args:
        url (str): URL de l'API.
        file_path (str): fichier à uploader.
        accession_id (int): PK de l'accession à utiliser.

    Returns:
        checksum: si upload OK, retourne le checksum du fichier uploadé.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    filename = os.path.basename(biofile_path)
    
    access_token = get_access_token(config)
    if not access_token:
        return {"error": "No access token available"}   
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    if not os.path.isfile(biofile_path):
        logging.getLogger("API_POST_BIOFILE").error(f"{filename} - Biofile not found: {biofile_path}")
        return {"error": "Biofile not found"}
    
    files = {
        'file': (os.path.basename(biofile_path), open(biofile_path, 'rb'), 'application/octet-stream')
    }
    if biofile_type == "SNV":
        logging.getLogger("API_POST_BIOFILE").info(f"{filename} - Biofile type: {biofile_type}")
        logging.getLogger("API_POST_BIOFILE").info(f"{filename} - Use accession_id: {param}")
        data = {
            'accession': param
        }
    elif biofile_type == "CNV":
        logging.getLogger("API_POST_BIOFILE").info(f"{filename} - Biofile type: {biofile_type}")
        logging.getLogger("API_POST_BIOFILE").info(f"{filename} - Use assembly_name: {param}")
        data = {
            'assembly': param
        }
    else:
        logging.getLogger("API_POST_BIOFILE").error(f"{filename} - Invalid biofile_type.")
        return {"error": "Unknown Biofile type"}
    
    try:
        logging.getLogger("API_POST_BIOFILE").warning(f"{filename} - URL POST_BIOFILE: {url}")
        response = requests.post(url, headers=headers, files=files, data=data)
        time.sleep(3)
        try:
            response_json = response.json()
            
            # Si le POST a réussi, on récupère un dict         
            if isinstance(response_json, dict):
                checksum = response_json.get('checksum')
                logging.getLogger("API_POST_BIOFILE").info(f"{filename} - POST Biofile completed.")
                logging.getLogger("API_POST_BIOFILE").info(f"{filename} - Get checksum: {checksum}")
                return {"checksum": checksum}
            else:
                # Si fichier déjà envoyé précédemment, on récupère son ID
                logging.getLogger("API_POST_BIOFILE").info(f"{filename} -  Biofile already uploaded.")
                match = re.search(r'ID:\s*(\d+)', response.text)
                if match:
                    file_id = match.group(1)
                    print(f"ID récupéré : {file_id}")
                    logging.getLogger("API_POST_BIOFILE").info(f"{filename} - Get file_id: {file_id}")
                    
                    url_get_biofile = diagho_api['get_biofile']
                    url_with_params = f"{url_get_biofile}/{file_id}"
                    response2 = requests.get(url_with_params, headers=headers)
                    response2_json = response2.json()
                    checksum = response2_json.get('checksum')
                    logging.getLogger("API_POST_BIOFILE").info(f"{filename} - Get checksum: {checksum}")
                    return {"checksum": checksum}
                else:
                    print("Aucun ID de fichier trouvé dans la réponse.")
                
                return {"error": "No checksum in response"}
        except ValueError:
            logging.getLogger("API_POST_BIOFILE").error(f"FUNCTION: {function_name}:Error: Response is not in JSON format")
            return {"error": "Response is not in JSON format"}
    except requests.exceptions.HTTPError as err:
        logging.getLogger("API_POST_BIOFILE").error(f"FUNCTION: {function_name}:HTTP Error: {str(err)}")
        return {"error": str(err)}  
    except requests.exceptions.RequestException as e:
        logging.getLogger("API_POST_BIOFILE").error(f"FUNCTION: {function_name}:Request Error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logging.getLogger("API_POST_BIOFILE").error(f"FUNCTION: {function_name}:Unexpected Error: {str(e)}")
        return {"error": str(e)}



# GET api/v1/bio_files/files/ --> loading
def diagho_api_get_loadingstatus(url, checksum, config):
    """
    GET pour obtenir le loading_status du fichier (checksum).

    Arguments:
        url (str): URL de l'API.
        checksum (str): valeur du checksum à inclure comme paramètre de requête dans l'URL.

    Returns:
        dict: Contenant la valeur du champ 'loading' ou un message d'erreur.
        
    """
    function_name = inspect.currentframe().f_code.co_name
    
    access_token = get_access_token(config)
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
        response.raise_for_status() 
        
        try:
            results = response.json().get('results', [])
            if not results:
                logging.getLogger("API_GET_LOADING_STATUS").error(f"FUNCTION: {function_name}:Error: No results found in response")
                return {"error": "No results found in response"}
            
            loading = results[0].get('loading')
            if loading is None:
                logging.getLogger("API_GET_LOADING_STATUS").error(f"FUNCTION: {function_name}:Error: 'loading' field not found in results")
                return {"error": "'loading' field not found in results"}
            return {"loading": loading}
        except ValueError:
            logging.getLogger("API_GET_LOADING_STATUS").error(f"FUNCTION: {function_name}:Error: Response is not in JSON format")
            return {"error": str(e)}
    except requests.exceptions.HTTPError as err:
        logging.getLogger("API_GET_LOADING_STATUS").error(f"FUNCTION: {function_name}:HTTP Error: {str(err)}")
        return {"error": str(err)}
    except requests.exceptions.RequestException as e:
        logging.getLogger("API_GET_LOADING_STATUS").error(f"FUNCTION: {function_name}:Request Error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logging.getLogger("API_GET_LOADING_STATUS").error(f"FUNCTION: {function_name}:Unexpected Error: {str(e)}")
        return {"error": str(e)}


# POST api/v1/configurations/configurations/
def diagho_api_post_config(url, file, config):
    """
    Requête POST pour se uploader un config_file (JSON).
    
    Args:
        url (str): URL de l'API.
        file (str): fichier JSON de config à uploader.

    Returns:
        dict: réponse JSON de l'API.
    """
    function_name = inspect.currentframe().f_code.co_name
    
    access_token = get_access_token(config)
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
                pretty_print_json_string(json_data)
            except json.JSONDecodeError:
                logging.getLogger("API_POST_CONFIGURATION").error(f"FUNCTION: {function_name}:Error: Config file '{file}' is not valid JSON")
                return {"error": "Config file is not valid JSON"}
            
        response = requests.post(url, headers=headers, json=json_data)
        # response.raise_for_status()  # Vérifie si la requête a réussi (statut 200)
        
        try:
            response = requests.post(url, headers=headers, json=json_data)
            logging.getLogger("API_POST_CONFIGURATION").info(f"JSON file {file} posted succesfully.")
            logging.getLogger("API_POST_CONFIGURATION").info(f"status_code: {response.status_code}, json_response: {response.json()}")
            return {"status_code": response.status_code, "json_response": response.json()}
        except ValueError:
            logging.getLogger("API_POST_CONFIGURATION").error(f"FUNCTION: {function_name}:Error: Response is not in JSON format")
            return {"error": "Response is not in JSON format"}
    except requests.exceptions.HTTPError as err:
        logging.getLogger("API_POST_CONFIGURATION").error(f"FUNCTION: {function_name}:HTTP Error: {str(err)}")
        logging.getLogger("API_POST_CONFIGURATION").error(f"status_code: {response.status_code}")
        logging.getLogger("API_POST_CONFIGURATION").error(f"json_response: {response.json()}")
        return {"error": str(err)}
    except requests.exceptions.RequestException as e:
        logging.getLogger("API_POST_CONFIGURATION").error(f"FUNCTION: {function_name}:Request Error: {str(e)}")
        return {"error": str(e)} 
    