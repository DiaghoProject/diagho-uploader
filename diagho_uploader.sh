#!/bin/bash

START=false
STOP=false
FORCE=false
UPDATE=false
DEBUG=false


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
    *)
      echo "Option inconnue : $1"
      exit 1
      ;;
  esac
done


#--------------

# source venv
source venv/bin/activate

# Start watcher
if [ "$START" = true ]; then
  echo "
  #################################
  #        START WATCHER          #
  #################################
  "

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

  fi
fi

# Stop watcher (+/- forcer l'arrêt du process)
if [ "$STOP" = true ]; then
  echo "
  #################################
  #        STOP WATCHER           #
  #################################
  "
  CMD="python main.py start_file_watcher"
  PID=$(pgrep -f "$CMD")

  # Arrêt du watcher
  touch stop_watcher.flag

  if [ "$FORCE" = true ]; then
    echo "> FORCE"
    echo " "
    
    echo "Process found with PID: $PID"
    echo "Kill process..."

    kill -9 $PID

    echo "Process $PID terminated."

  fi
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
