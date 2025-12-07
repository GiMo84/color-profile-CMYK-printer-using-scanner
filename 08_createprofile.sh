#!/usr/bin/env bash
set -e
source env.sh

if [ ! -f "$K_CURVE_STORE" ]; then
    echo "ERROR: No K curve stored. Run 07_blackcurve.sh first."
    exit 1
fi

K_CURVE=$(cat "$K_CURVE_STORE")

colprof -r 2.0 -v \
    -A "$PRINTER_MANUFACTURER" \
    -M "$PRINTER_FRIENDLY" \
    -D "$TARGET_PROFILE_NAME" \
    -C "Dr.G" \
    -qh \
    $K_CURVE \
    -l$INK_LIMIT_PROFILE \
    -S "$DEFAULT_LINK_PROFILE" \
    -cmt -dpp \
    -O "$TARGET_PROFILE_NAME" \
    "$SESSION"
