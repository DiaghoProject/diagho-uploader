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


        
def diagho_api_post_login(url, username, password, csrf_token):
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
        'X-CSRFTOKEN': csrf_token
    }
    
    payload = {
        'username': username,
        'password': password
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
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
def diagho_api_get_md5sum(biofile):
    """
    Description.

    Arguments:

    Returns:
        
    """
    print("API GET - MD5SUM for biofile:", biofile)
    ## Pour les tests:
    return "139361d8c92fd7bba1e26fbe89ebf5eb"

# GET api/v1/bio_files/files/ --> loading
def diagho_api_get_loadingstatus():
    """
    Description.

    Arguments:

    Returns:
        
    """
    print("diagho_api_get_loadingstatus")
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