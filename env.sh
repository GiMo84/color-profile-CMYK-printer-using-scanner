#!/usr/bin/env bash

### GLOBAL SETTINGS #############################################################
export PRINTER_NAME="EPSON_XP-970_Series"
export PRINTER_FRIENDLY="EPSON XP-970"
export PRINTER_MANUFACTURER="EPSON"
export INKSET="InkTec"
export PAPER="Plain"
export RESOLUTION="720dpi"

### PROFILE SESSION #############################################################
# A unique session name
export SESSION="Plain720_CMYK_unc"

### TARGEN SETTINGS #############################################################
export INK_LIMIT_PRINT="260"
export INK_LIMIT_PROFILE="225"
export INK_LIMIT_PROFILE_BLACK="100"
export TARGEN_OPTS="-v -d4 -G -s27 -g27 -p2.0 -f1026 -O -l${INK_LIMIT_PRINT}"

### SCAN SETTINGS ###############################################################
export SCANNER_NOISE="2.0"
export SCANNER_ICC="./icc/EPSON XP-970 colorimeter B0 C0 G2_2.icc"
export SCAN_DIR="scans"
mkdir -p "$SCAN_DIR"

### EpsonScan2 settings #########################################################
export SCAN_SETTING_FILE="ScanSettings.SF2"

### Storage for last-used black curve
export K_CURVE_STORE="K_CURVE.conf"

### PROFILE OUTPUT ##############################################################
export TARGET_PROFILE_NAME="${PRINTER_FRIENDLY}, ${INKSET} ink, ${PAPER} paper, ${RESOLUTION}, CMYK, Uncorrected.icc"
export DEFAULT_LINK_PROFILE="/usr/share/color/icc/compatibleWithAdobeRGB1998.icc"
