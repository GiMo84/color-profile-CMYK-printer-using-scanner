#!/usr/bin/env bash
source env.sh

echo "Generating patches for $SESSION..."
targen $TARGEN_OPTS "$SESSION"

printtarg -v -s -r -iSS -R0 -pA4R "$SESSION"
