#!/usr/bin/env bash
set -e
source env.sh

echo "Preparing black curve base..."
cp "${SESSION}.ti3" "${SESSION}_t.ti3"

colprof -r $SCANNER_NOISE -v -qm -l $INK_LIMIT_PROFILE -L $INK_LIMIT_PROFILE_BLACK -b -cmt -dpp "${SESSION}_t"

echo "Created: ${SESSION}_t.icc"
