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


# GET /api/v1/healthcheck 
def diagho_api_healthcheck(diagho_api, exit_on_error=False):
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
    logging.getLogger("API_HEALTHCHECK").error(error_message)
    raise ValueError(error_message)
