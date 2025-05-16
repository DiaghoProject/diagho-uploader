#!/bin/bash

START=false
STOP=false
FORCE=false
UPDATE=false
DEBUG=false
STATUS=false


while [[ $# -gt 0 ]]; do
  case "$1" in
    --start)
      START=true
      shift
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --stop)
      STOP=true
      shift
      ;;
    --update)
      UPDATE=true
      shift
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    --status)
      STATUS=true
      shift
      ;;
    *)
      echo "Option inconnue : $1"
      exit 1
      ;;
  esac
done


#--------------

# source venv
source venv/bin/activate

# PID (pour tester si process actif)
SCRIPT_NAME=$(basename "$0")
PID_FILE="${SCRIPT_NAME}.pid"

# Start watcher
if [ "$START" = true ]; then
  echo "
  #################################
  #        START WATCHER          #
  #################################
  "

  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Le script est déjà en cours d'exécution avec le PID $(cat "$PID_FILE")."
    exit 1
  fi

  # Debug mode (not started in background)
  if [ "$DEBUG" = true ]; then

    echo "
    #################################
    #        START WATCHER          #
    #################################
    > DEBUG
    "
    python main.py start_file_watcher
  
  else

    nohup python main.py start_file_watcher &

    # Ecrire le PID dans le fichier
    echo $! > "$PID_FILE"
    echo "Script lancé avec le PID $(cat "$PID_FILE")."

  fi
fi

# Stop watcher (+/- forcer l'arrêt du process)
if [ "$STOP" = true ]; then
  echo "
  #################################
  #        STOP WATCHER           #
  #################################
  "

  # Arrêt du watcher avec le flag
  touch stop_watcher.flag

  # Si "force" : kill le process
  if [ "$FORCE" = true ] && [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    PID=$(cat "$PID_FILE")
    echo "Option --force activée. Arrêt forcé..."
    kill "$PID"
    echo "Processus $PID terminé de force."
  fi

  # Suppression du fichier car plus de process actif
  rm -f "$PID_FILE"

fi

# Update script from Github
if [ "$UPDATE" = true ]; then
  
  # Arrêt du watcher
  echo "
  #################################
  #        STOP WATCHER           #
  #################################
  "
  touch stop_watcher.flag

  # Pull
  echo "
  #################################
  #        UPDATE                 #
  #################################
  "
  git pull

  # Start watcher
  echo "
  #################################
  #        START WATCHER          #
  #################################
  "
  nohup python main.py start_file_watcher &

fi

# Status

if [ "$STATUS" = true ]; then

 if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Le script est en cours d'exécution avec le PID $(cat "$PID_FILE")."
  else
    echo "Le script n'est pas en cours d'exécution."
  fi

fi