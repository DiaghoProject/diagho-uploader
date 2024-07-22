#!/usr/bin/python3

import json
import random   # pour les tests


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
    print("diagho_api_post_config")