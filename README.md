# Diagho Uploader

## Description

Upload automatisé des fichiers **biofiles** (SNV, CNV) dans Diagho.



## Pré-requis

- Fichier tabulé contenant les informations de chaque sample.
- Colonnes attendues :


| **Colonne**              | **Description** |
|--------------------------|----------------|
| `filename`              | Nom du fichier VCF ou BED |
| `checksum`              | Checksum du fichier (optionnel) |
| `file_type`             | Type de fichier : SNV ou CNV |
| `assembly`              | Version du génome de référence utilisée : GRCh37 ou GRCh38 |
| `sample`                | ID du sample |
| `bam_path`              | Chemin du fichier BAM (optionnel) |
| `family_id`            | ID de la famille de l'échantillon |
| `person_id`            | ID unique de l'induvidu |
| `father_id`            | ID du père |
| `mother_id`            | ID de la mère |
| `sex`                  | Sexe de l'individu (`male`/`female`/`unknown`). |
| `is_affected`          | Indique si l'individu est atteint (`1 = affecté`, `0 = non affecté`). |
| `first_name`           | Prénom (optionnel) |
| `last_name`            | Nom de famille (optionnel) |
| `date_of_birth`        | Date de naissance (format `JJ/MM/AAAA`) |
| `hpo`                  | Termes HPO associés (optionnel) |
| `interpretation_title` | Titre de l'interprétation Diagho |
| `is_index`             | Indique si l'individu est le cas index de la famille (`1 = oui`, `0 = non`). |
| `project`              | Nom du projet |
| `assignee`             | Utilisateur assignée à l'analyse (optionnel) |
| `priority`             | Niveau de priorité de l'analyse (ex. `1 = haute priorité`, `2 = normale`, etc.) (défaut = 2) |
| `person_note`          | Notes ou remarques concernant l'individu (optionnel) |
| `data_title`           | Titre des données de l'analyse (optionnel) |


## Installation et configuration


### Pré-requis

Créer 2 répertoires :
- **input_biofiles** : va contenir les fichiers VCF et BED
- **input_data** : va contenir les fichiers TSV (informations sur les échantillons)


### Installation 

- Cloner le repo

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
cp config/config.yaml.example config/config.yaml
```


### Configuration

- Compléter le fichier `config.yaml` :
  - **input_data** : répertoire d'input des fichier TSV
  - **input_biofiles** : répertoire d'input des biofiles (VCF, BED,...)
  - **backup_data** : backup fichiers TSV (une fois chargé)
  - **backup_biofiles**: backup biofiles (une fois chargé)
  - **logging > log_directory** : répertoire des fichiers de logs
  - **emails > recipients** : liste des adresses emails pour recevoir les mails d'info/alerte
    - si plusieurs : `"user1@example.com,userb@example.com"`
  - **diagho_api** : renseigner les informations de connexion à l'API
  - **accessions** : indiquer l'ID d'accession pour GRCh37 et GRCh38



## Start watcher

```bash
bash diagho_uploader --start
```



## Stop watcher

```bash
bash diagho_uploader --stop
```

### Forcer le stop de l'uploader (kill le process si en cours)

```bash
bash diagho_uploader --stop --force
```


## Update

```bash
bash diagho_uploader --update
```
