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

# Forward core .env variables to the PBS job
ENV_VARS="PROJECT_ROOT=$PROJECT_ROOT"
ENV_VARS+=",HF_HOME=$HF_HOME"
ENV_VARS+=",DATADIR=$DATADIR"
ENV_VARS+=",CONDA_ENV=$CONDA_ENV"
ENV_VARS+=",MODEL_NAME=$MODEL_NAME"
ENV_VARS+=",HPARAMS=$HPARAMS"

# Merge user -v variables into ENV_VARS so qsub gets a single -v flag
ARGS=()
for arg in "$@"; do
    if [[ "$prev" == "-v" ]]; then
        ENV_VARS+=",$arg"
        prev=""
        continue
    fi
    if [[ "$arg" == "-v" ]]; then
        prev="-v"
        continue
    fi
    prev=""
    ARGS+=("$arg")
done

qsub -o "$OUT_DIR/${JOB_NAME}_${TIMESTAMP}.out" \
     -e "$OUT_DIR/${JOB_NAME}_${TIMESTAMP}.err" \
     -v "$ENV_VARS" \
     "${ARGS[@]}" \
     "$PBS_SCRIPT"
