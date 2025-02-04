import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
import yaml

from colorlog import ColoredFormatter

formatter = ColoredFormatter(
    "%(log_color)s%(levelname)s: %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "SUCCESS": "bold_green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }
)

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




# Définition du niveau personnalisé SUCCESS
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")
# Fonction pour ajouter success() au logger
def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)
logging.Logger.success = success  # Ajout de la méthode au logger



def setup_logger(name, log_file, level=logging.INFO):
    """
    Crée et retourne un logger avec un fichier spécifique.

    Args:
        name (str): nom du logger
        log_file (str): fichier de log
        level (str, optional): niveau de log. Defaults to logging.INFO.

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


# Empêcher les handlers en double si le script est relancé
if not logger.handlers:
    
    logging.basicConfig(
        level=logging.INFO,                                             # Définir le niveau de log minimum
        format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s",    # Format du message
        handlers=[
            TimedRotatingFileHandler(
                log_file, 
                when="midnight",              # W0 = le lundi
                interval=1,             # toute les semaine --> donc chaque lundi à minuit
                backupCount=52,         # on conserve les 52 fichiers = 1 an
                encoding="utf-8", 
                delay=False),                                           # Rotation de logs
            logging.StreamHandler(sys.stdout),                          # Afficher les logs sur la console
        ],
        force=True)  # Force la reconfiguration et l'écriture immédiate





# # Chemin du fichier de log pour CREATE_JSON
# log_filename2 = "create_json.log"
# log_file2 = os.path.join(log_directory, log_filename2)
# logger2 = logging.getLogger("CREATE_JSON")
# logger2.setLevel(logging.INFO)

# # Empêcher les handlers en double si le script est relancé
# if not logger2.handlers:
    
#     logging.basicConfig(
#         level=logging.INFO,                                             # Définir le niveau de log minimum
#         format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s",    # Format du message
#         handlers=[
#             TimedRotatingFileHandler(
#                 log_file2, 
#                 when="midnight",              # W0 = le lundi
#                 interval=1,             # toute les semaine --> donc chaque lundi à minuit
#                 backupCount=52,         # on conserve les 52 fichiers = 1 an
#                 encoding="utf-8", 
#                 delay=False),                                           # Rotation de logs
#             logging.StreamHandler(sys.stdout),                          # Afficher les logs sur la console
#         ],
#         force=True)  # Force la reconfiguration et l'écriture immédiate