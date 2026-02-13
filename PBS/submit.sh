#!/bin/bash
# Usage: ./PBS/submit.sh <pbs_script> [-v VAR=val,...] [extra qsub args]
#
# Examples:
#   ./PBS/submit.sh PBS/rectangle_area_baseline.pbs
#   ./PBS/submit.sh coderewrite/pbs/run_test.pbs -v EDIT=edit_single

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
