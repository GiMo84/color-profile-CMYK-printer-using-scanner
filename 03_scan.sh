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
echo "=== Starting EpsonScan2 auto-scan for $PAGE_COUNT page(s) ==="
echo "Using Scan Setting File: $SCANSET"
echo ""

# Ensure setting file exists
if [ ! -f "$SCANSET" ]; then
    echo "ScanSetting file '$SCANSET' missing."
    echo "Create one using:  epsonscan2 --create   or   epsonscan2 --edit file.SF2"
    exit 1
fi

# Determine scanner automatically
SCANNER_ID=$(epsonscan2 -l | grep "device ID :" | awk '{split($0,a,":"); print a[2]}')
if [ -z "$SCANNER_ID" ]; then
    echo "No Epson scanner found!"
    exit 1
fi
echo "Using scanner: $SCANNER_ID"
echo ""

# --- Scan each page ---
for ((i=1; i<=PAGE_COUNT; i++)); do
    OUTFILE="${SCAN_DIR}/${SESSION}_scan_$(printf "%02d" $i).tiff"
    echo "Scanning page $i → $OUTFILE"

    epsonscan2 --scan "$SCANNER_ID" "$SCANSET"

    # EpsonScan2 always writes to whatever path is stored inside .SF2,
    # so we must move the resulting file here:
    RAW_OUTPUT=$(ls -t *.tif *.tiff 2>/dev/null | head -n 1)
    if [ -z "$RAW_OUTPUT" ]; then
        echo "ERROR: No TIFF detected after scanning!"
        exit 1
    fi

    mv "$RAW_OUTPUT" "$OUTFILE"
    echo "Saved: $OUTFILE"
done

echo ""
echo "=== All pages scanned ==="
