# diagho-uploader


## Table des Matières

1. [Installation](#installation)
2. [Utilisation](#utilisation)

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


## Utilisation

```bash

source venv/bin/activate

python diagho-uploader/file_watcher.py 

```

2 répertoires :
- **input_biofiles** : va contenir les VCF.gz
- **input_data** : va contenir les fichiers JSON (informations sur les échantillons)


- Déposer un fichier **file.json** dans le répertoire **input_data**
- **input_data** doit contenir aussi les fichiers JSON : families + interpretations (1 fichier par famille/interpretation)