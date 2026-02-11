#!/usr/bin/env bash
set -e
source env.sh

iccgamut -v -w -k -d 5 -ip "$TARGET_PROFILE_NAME"

xicclu -g -fb -ir "$TARGET_PROFILE_NAME"
