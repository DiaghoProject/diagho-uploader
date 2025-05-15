#!/bin/bash

START=false
STOP=false
FORCE=false
UPDATE=false


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
    *)
      echo "Option inconnue : $1"
      exit 1
      ;;
  esac
done


# Start watcher
if [ "$START" = true ]; then
  bash start_uploader.sh
fi

# Stop watcher (+/- forcer l'arrêt du process)
if [ "$STOP" = true ]; then
  if [ "$FORCE" = true ]; then
    bash stop_uploader.sh 1
  else
    bash stop_uploader.sh 0
  fi
fi

# Update script from Github
if [ "$UPDATE" = true ]; then
  bash update.sh
fi
