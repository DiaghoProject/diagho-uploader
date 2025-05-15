import inspect
import yaml

from utils.logger import log_message

def load_config(config_path):
    """
    Loads a YAML configuration file and returns it as a dictionary.
    """
    function_name = inspect.currentframe().f_code.co_name
    log_message(function_name, "INFO", f"Load config_file: {config_path}")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)
    

def load_configuration(config):
    """
    Loads the settings dictionary and returns it in structured form.

    Args:
        config (dict): settings dict

    Returns:
        dict: structured dict
    """
    function_name = inspect.currentframe().f_code.co_name
    log_message(function_name, "DEBUG", f"Load config: {config}")
    
    return {
        "recipients": config['emails']['recipients'],
        "path_biofiles": config['input_biofiles'],
        "path_backup_biofiles": config['backup_biofiles'],
        "path_backup_data": config['backup_data'],
        "get_biofile_max_retries": config['check_biofile']['max_retries'],
        "get_biofile_delay": config['check_biofile']['delay'],
        "check_loading_max_retries": config['check_loading']['max_retries'],
        "check_loading_delay": config['check_loading']['delay'],
        "max_workers": config['settings']['max_workers'],
        "accessions": config['accessions'],
        "excludeColumns": config['interpretations']['excludeColumns'],
        "projects": config['interpretations']['projects']
    }
