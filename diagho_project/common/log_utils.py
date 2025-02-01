import logging


def log_info(logger_name, message):
    """
    Enregistre un message d'information dans les logs.

    Args:
        logger_name (str): Nom du logger.
        message (str): Message à enregistrer.
    """
    logging.getLogger(f"{logger_name}").info(f"{message}")


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


def log_warning(logger_name, message):
    """
    Enregistre un message de warning dans les logs et le retourne sous forme de dictionnaire.

    Args:
        logger_name (str): Nom du logger.
        message (str): Message d'erreur.

    Returns:
        dict: Contenant l'erreur.
    """
    logging.getLogger(f"{logger_name}").warning(f"WARNING: {message}")
    return {"warning": message}