#!/usr/bin/env bash
PIDFILE="/dev/shm/whistle.pid"
AUDIO="/dev/shm/whistle.wav"
PIPE="/dev/shm/whistle.pipe"

flash() {
    local urgency="$1"
    local text="$2"
    if command -v dunstify >/dev/null 2>&1; then
        dunstify -r 9123 -u "$urgency" -t 600 "$text"
    else
        notify-send -u "$urgency" -t 600 -h string:x-canonical-private-synchronous:whistle "$text"
    fi
}

if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    kill -2 "$PID" 2>/dev/null
    rm -f "$PIDFILE"
    flash normal "PROCESSING"
    sleep 0.05
    if [ -p "$PIPE" ]; then
        echo "$AUDIO" > "$PIPE"
    fi
else
    flash critical "RECORDING"
    if command -v pw-record >/dev/null 2>&1; then
        pw-record --rate 16000 --channels 1 "$AUDIO" &
    else
        arecord -f S16_LE -r 16000 -c 1 "$AUDIO" &
    fi
    echo $! > "$PIDFILE"
fi
