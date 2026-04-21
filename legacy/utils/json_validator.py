import inspect
import json
import os

from utils.logger import *


def validate_json_input(json_input):
    """
    Validates JSON file structure.
    """
    function_name = inspect.currentframe().f_code.co_name
    json_filename = os.path.basename(json_input)
    try:
        with open(json_input, 'r') as json_file:
            input_data = json.load(json_file)

        if "families" not in input_data:
            log_message(function_name, "ERROR", f"{os.path.basename(json_filename)}- Le fichier JSON doit contenir une clé 'families'.")
            raise ValueError("Le fichier JSON doit contenir une clé 'families'.")
        if "files" not in input_data:
            log_message(function_name, "ERROR", f"{os.path.basename(json_filename)}- Le fichier JSON doit contenir une clé 'files'.")
            raise ValueError("Le fichier JSON doit contenir une clé 'files'.")
        if "interpretations" not in input_data:
            log_message(function_name, "ERROR", f"{os.path.basename(json_filename)}- Le fichier JSON doit contenir une clé 'interpretations'.")
            raise ValueError("Le fichier JSON doit contenir une clé 'interpretations'.")

        required_keys = ["filename", "checksum", "assembly", "samples"]
        
        for file in input_data["files"]:
            # Vérifier la présence des clés obligatoires
            missing_keys = [key for key in required_keys if key not in file]
            if missing_keys:
                raise ValueError(f"Clés manquantes: {missing_keys}")

            # Vérifier la structure des samples
            if not isinstance(file["samples"], list) or not file["samples"]:
                raise ValueError(f"'samples' doit être une liste non vide pour '{file['filename']}'.")

            for sample in file["samples"]:
                if "person" not in sample:
                    raise ValueError(f"Clé 'person' manquante dans un sample du fichier '{file['filename']}'.")
        return input_data

    except (json.JSONDecodeError, FileNotFoundError) as e:
        raise ValueError(f"Erreur lors de la lecture du fichier JSON : {e}")