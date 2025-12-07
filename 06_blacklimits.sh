#!/usr/bin/env bash
set -e
source env.sh

echo "=== MIN BLACK (leave window open) ==="
xicclu -g -kz -l$INK_LIMIT_PROFILE -fif -ir "${SESSION}_t.icc" &

echo "=== MAX BLACK (leave window open) ==="
xicclu -g -kx -l$INK_LIMIT_PROFILE -fif -ir "${SESSION}_t.icc" &

echo ""
echo "Adjust limits interactively, then run 07_blackcurve.sh."
