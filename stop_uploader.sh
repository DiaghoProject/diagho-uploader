#!/bin/bash

echo "
################################
#        STOP WATCHER          #
################################

"

FORCE=$1

CMD="python main.py start_file_watcher"
PID=$(pgrep -f "$CMD")

if [[ -n "$PID" ]]; then

    # Arrêt du watcher
    touch stop_watcher.flag

    # Forcer l'arrêt de l'uploader (si en cours d'upload)
    if [[ "${FORCE:-}" == 1 ]]; then 
        echo "Force stop uploader"

        echo "Process found with PID: $PID"
        echo "Kill process..."

        kill -9 $PID

        echo "Process $PID terminated."
    fi

else
    echo "No process found for: $CMD"
fi

