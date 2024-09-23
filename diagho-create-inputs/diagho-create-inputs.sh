#! /bin/bash

# Create venv
python -m venv venv
# Activate venv
source venv/bin/activate
# Install dependences
pip install -r requirements.txt

# Arguments:
BATCHID="RUN-001"                                                           # utilisé pour nommer les fichiers de sortie (généralement le nom du run)
INPUT_DIR="./INPUTS/input"                                                  # répertoire d'input
INPUT_FILE="${INPUT_DIR}/input_file.tsv"                                    # ficher d'input TSV
DIR_VCFS="/ngs/datagen/diagho/DIAGHO-UPLOADER/input_biofiles"               # répertoire où sont stockés les VCFs
OUTPUT_DIR="./OUTPUTS/${BATCHID}"                                            # répertoire de sortie
OUTPUT_PREFIX="${BATCHID}"                                                  # préfix fichiers de sortie (par défaut BATCHID)

mkdir -p $OUTPUT_DIR


# Exemple :
BATCHID="TEST-GM"
INPUT_DIR="/ngs/datagen/diagho/DIAGHO-CREATE-INPUTS/INPUTS"
INPUT_FILE="${INPUT_DIR}/diagho_TEST-GM.tsv"
DIR_VCFS="/ngs/datagen/diagho/DIAGHO-UPLOADER/input_biofiles"
OUTPUT_DIR="/ngs/datagen/diagho/DIAGHO-CREATE-INPUTS/OUTPUTS/${BATCHID}"
OUTPUT_PREFIX="${BATCHID}" 
mkdir -p $OUTPUT_DIR

# Script :
python ./diagho-create-inputs/diagho-create-inputs.py \
    --input_file $INPUT_FILE \
    --output_directory $OUTPUT_DIR \
    --output_prefix $OUTPUT_PREFIX \
    --vcfs_directory $DIR_VCFS
