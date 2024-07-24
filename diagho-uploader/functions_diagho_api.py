#!/usr/bin/python3

import json
from bs4 import BeautifulSoup
import requests
import os
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
    Requête POST pour se connecter à l'API et stocke la réponse dans un fichier JSON.

    Args:
        url (str): URL de l'API de connexion.
        username (str): nom d'utilisateur.
        password (str): mot de passe.

    Returns:
        dict: réponse JSON de l'API contenant les tokens d'accès.
    """
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json'
    }
    payload = {
        'username': username,
        'password': password
    }
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        response_json = response.json()
        store_tokens(response_json)  # Stocker la réponse dans un fichier JSON
        print("Tokens stored successfully.")
        return response.json()  # Assuming the response is in JSON format
    else:
        response.raise_for_status()  # Raise an HTTPError if the response code is not 200


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
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    files = {
        'file': (os.path.basename(file_path), open(file_path, 'rb'), 'application/octet-stream')
    }
    data = {
        'accession': accession_id
    }
    try:
        # Effectuer la requête POST avec le fichier et les données de formulaire
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()  # Vérifie si la requête a réussi (statut 200)
        try:
            return response.json().get('checksum')
            # return response.json()  # Retourner la réponse JSON
        except ValueError:
            return {"error": "Response is not in JSON format"}
    except requests.exceptions.HTTPError as err:
        return {"error": str(err)}  # Retourner une erreur HTTP si la requête échoue
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}  # Retourner une erreur de requête si un autre problème survient


# # GET api/v1/bio_files/files/ --> checksum
# def diagho_api_get_md5sum(biofile, url):
#     """
#     Description.

#     Arguments:

#     Returns:
        
#     """
#     access_token = get_access_token()
#     headers = {
#         'Authorization': f'Bearer {access_token}',  # Remplacez par votre token d'accès
#         'Accept': 'application/json'
#     }
#     try:
#         # Effectuer la requête GET avec les en-têtes spécifiés
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()  # Vérifie si la requête a réussi (statut 200)
#         # Retourner la réponse JSON ou le texte brut si ce n'est pas du JSON
#         try:
#             return response.json()
#         except ValueError:
#             return response.text
#     except requests.exceptions.HTTPError as err:
#         return {"error": str(err)}
#     except requests.exceptions.RequestException as e:
#         return {"error": str(e)}
    
    
#     ## Pour les tests:
#     return "139361d8c92fd7bba1e26fbe89ebf5eb"

# GET api/v1/bio_files/files/ --> loading
def diagho_api_get_loadingstatus(url, checksum):
    """
    GET pour obtenir le loading_status du fichier (checksum).

    Arguments:
        url (str): URL de l'API.
        checksum (str): valeur du checksum à inclure comme paramètre de requête dans l'URL.

    Returns:
        int: La valeur du champ 'loading' si elle est trouvée dans la réponse JSON. 
        
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
def diagho_api_post_config(url, config_file):
    """
    Requête POST pour se uploader un config_file (JSON).

    Args:
        url (str): URL de l'API.
        config_file (str): fichier JSON de config à uploader.

    Returns:
        dict: réponse JSON de l'API.
    """
    print("diagho_api_post_config:",config_file)
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }            
    try:
        with open(config_file, 'r') as json_file:
            json_data = json.load(json_file)
        response = requests.post(url, headers=headers, json=json_data)
        response.raise_for_status()  # Vérifie si la requête a réussi (statut 200)
        try:
            return response.json()  # Retourner la réponse JSON
        except ValueError:
            return {"error": "Response is not in JSON format"}
    except requests.exceptions.HTTPError as err:
        return {"error": str(err)}  # Retourner une erreur HTTP si la requête échoue
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}  # Retourner une erreur de requête si un autre problème survient