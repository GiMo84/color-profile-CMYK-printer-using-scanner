#!/usr/bin/env bash
source env.sh

psfile="${SESSION}.ps"
echo "Printing $psfile to printer: $PRINTER_NAME"
lpr -P "$PRINTER_NAME" "$psfile"
