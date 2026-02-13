#!/bin/bash
# Usage: ./PBS/submit.sh <pbs_script> [-v VAR=val,...] [extra qsub args]
#
# Examples:
#   ./PBS/submit.sh PBS/run_baseline.pbs -v EXPERIMENT=rectangle_area,OUTPUT_DIR=results/rectangle_area/baseline
#   ./PBS/submit.sh PBS/run_test.pbs -v EXPERIMENT=rectangle_area,EDIT=edit_single,TARGET_NEW="width ** height",OUTPUT_DIR=results/rectangle_area/edit_pow

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env.sh"

PBS_SCRIPT="$1"; shift
JOB_NAME=$(basename "$PBS_SCRIPT" .pbs)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUT_DIR="${PBS_OUT_DIR:-$HOME/pbs_out}"
mkdir -p "$OUT_DIR"

qsub -o "$OUT_DIR/${JOB_NAME}_${TIMESTAMP}.out" \
     -e "$OUT_DIR/${JOB_NAME}_${TIMESTAMP}.err" \
     "$@" \
     "$PBS_SCRIPT"
