# Diagho Create Inputs

Création du fichier JSON.

1 fichier JSON par batch.

## Process

- Détection du type de fichier en entrée :
  - TSV : le fichier sera transformé en JSON simple
  - JSON : TODO (valider le format)

- Création du fichier *.families.json*
- Création du fichier *.biofiles.json*
- Création du fichier *.interpretations.json*

- Combiner les 3 fichiers JSON

- Supprimer les fichiers temporaires