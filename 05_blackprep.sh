#!/usr/bin/env bash
set -e
source env.sh

echo "Preparing black curve base..."
cp "${SESSION}.ti3" "${SESSION}_t.ti3"

colprof -r 2.0 -v -qh -b -cmt -dpp "${SESSION}_t"

echo "Created: ${SESSION}_t.icc"
