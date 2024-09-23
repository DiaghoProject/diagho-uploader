# Diagho Uploader

Surveillance du répertoire défini par **input_data** dans le fichier de configuration.

Si un nouveau fichier JSON ou TSV est détecté, demarrage du pipeline.

## Pipeline

1. Copie du fichier dans **backup**
2. Process fichier
3. Suppression du fichier de **input_data**


## Process du fichier

### diagho_process_file


#### 1. Récupération de la configuration (chargement du fichier config.yaml)

- Récupère les valeurs définies dans la config 
  - URLs des endpoints
  - Valeur de l'accession à utiliser
  - Temps/délai définis par défaut
  - etc.

#### 2. Test de la conexion à l'API Diagho

#### 3. Connexion API
- Récupérer le token d'accès

#### 4. Test du format du fichier
- Si JSON : vérifie le formatage attendu

#### 5. Récupération des informations du fichier JSON
- filename (fichier VCF ou BED)
- checksum
- samples et persons associés

#### 6. Pour chaque filename
- Récupère le chemin complet du *biofile* correspondant (dans **input_biofie**)
- Si le *biofile* n'existe pas : attendre (délai d'attente défini)
- S'il existe : continuer
- Calcul du checksum du *biofile*
- Si c'est un VCF : **process_vcf**
- Si c'est un BED : **process_bed**

#### 7.1. Process VCF
- POST du *biofile* 
  - Récupération du checksum
- Compare le checksum calculé précédemment avec le checksum renvoyé par l'API
  - Si différents --> problem !
- Vérification du statut de chargement du fichier
  - Pendant un temps défini en config (retry toutes les X secondes...)
  - Si statut == 0 --> échec du chargement
  - SI statut == 3 --> success, passer à la suite...
  - Autre statut : attendre et re-checker le statut
- Quand le statut est à SUCCESS :
- Récupérer les fichiers JSON (familles et interprétations) correspondants au *filename* en cours de traitement
  - 2 fichiers à récupérer : *.families.json* et *.interpretations.json*
- POST de chaque fichiers :
  - families
  - files (le JSON en cours de traitement)
  - interpretations
- Pour chacun de ces 3 fichiers : les déplacer dans le dossier **backup**


#### 7.2. Process BED
- TODO
