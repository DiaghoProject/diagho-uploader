import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
import yaml

# Charger la configuration depuis config.yaml
config_file = "config/config.yaml"
with open(config_file, "r") as file:
    config = yaml.safe_load(file)

# Récupérer le niveau de logs du fichier de config (par défaut = INFO)
LOG_LEVEL = config.get("logging", {}).get("log_level", "INFO")

# Récupérer le répertoire des logs depuis la config
LOG_DIRECTORY = config.get("logging", {}).get("log_directory", "logs")
os.makedirs(LOG_DIRECTORY, exist_ok=True)

# Récupérer les paramètres de rotation des logs depuis la config
LOG_ROTATION_WHEN = config.get("logging", {}).get("log_rotation_when", "W0")
LOG_ROTATION_INTERVAL = config.get("logging", {}).get("log_rotation_interval", 1)
LOG_BACKUP_COUNT = config.get("logging", {}).get("log_backup_count", 52)

# Chemin du fichier de log pour FILE_WATCHER
log_filename = "diagho_uploader.log"
log_file = os.path.join(LOG_DIRECTORY, log_filename)

# Configuration du logger
logger = logging.getLogger("FILE_WATCHER")
logger.setLevel(LOG_LEVEL)


def setup_logger(name, log_file, level=LOG_LEVEL):
    """
    Creates and returns a logger with a specific file.

    Args:
        name (str): logger name
        log_file (str): logs file
        level (str, optional): log level. Defaults to logging.INFO.

    Returns:
        logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Vérifier si le logger a déjà des handlers pour éviter les doublons
    if not logger.hasHandlers():
        # Format du message
        formatter = logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s")
        
        # Handler pour la rotation des logs
        file_handler = TimedRotatingFileHandler(
            log_file, 
            when=LOG_ROTATION_WHEN,
            interval=LOG_ROTATION_INTERVAL,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
            delay=False
        )
        file_handler.setFormatter(formatter)
        
        # Handler pour afficher les logs dans la console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Ajouter les handlers au logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


# Empêcher les handlers en double si le script est relancé
if not logger.handlers:
    
    logging.basicConfig(
        level=LOG_LEVEL,                                                # Définir le niveau de log minimum
        format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s",    # Format du message
        handlers=[
            TimedRotatingFileHandler(
                log_file, 
                when=LOG_ROTATION_WHEN,
                interval=LOG_ROTATION_INTERVAL,
                backupCount=LOG_BACKUP_COUNT,
                encoding="utf-8", 
                delay=False),                                           # Rotation de logs
            logging.StreamHandler(sys.stdout),                          # Afficher les logs sur la console
        ],
        force=True)  # Force la reconfiguration et l'écriture immédiate


# Fonction de log générique
def log_message(logger_name, level, message):
    """
    Logs a message at a given level.

    Args:
        logger_name (str): logger name.
        level (str): log level (INFO, WARNING, ERROR, SUCCESS, etc.).
        message (str): Message.
    """
    logger = logging.getLogger(logger_name)

    if level.upper() == 'INFO':
        logger.info(message)
    elif level.upper() == 'WARNING':
        logger.warning(message)
    elif level.upper() == 'ERROR':
        logger.error(message)
    elif level.upper() == 'DEBUG':
        logger.debug(message)
    else:
        logger.log(logging.DEBUG, message)


# Fonction de log générique pour un biofile
def log_biofile_message(logger_name, level, biofile_name, message):
    """
    Logs a message for a BIOFILE file at a given level.
    The message is of the form: BIOFILE_NAME - MESSAGE

    Args:
        logger_name (str): logger name.
        level (str): log level (INFO, WARNING, ERROR, SUCCESS, etc.).
        biofile_name (str): name of the biofile.
        message (str): Message.
    """
    logger = logging.getLogger(logger_name)
    log_message = f"{biofile_name} - {message}"

    if level.upper() == 'INFO':
        logger.info(log_message)
    elif level.upper() == 'WARNING':
        logger.warning(log_message)
    elif level.upper() == 'ERROR':
        logger.error(log_message)
    elif level.upper() == 'DEBUG':
        logger.debug(log_message)
    else:
        logger.log(logging.DEBUG, log_message)

