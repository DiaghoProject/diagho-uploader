#! /bin/bash

###########################################################################
#
# Exemple pour lancer le script de création du fichier JSON
#
###########################################################################

# Si besoin : créer un venv
# Create venv
python -m venv venv
# Activate venv
source venv/bin/activate
# Install dependences
pip install -r requirements.txt



source venv/bin/activate

# Inputs :
BATCHID="RUN-001"                               # utilisé pour nommer les fichiers de sortie (généralement le nom du run)
INPUT_DIR="./INPUTS/input"                      # répertoire d'input
INPUT_FILE="${INPUT_DIR}/input_file.tsv"        # ficher d'input TSV (selon le template défini)
DIR_BIOFILES="./input_biofiles"                 # répertoire où sont stockés les VCFs et les BEDs
OUTPUT_DIR="./OUTPUTS/${BATCHID}"               # répertoire de sortie
OUTPUT_PREFIX="${BATCHID}"                      # préfix fichiers de sortie (par défaut BATCHID = nom du run)

mkdir -p $OUTPUT_DIR


# Script :
python ./diagho-create-inputs/diagho-create-inputs.py \
    --input_file $INPUT_FILE \
    --output_directory $OUTPUT_DIR \
    --output_prefix $OUTPUT_PREFIX \
    --biofiles_directory $DIR_BIOFILES
