import logging


# Fonction de log générique
def log_message(logger_name, level, message):
    """
    Enregistre un message dans les logs à un niveau donné.

    Args:
        logger_name (str): Nom du logger.
        level (str): Niveau du log (INFO, WARNING, ERROR, SUCCESS, etc.).
        message (str): Message à enregistrer.
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
        logger.log(logging.DEBUG, message)  # Par défaut, on utilise DEBUG si niveau inconnu


# Fonction de log générique pour un biofile
def log_biofile_message(logger_name, level, biofile_name, message):
    """
    Enregistre un message dans les logs pour un fichier BIOFILE à un niveau donné.
    Le message est de la forme : BIOFILE_NAME - MESSAGE

    Args:
        logger_name (str): Nom du logger.
        level (str): Niveau du log (INFO, WARNING, ERROR, SUCCESS, etc.).
        biofile_name (str): Nom du fichier bioinformatique.
        message (str): Message à enregistrer.
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
        logger.log(logging.DEBUG, log_message)  # Par défaut, on utilise DEBUG si niveau inconnu




# INFO
def log_info(logger_name, message):
    """
    Enregistre un message d'information dans les logs.

    Args:
        logger_name (str): Nom du logger.
        message (str): Message à enregistrer.
    """
    logging.getLogger(f"{logger_name}").info(f"{message}")

def log_biofile_info(logger_name, biofile_name,  message):
    """
    Enregistre un message d'information pour un BIOFILE dans les logs.

    Args:
        logger_name (str): Nom du logger.
        message (str): Message à enregistrer.
    """
    logging.getLogger(f"{logger_name}").info(f"{biofile_name} - {message}")


# ERROR
def log_error(logger_name, message):
    """
    Enregistre un message d'erreur dans les logs et le retourne sous forme de dictionnaire.

    Args:
        logger_name (str): Nom du logger.
        message (str): Message d'erreur.

    Returns:
        dict: Contenant l'erreur.
    """
    logging.getLogger(f"{logger_name}").error(f"Error: {message}")
    return {"error": message}

def log_biofile_error(logger_name, biofile_name,message):
    """
    Enregistre un message d'erreur pour un BIOFILE dans les logs et le retourne sous forme de dictionnaire.

    Args:
        logger_name (str): Nom du logger.
        message (str): Message d'erreur.

    Returns:
        dict: Contenant l'erreur.
    """
    logging.getLogger(f"{logger_name}").error(f"{biofile_name} - {message}")
    return {"error": message}


# WARNING
def log_warning(logger_name, message):
    """
    Enregistre un message de warning dans les logs et le retourne sous forme de dictionnaire.

    Args:
        logger_name (str): Nom du logger.
        message (str): Message d'erreur.

    Returns:
        dict: Contenant l'erreur.
    """
    logging.getLogger(f"{logger_name}").warning(f"{message}")
    return {"warning": message}

def log_biofile_warning(logger_name, biofile_name, message):
    """
    Enregistre un message de warning pour un BIOFILE dans les logs et le retourne sous forme de dictionnaire.

    Args:
        logger_name (str): Nom du logger.
        message (str): Message d'erreur.

    Returns:
        dict: Contenant l'erreur.
    """
    logging.getLogger(f"{logger_name}").warning(f"{biofile_name} - {message}")
    return {"warning": message}


# SUCCESS
def log_success(logger_name, message):
    """
    Enregistre un message de succès dans les logs et le retourne sous forme de dictionnaire.

    Args:
        logger_name (str): Nom du logger.
        message (str): Message d'erreur.

    Returns:
        dict: Contenant l'erreur.
    """
    logging.getLogger(f"{logger_name}").success(f"{message}")
    return {"warning": message}

def log_biofile_success(logger_name, biofile_name, message):
    """
    Enregistre un message de succès pour un BIOFILE dans les logs et le retourne sous forme de dictionnaire.

    Args:
        logger_name (str): Nom du logger.
        message (str): Message d'erreur.

    Returns:
        dict: Contenant l'erreur.
    """
    logging.getLogger(f"{logger_name}").success(f"{biofile_name} - {message}")
    return {"warning": message}