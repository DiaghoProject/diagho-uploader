# Diagho Uploader

## Description

Upload automatisé des fichiers **biofiles** (SNV, CNV) et des informations patients associées, dans Diagho.



## Input file (TSV) : samples informations

- Fichier tabulé contenant les informations de chaque sample.
- Colonnes attendues :


| **Colonne**              | **Description** |
|--------------------------|----------------|
| **filename**             | Nom du fichier VCF ou BED |
| **checksum**             | Checksum du fichier (optionnel) |
| **file_type**            | Type de fichier : SNV ou CNV |
| **assembly**             | Version du génome de référence utilisée : GRCh37 ou GRCh38 |
| **sample**               | ID du sample |
| **bam_path**             | Chemin du fichier BAM (optionnel) |
| **family_id**            | ID de la famille |
| **person_id**            | ID unique de l'individu |
| **father_id**            | ID du père |
| **mother_id**            | ID de la mère |
| **sex**                  | Sexe de l'individu (`male`/`female`/`unknown`). |
| **is_affected**          | Indique si l'individu est atteint (`1 = affecté`, `0 = non affecté`). |
| **first_name**           | Prénom (optionnel) |
| **last_name**            | Nom de famille (optionnel) |
| **date_of_birth**        | Date de naissance (format `JJ/MM/AAAA`) |
| **hpo**                  | Termes HPO associés (optionnel) |
| **interpretation_title** | Titre de l'interprétation Diagho |
| **is_index**             | Indique si l'individu est le cas index de la famille (`1 = oui`, `0 = non`). |
| **project**              | Nom du projet |
| **assignee**             | Utilisateur assignée à l'analyse (optionnel) |
| **priority**             | Niveau de priorité de l'analyse (ex. `1 = low`, `2 = normal`, `3 = high`, etc.) (défaut = 2) |
| **person_note**          | Notes ou remarques concernant l'individu (optionnel) |
| **data_title**           | Titre des données de l'analyse (optionnel) |


## Installation et configuration


### Pré-requis

Créer 2 répertoires :
- **input_biofiles** : va contenir les fichiers VCF et BED
- **input_data** : va contenir les fichiers TSV (informations sur les échantillons)


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
cp config/config.yaml.example config/config.yaml
```


### Configuration

- Compléter le fichier `config.yaml` :
  - **input_data** : répertoire d'input des fichier TSV
  - **input_biofiles** : répertoire d'input des biofiles (VCF, BED,...)
  - **backup_data** : backup fichiers TSV (une fois chargé)
  - **backup_biofiles**: backup biofiles (une fois chargé)
  - **logging > log_directory** : répertoire des fichiers de logs
  - **emails**
    - **recipients** : liste des adresses emails pour recevoir les mails d'info/alerte (si plusieurs : `"user1@example.com,user2@example.com"`)
    - **send_mail_flag** : mettre à `1` pour activer l'envoi de mail, sinon `0` pour désactiver

  - **diagho_api** : renseigner les informations de connexion à l'API
  - **accessions** : indiquer les ID d'accession pour GRCh37 et GRCh38



## Start watcher

### Start in background

```bash
bash diagho_uploader.sh --start
```

### Start in debug mode

Affichage des logs dans le terminal.

```bash
bash diagho_uploader.sh --start --debug
```

## Stop watcher

```bash
bash diagho_uploader.sh --stop
```

### Forcer l'arrêt de l'uploader (kill le process si en cours)

```bash
bash diagho_uploader.sh --stop --force
```


## Update

```bash
bash diagho_uploader.sh --update
```

## Check status

Indique si l'uploader est en cours.

```bash
bash diagho_uploader.sh --status
```