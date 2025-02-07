# Diagho Uploader

## Description

Upload automatiqsé des fichiers **biofiles** (SNV, CNV) dans Diagho.



## Pré-requis

- Fichier TSV contenant les informations de chaque sample.
- Colonnes attendues :


| **Colonne**              | **Description** |
|--------------------------|----------------|
| `filename`              | Nom du fichier VCF ou BED |
| `checksum`              | Checksum du fichier |
| `file_type`             | Type de fichier : SNV ou CNV |
| `assembly`              | Version du génome de référence utilisée : GRCh37 ou GRCh38 |
| `sample`                | ID du sample |
| `bam_path`              | Chemin du fichier BAM |
| `family_id`            | ID de la famille de l'échantillon |
| `person_id`            | ID unique de l'induvidu |
| `father_id`            | ID du père |
| `mother_id`            | ID de la mère |
| `sex`                  | Sexe de l'individu (`male`/`female`/`unknown`). |
| `is_affected`          | Indique si l'individu est atteint (`1 = affecté`, `0 = non affecté`). |
| `first_name`           | Prénom |
| `last_name`            | Nom de famille |
| `date_of_birth`        | Date de naissance (format `JJ/MM/AAAA`) |
| `hpo`                  | Termes HPO associés |
| `interpretation_title` | Titre de l'interprétation Diagho |
| `is_index`             | Indique si l'individu est le cas index de la famille (`1 = oui`, `0 = non`). |
| `project`              | Nom du projet |
| `assignee`             | Utilisateur assignée à l'analyse (peut être vide) |
| `priority`             | Niveau de priorité de l'analyse (ex. `1 = haute priorité`, `2 = normale`, etc.) |
| `person_note`          | Notes ou remarques concernant l'individu |
| `data_title`           | Titre des données de l'analyse |


## Installation

- Cloner le repo

```bash
git clone https://github.com/DiaghoProject/diagho-uploader.git

cd diagho-uploader/diagho_project

# Create venv
python -m venv venv

# Activate venv
source venv/bin/activate

# Install dependences
pip install -r requirements.txt

# Copy config file
cp config/config.yaml.example config.yaml

```

- Renseigner le fichier de config : `config.yaml`

### Start uploader

```
# Activate python venv
source venv/bin/activate

cd diagho_project

# Start file_watcher
python main.py start_file_watcher
```

### Start in background

```
# Activate python venv
source venv/bin/activate

cd diagho_project

nohup python main.py start_file_watcher
```

## Usage

- Déposer les fichiers VCF/BED dans : `input_biofiles`
- Déposer les fichiers TSV ou JSON dans : `input_data`

### Pipeline

- Si un fichier TSV est déposé : il va être converti en JSON
- A partir du JSON : récupération des **biofiles** et import dans Diagho
- Si tous les biofiles sont importés : chargement du JSON dans Diagho (création des familles et des interprétations)

### Troubleshooting

- Alertes par mail : renseigner les adresses email dans la config
- Logs : définir le répertoire des logfiles dans la config



