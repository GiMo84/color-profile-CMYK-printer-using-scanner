#!/usr/bin/env bash
set -e
source env.sh

PSFILE="${SESSION}.ps"
SCANSET="$SCAN_SETTING_FILE"

if [ ! -f "$PSFILE" ]; then
    echo "ERROR: PostScript file $PSFILE not found."
    exit 1
fi

# --- Detect page count by counting "showpage" tokens in postscript ---
PAGE_COUNT=$(grep -c "showpage" "$PSFILE")
if [ "$PAGE_COUNT" -eq 0 ]; then
    echo "Could not auto-detect page count. Defaulting to 1."
    PAGE_COUNT=1
fi

echo "Detected $PAGE_COUNT target page(s)."

# Allow user override
read -p "Press Enter to accept ($PAGE_COUNT pages), or type a number: " OVERRIDE
if [[ "$OVERRIDE" =~ ^[0-9]+$ ]]; then
    PAGE_COUNT=$OVERRIDE
fi

echo ""
echo "=== Starting MultiScan auto-scan for $PAGE_COUNT page(s) ==="
echo "Using Scan Setting File: $SCANSET"
echo ""

# --- Scan each page ---
for ((i=1; i<=PAGE_COUNT; i++)); do
    OUTFILE="${SCAN_DIR}/${SESSION}_scan_$(printf "%02d" $i)"
    echo "Scanning page $i → ${OUTFILE}"
    
    multi_scan.sh -n 4 -s "${SCANSET}" -r "${OUTFILE}_"
    
    scanlinecal.py process-stack ${OUTFILE}_*.tiff "${OUTFILE}.tiff"
    
    rm ${OUTFILE}_*.tiff
    
    echo "Saved: $OUTFILE.tiff"
done

echo ""
echo "=== All pages scanned ==="
