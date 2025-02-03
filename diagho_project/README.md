# Diagho Uploader

## Description


## Usage

### 1. Création du fichier JSON

#### Pré-requis

- Fichier TSV contenant les informations de famille, sample, ... formaté comme ceci :

TODO

#### Usage 

```
# Activate python venv
source venv/bin/activate

cd diagho_project

# Script
INPUT_TSV=xxxxxx
OUTPUT_JSON=xxxxxx

python main.py create_inputs \
    --input_file $INPUT_TSV \
    --output_file $OUTPUT_JSON
```


### 2. Upload des fichiers VCF/BED

#### Pré-requis 

- Fichiers VCF/BED déposés dans : `input_biofiles`
- Fichier JSON déposé dans : `input_data`

#### Usage 

```
# Activate python venv
source venv/bin/activate

cd diagho_project

# Start watcher 
python main.py start_file_watcher

# Start watcher in background
nohup python main.py start_file_watcher &
```
