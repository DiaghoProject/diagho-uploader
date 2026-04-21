#!/bin/bash

START=false
STOP=false
FORCE=false
UPDATE=false
DEBUG=false
STATUS=false
PARSE=false
CONFIG="config/config.yaml"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --start)
      START=true
      shift
      ;;
    --stop)
      STOP=true
      shift
      ;;
    --force)
      FORCE=true
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
    --parse)
      PARSE=true
      shift
      ;;
    --config)
      CONFIG="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

source venv/bin/activate

SCRIPT_NAME=$(basename "$0")
PID_FILE="${SCRIPT_NAME}.pid"

# --start
if [ "$START" = true ]; then
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Already running with PID $(cat "$PID_FILE")."
    exit 1
  fi

  if [ "$DEBUG" = true ]; then
    python main.py --config "$CONFIG"
  else
    nohup python main.py --config "$CONFIG" > /dev/null 2>&1 &
    disown
    echo $! > "$PID_FILE"
    echo "Started with PID $(cat "$PID_FILE")."
  fi
fi

# --stop
if [ "$STOP" = true ]; then
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    PID=$(cat "$PID_FILE")
    if [ "$FORCE" = true ]; then
      kill -9 "$PID"
      echo "Process $PID force-killed."
    else
      kill "$PID"
      echo "Shutdown signal sent to process $PID (will stop after current step)."
    fi
    rm -f "$PID_FILE"
  else
    echo "No running process found."
    rm -f "$PID_FILE"
  fi
fi

# --update: stop, pull, install deps, restart
if [ "$UPDATE" = true ]; then
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    PID=$(cat "$PID_FILE")
    kill "$PID"
    echo "Shutdown signal sent to process $PID, waiting..."
    sleep 5
    rm -f "$PID_FILE"
  fi

  echo "Pulling latest changes..."
  git pull

  echo "Installing dependencies..."
  pip install -r requirements.txt

  echo "Restarting..."
  nohup python main.py --config "$CONFIG" > /dev/null 2>&1 &
  disown
  echo $! > "$PID_FILE"
  echo "Started with PID $(cat "$PID_FILE")."
fi

# --status
if [ "$STATUS" = true ]; then
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Running with PID $(cat "$PID_FILE")."
  else
    echo "Not running."
  fi
fi

# --parse: wait for a TSV/JSON in metadata_dir, print validated JSON, exit
if [ "$PARSE" = true ]; then
  python main.py --parse --config "$CONFIG"
fi
