import yaml

def load_config(config_path):
    """Charge un fichier YAML de configuration et le retourne sous forme de dictionnaire."""
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def load_configuration(config):
    """Charge et structure les paramètres nécessaires à l'utilisation de l'API."""
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
