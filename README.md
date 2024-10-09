# diagho-uploader


## Table des Matières

1. [Installation](#installation)

2. [Utilisation](#utilisation)

   2.1 [Création du fichier json d'input](#etape-1--création-du-fichier-json-dinput)

   2.2 [Upload des fichiers dans Diagho](#etape-2--upload-des-fichiers-dans-diagho)

<br>
<br>

## Installation

### Pré-requis

- Python 3.x

### Installation

```bash

git clone https://github.com/DiaghoProject/diagho-uploader.git

cd diagho-uploader

# Create venv
python -m venv venv

# Activate venv
source venv/bin/activate

# Install dependences
pip install -r requirements.txt

# Copy config file
cp config/config.yaml.example config.yaml

```

- Compléter le fichier `config.yaml`

<br>
<br>

## Utilisation

### Pré-requis

Créer 2 répertoires :
- **input_biofiles** : va contenir les fichiers VCF et BED
- **input_data** : va contenir les fichiers JSON (informations sur les échantillons)

<br>
<br>

### Etape 1 : création du fichier JSON d'input

- Template TSV
- Colonnes :

| Column name   | Content       |
| ------------- | ------------- |
| id            | identifiat unique  |
| filename      | Nom du fichier (VCF ou BED) |
| checksum	    | Checksum du fichier (optionnel) |
| file_type     | **SNV** ou **CNV** |
| assembly      | **GRCh37** ou **GRCh38** |
| sample        | ID du sample |
| bam_path      | Chemin du fichier bam |
| family_id     | ID de la famille | 
| person_id	    | ID du patient | 
| father_id	    | ID père |
| mother_id	    | ID mère |
| sex           | **female** ou **male** ou **unknown** |
| is_affected   | boolean : 0 , 1 |
| first_name    | Prénom |
| last_name     | Nom de famille | 
| date_of_birth | Date de naissance | 
| hpo           | Codes HPO (séparateur ` ; `) (optionnel) | 
| interpretation_title | Titre de l'interprétation ; exemple `Family_ID (Cas_Index_ID)` |
| is_index      | boolean : 0 , 1 |
| project       | Nom du projet |
| assignee      | Username de l'assigné (optionnel) | 
| priority      | 0, 1, 2, 3, 4 (optionnel) |
| person_note   | Texte (optionnel) |
| data_title    | Titre de l'onglet de données SNV ou CNV (optionnel) |


- Création du fichier JSON :
```bash
source venv/bin/activate

BATCHID="RUN-001"                       # utilisé pour nommer les fichiers de sortie (généralement le nom du run)
INPUT_FILE="path/to/input_file.tsv"     # ficher d'input TSV (selon le template défini)
DIR_BIOFILES="path/to/input_biofiles"   # répertoire où sont stockés les VCFs et les BEDs
OUTPUT_DIR="./output_json/${BATCHID}"   # répertoire de sortie
OUTPUT_PREFIX="${BATCHID}"              # préfix fichier de sortie
mkdir -p $OUTPUT_DIR


python ./diagho-create-inputs/diagho-create-inputs.py \
    --input_file $INPUT_FILE \
    --output_directory $OUTPUT_DIR \
    --output_prefix $OUTPUT_PREFIX \
    --biofiles_directory $DIR_BIOFILES

```

- Déposer le fichier JSON créé dans le répertoire **input_data** pour la suite

<br>
<br>

### Etape 2 : upload des fichiers dans Diagho

- Le fichier json créé doit être déposé dans le répertoire **input_data**
- **input_biofiles** doit contenir les fichiers VCF et BED

```bash
source venv/bin/activate

python diagho-uploader/file_watcher.py 

# ou :
nohup python ./diagho-uploader/file_watcher.py &

```
