#! /bin/bash

###########################################################################
#
# Exemple pour lancer le script d'import dans Diagho
#
###########################################################################

# Si besoin : créer un venv
# Create venv
python -m venv venv
# Activate venv
source venv/bin/activate
# Install dependences
pip install -r requirements.txt




source venv/bin/activate

DT=$(date +"%Y%m%d_%H%M%S")
LOGFILE=./logs/nohup.${DT}.log

nohup python ./diagho-uploader/file_watcher.py > $LOGFILE 2>&1 &

