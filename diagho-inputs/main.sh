#! /bin/bash
source /home/${USER}/miniconda3/etc/profile.d/conda.sh
source diagho-inputs/config.sh

# Arguments:
BATCHID="EXOME-71"
INPUT_FILE="${DIR_DIAGHO}/cytogen/input_files/${BATCHID}/diagho_${BATCHID}.json"
OUTPUT_DIR="${DIR_DIAGHO}/cytogen/input_files/${BATCHID}/"
OUTPUT_PREFIX="${BATCHID}"

DIR_VCFS="${DIR_DIAGHO}/DIAGHO-UPLOADER/input_biofiles"
TARGET_DIRECTORY="${DIR_DIAGHO}/DIAGHO-UPLOADER/input_data"




# Script :
conda activate python-3.10

python /ngs/datagen/cytogen/SCRIPTS/package_diagho_input_files/diagho_input_files/diagho_tsv2json.py \
    --input_file $INPUT_FILE \
    --input_type "json" \
    --output_directory $OUTPUT_DIR \
    --output_prefix $OUTPUT_PREFIX \
    --vcfs_directory $DIR_VCFS \
    --target_directory $TARGET_DIRECTORY
