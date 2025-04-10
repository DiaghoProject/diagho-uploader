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



## Start uploader

```
# Activate python venv
=======
- Compléter le fichier `config.yaml` :
  - **input_data**: répertoire des fichiers JSON
  - **input_biofiles**: répertoire des biofiles (VCF, BED...)
  - **backup_data_files**: backup JSON (une fois chargé)
  - **backup_biofiles**: backup biofiles (une fois chargé)
  - **emails > recipients** : liste des adresses emails pour recevoir les mails d'info/alerte
    - si plusieurs : `"user1@example.com,userb@example.com"`
  - **diagho_api** : renseigner les informations de connexion à l'API
  - **accessions** : indiquer l'ID d'accession pour GRCh37 et GRCh38



<br>
<br>

## Utilisation

### Pré-requis

Créer 2 répertoires :
- **input_biofiles** : va contenir les fichiers VCF et BED
- **input_data** : va contenir les fichiers JSON (informations sur les échantillons)

<br>
<br>

### Etape 1 : création du fichier JSON d'input

- Template TSV
- Colonnes :

| Column name   | Content       |
| ------------- | ------------- |
| id            | identifiat unique  |
| filename      | Nom du fichier (VCF ou BED) |
| checksum	    | Checksum du fichier (optionnel) |
| file_type     | **SNV** ou **CNV** |
| assembly      | **GRCh37** ou **GRCh38** |
| sample        | ID du sample |
| bam_path      | Chemin du fichier bam |
| family_id     | ID de la famille | 
| person_id	    | ID du patient | 
| father_id	    | ID père |
| mother_id	    | ID mère |
| sex           | **female** ou **male** ou **unknown** |
| is_affected   | boolean : 0 , 1 |
| first_name    | Prénom |
| last_name     | Nom de famille | 
| date_of_birth | Date de naissance | 
| hpo           | Codes HPO (séparateur ` ; `) (optionnel) | 
| interpretation_title | Titre de l'interprétation ; exemple `Family_ID (Cas_Index_ID)` |
| is_index      | boolean : 0 , 1 |
| project       | Nom du projet |
| assignee      | Username de l'assigné (optionnel) | 
| priority      | 0, 1, 2, 3, 4 (optionnel) |
| person_note   | Texte (optionnel) |
| data_title    | Titre de l'onglet de données SNV ou CNV (optionnel) |


- Création du fichier JSON :
```bash




