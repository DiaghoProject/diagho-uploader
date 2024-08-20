#! /bin/bash
source /home/${USER}/miniconda3/etc/profile.d/conda.sh
conda activate python-3.10

# Arguments:
BATCHID="TEST"                                                              # utilisé pour nommer les fichiers de sortie
INPUT_DIR="/ngs/datagen/diagho/cytogen/tsv2json/input"                      # répertoire d'input
INPUT_FILE="${INPUT_DIR}/test.tsv"                                          # ficher d'input TSV
DIR_VCFS="/ngs/datagen/diagho/DIAGHO-UPLOADER/input_biofiles"               # répertoire où sont stockés les VCFs
OUTPUT_DIR="/ngs/datagen/diagho/cytogen/tsv2json/output/${BATCHID}"         # répertoire de sortie
OUTPUT_PREFIX="${BATCHID}"                                                  # préfix fichiers de sortie (par défaut BATCHID)

mkdir -p $OUTPUT_DIR

# Script :
python /home/nouyou/pipelines/diagho-uploader/diagho_tsv2json/diagho_tsv2json.py \
    --input_file $INPUT_FILE \
    --output_directory $OUTPUT_DIR \
    --output_prefix $OUTPUT_PREFIX \
    --vcfs_directory $DIR_VCFS
