


def load_configuration(config):
    """
    Charge les paramètres de configuration nécessaires au fonctionnement du script.
    
    Args:
        config (dict): Dictionnaire contenant les configurations chargées depuis un fichier YAML ou JSON.
    
    Returns:
        dict: Contient les emails, le chemin des biofiles, les paramètres de vérification des biofiles et les endpoints API.
    """
    return {
        "recipients": config['emails']['recipients'],
        "path_biofiles": config['input_biofiles'],
        "get_biofile_max_retries": config['check_biofile']['max_retries'],
        "get_biofile_delay": config['check_biofile']['delay'],
        "diagho_api": {
            'healthcheck': f"{config['diagho_api']['url']}healthcheck",
            'login': f"{config['diagho_api']['url']}auth/login/",
            'get_user': f"{config['diagho_api']['url']}accounts/users/me",
            'get_biofile': f"{config['diagho_api']['url']}bio_files/files",
            'post_biofile_snv': f"{config['diagho_api']['url']}bio_files/files/snv/",
            'post_biofile_cnv': f"{config['diagho_api']['url']}bio_files/files/cnv/",
            'loading_status': f"{config['diagho_api']['url']}bio_files/files/",
            'config': f"{config['diagho_api']['url']}configurations/configurations/"
        }
    }