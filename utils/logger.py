import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
import yaml

# Charger la configuration depuis config.yaml
config_file = "config/config.yaml"
with open(config_file, "r") as file:
    config = yaml.safe_load(file)

# Récupérer le log_directory depuis la config
log_directory = config.get("log_directory", "logs")
os.makedirs(log_directory, exist_ok=True)

# Chemin du fichier de log pour FILE_WATCHER
log_filename = "diagho_uploader.log"
log_file = os.path.join(log_directory, log_filename)

# Configuration du logger
logger = logging.getLogger("FILE_WATCHER")
logger.setLevel(logging.INFO)




# # Définition du niveau personnalisé SUCCESS
# SUCCESS_LEVEL = 25
# logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")
# # Fonction pour ajouter success() au logger
# def success(self, message, *args, **kwargs):
#     if self.isEnabledFor(SUCCESS_LEVEL):
#         self._log(SUCCESS_LEVEL, message, args, **kwargs)
# logging.Logger.success = success  # Ajout de la méthode au logger



def setup_logger(name, log_file, level=logging.INFO):
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
            when="W0",              # W0 = chaque lundi
            interval=1,             # Chaque semaine
            backupCount=52,         # Conserver 52 semaines de logs (1 an)
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

# Utilisé pour les tests
# Empêcher les handlers en double si le script est relancé
if not logger.handlers:
    
    logging.basicConfig(
        level=logging.INFO,                                             # Définir le niveau de log minimum
        format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s",    # Format du message
        handlers=[
            TimedRotatingFileHandler(
                log_file, 
                when="W0",              # W0 = le lundi
                interval=1,             # toute les semaine --> donc chaque lundi à minuit
                backupCount=52,         # on conserve les 52 fichiers = 1 an
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

    # Log selon le niveau spécifié
    if level.upper() == 'INFO':
        logger.info(message)
    elif level.upper() == 'WARNING':
        logger.warning(message)
    elif level.upper() == 'ERROR':
        logger.error(message)
    elif level.upper() == 'SUCCESS':
        logger.success(message)
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
    
    # Log selon le niveau spécifié
    log_message = f"{biofile_name} - {message}"

    if level.upper() == 'INFO':
        logger.info(log_message)
    elif level.upper() == 'WARNING':
        logger.warning(log_message)
    elif level.upper() == 'ERROR':
        logger.error(log_message)
    elif level.upper() == 'SUCCESS':
        logger.success(log_message)
    elif level.upper() == 'DEBUG':
        logger.debug(log_message)
    else:
        logger.log(logging.DEBUG, log_message)

