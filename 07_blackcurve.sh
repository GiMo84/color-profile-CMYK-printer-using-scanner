#!/usr/bin/env bash
set -e
source env.sh

if [ -z "$1" ]; then
    echo "Usage: $0 \"-kp a b c d e\""
    exit 1
fi

KARG="$1"

echo "$KARG" > "$K_CURVE_STORE"
echo "Saved K curve to $K_CURVE_STORE"

echo "Opening black curve preview with:"
echo "xicclu -g $KARG -l$INK_LIMIT_PROFILE -fif -ir ${SESSION}_t.icc"

xicclu -g $KARG -l$INK_LIMIT_PROFILE -fif -ir "${SESSION}_t.icc" &
