import yaml

def load_config(config_path):
    """Charge un fichier YAML de configuration et le retourne sous forme de dictionnaire."""
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def load_configuration(config):
    """
    Charge le dictionnaire des paramètres et le retourne sous forme structurée.

    Args:
        config (dict): dictionnaire des paramètres

    Returns:
        dict: dictionnaire structuré
    """
    return {
        "recipients": config['emails']['recipients'],
        "path_biofiles": config['input_biofiles'],
        "path_backup_biofiles": config['backup_biofiles'],
        "get_biofile_max_retries": config['check_biofile']['max_retries'],
        "get_biofile_delay": config['check_biofile']['delay'],
        "check_loading_max_retries": config['check_loading']['max_retries'],
        "check_loading_delay": config['check_loading']['delay'],
        "accessions": config['accessions']
    }
