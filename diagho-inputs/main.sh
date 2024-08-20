#! /bin/bash
source /home/${USER}/miniconda3/etc/profile.d/conda.sh
source diagho-inputs/config.sh

# Arguments:
BATCHID="EXOME-78"
INPUT_FILE="${DIR_DIAGHO}/cytogen/input_files/${BATCHID}/diagho_${BATCHID}.json"
OUTPUT_DIR="${DIR_DIAGHO}/cytogen/input_files/${BATCHID}/"
OUTPUT_PREFIX="${BATCHID}"

DIR_VCFS="${DIR_DIAGHO}/DIAGHO-UPLOADER/input_biofiles"
TARGET_DIRECTORY="${DIR_DIAGHO}/DIAGHO-UPLOADER/input_data"


# BATCHID="TEST"
# INPUT_FILE="/ngs/datagen/diagho/cytogen/input_files/${BATCHID}/diagho_${BATCHID}.json"
# INPUT_FILE="/ngs/datagen/diagho/cytogen/input_files/TEST/test2.tsv"
# DIR_VCFS="/ngs/datagen/diagho/DIAGHO-UPLOADER/input_biofiles"
# OUTPUT_DIR="/ngs/datagen/diagho/cytogen/input_files/${BATCHID}/"
# OUTPUT_PREFIX="${BATCHID}"
# TARGET_DIRECTORY="/ngs/datagen/diagho/DIAGHO-UPLOADER/input_data"


# Script :
conda activate python-3.10

python /home/nouyou/pipelines/diagho-uploader/diagho-inputs/diagho_inputs.py \
    --input_file $INPUT_FILE \
    --input_type "tsv" \
    --output_directory $OUTPUT_DIR \
    --output_prefix $OUTPUT_PREFIX \
    --vcfs_directory $DIR_VCFS \
    --target_directory $TARGET_DIRECTORY
