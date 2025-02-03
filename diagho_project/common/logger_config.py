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
print("LOG_DIRECTORY:", log_directory)
os.makedirs(log_directory, exist_ok=True)

# Chemin du fichier de log
log_filename = "diagho_uploader.log"
log_file = os.path.join(log_directory, log_filename)

# Configuration du logger
logger = logging.getLogger("FileWatcher")
logger.setLevel(logging.INFO)

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
            # logging.FileHandler(log_file)                               # Enregistrer les logs dans un fichier
        ],
        force=True)  # Force la reconfiguration et l'écriture immédiate
    
