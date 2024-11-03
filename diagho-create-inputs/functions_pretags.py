#!/usr/bin/python3

import json

# Charger la config des pretags
with open("diagho-create-inputs/config_pretags.json", "r") as config_file:
    config_pretags = json.load(config_file)


def set_pretags_by_project(interpretation, datas_dict, composite_key):
    """
    Ajoute les pretags spécifiques à un projet dans un dictionnaire, en fonction du projet renseigné en 'interpretation'.
    Cette fonction récupère les tags et filtres prédéfinis pour le projet dans un fichier json.
    
    Args:
        interpretation (dict): 
            Dictionnaire contenant les informations sur l'interprétation
        datas_dict (dict): 
            Dictionnaire principal de données, dans lequel les pretags sont ajoutés pour une clé composite spécifique.
        composite_key: 
            Clé composite utilisée pour accéder à la section correspondante de 'datas_dict' où les pretags doivent être ajoutés.

    """
    # Récupération des pretags pour le projet courant
    project = interpretation.get('project', 'default')
    pretags_list = config_pretags.get(project, config_pretags["default"])
    
    # Ajout des pretags si non présents dans datas_dict
    for dict_pretag in pretags_list:
        if dict_pretag not in datas_dict[composite_key]["pretags"]:
            datas_dict[composite_key]["pretags"].append(dict_pretag)
    