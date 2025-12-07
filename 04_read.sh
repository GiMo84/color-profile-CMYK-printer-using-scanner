#!/usr/bin/env bash
set -e
source env.sh

PAGE_COUNT=$(ls "$SCAN_DIR"/${SESSION}_scan_*.tiff 2>/dev/null | wc -l)
if [ "$PAGE_COUNT" -lt 1 ]; then
    echo "No scanned pages found in $SCAN_DIR"
    exit 1
fi

echo "Found $PAGE_COUNT scanned pages."

for ((i=1; i<=PAGE_COUNT; i++)); do
    SCANFILE="${SCAN_DIR}/${SESSION}_scan_$(printf "%02d" $i).tiff"

    if [ "$i" -eq 1 ]; then
        CHOICE="-c"
        CHTFILE="${SESSION}.cht"
    else
        CHOICE="-ca"
        CHTFILE="${SESSION}_$(printf "%02d" $i).cht"
    fi

    echo ""
    echo "============================================================="
    echo "Reading page $i using scanin"
    echo "  scan file : $SCANFILE"
    echo "  chart file: $CHTFILE"
    echo "============================================================="
    echo ""

    # --- First attempt: no -F override ---
    scanin -v -dipoan \
        $CHOICE \
        "$SCANFILE" \
        "$CHTFILE" \
        "$SCANNER_ICC" \
        "$SESSION"

    STATUS=$?
    if [ "$STATUS" -eq 0 ]; then
        echo "Page $i read successfully."
        continue
    fi

    echo ""
    echo "*************************************************************"
    echo "** scanin FAILED for page $i (exit status: $STATUS)."
    echo "** Likely cause: bad fiducials or scan misalignment."
    echo "*************************************************************"
    echo ""

    # Loop until successful or user aborts
    while true; do
        echo "You must now provide the pixel coordinates of the 4 chart fiducials."
        echo ""
        echo "Format: X1,Y1,X2,Y2,X3,Y3,X4,Y4"
        echo ""
        echo "Meaning:"
        echo "  X1,Y1 = top-left fiducial"
        echo "  X2,Y2 = top-right fiducial"
        echo "  X3,Y3 = bottom-right fiducial"
        echo "  X4,Y4 = bottom-left fiducial"
        echo ""
        echo "Example: 191,245,6852,242,6860,4772,195,4774"
        echo ""

        read -p "Enter 8 coordinates (or 'q' to abort this page): " COORDS

        if [[ "$COORDS" == "q" ]]; then
            echo "User aborted correction for page $i."
            exit 1
        fi

        echo ""
        echo "Re-running scanin with:"
        echo "  -F $COORDS"
        echo ""

        scanin -v -dipoan -F "$COORDS" \
            $CHOICE \
            "$SCANFILE" \
            "$CHTFILE" \
            "$SCANNER_ICC" \
            "$SESSION"

        STATUS=$?

        if [ "$STATUS" -eq 0 ]; then
            echo ""
            echo "Page $i successfully corrected and read!"
            break
        fi

        echo ""
        echo "scanin FAILED again (exit $STATUS)."
        echo "Try new coordinates or inspect the scan."
        echo ""
    done

done

echo ""
echo "=== All pages processed successfully. ==="
