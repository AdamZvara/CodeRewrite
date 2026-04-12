#!/bin/bash
# Usage: ./PBS/submit.sh <pbs_script> [-v VAR=val,...] [extra qsub args]
#
# Examples:
#   ./PBS/submit.sh PBS/run_baseline.pbs -v EXPERIMENT=rectangle_area,OUTPUT_DIR=results/rectangle_area/baseline
#   ./PBS/submit.sh PBS/run_edit.pbs -v EXPERIMENT=rectangle_area,EDIT=edit_single,OUTPUT_DIR=results/rectangle_area/edit_pow
#   ./PBS/submit.sh PBS/run_external_model.pbs -v EXPERIMENT=rectangle_area,EDIT=edit_single,MODEL_PATH=/path/to/model,OUTPUT_DIR=results/rectangle_area/edit_pow

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

# Append EXPERIMENT/EDIT/EDIT_CNT/DATASET_CONFIG when present (from merged -v vars)
EXPERIMENT=$(printf '%s' "$ENV_VARS" | sed -n 's/.*\bEXPERIMENT=\([^,]*\).*/\1/p')
EDIT=$(printf '%s' "$ENV_VARS" | sed -n 's/.*\bEDIT=\([^,]*\).*/\1/p')
MODEL_HPARAMS=$(printf '%s' "$ENV_VARS" | sed -n 's/.*\bHPARAMS=\([^,]*\).*/\1/p')
EDIT_CNT=$(printf '%s' "$ENV_VARS" | sed -n 's/.*\bEDIT_CNT=\([^,]*\).*/\1/p')
DATASET_CONFIG=$(printf '%s' "$ENV_VARS" | sed -n 's/.*\bDATASET_CONFIG=\([^,]*\).*/\1/p')
if [[ -n "$EXPERIMENT" ]]; then
    JOB_NAME+="_${EXPERIMENT}"
fi
if [[ -n "$EDIT" ]]; then
    JOB_NAME+="_${EDIT}"
fi
if [[ -n "$MODEL_HPARAMS" ]]; then
    KE_METHOD=$(basename "$(dirname "$MODEL_HPARAMS")")
    if [[ -n "$KE_METHOD" ]]; then
        JOB_NAME+="_${KE_METHOD}"
    fi
fi
if [[ -n "$DATASET_CONFIG" ]]; then
    JOB_NAME+="_${DATASET_CONFIG}"
fi
if [[ -n "$EDIT_CNT" ]]; then
    JOB_NAME+="_n${EDIT_CNT}"
fi

qsub -o "$OUT_DIR/${JOB_NAME}_${TIMESTAMP}.out" \
     -e "$OUT_DIR/${JOB_NAME}_${TIMESTAMP}.err" \
     -v "$ENV_VARS" \
     "${ARGS[@]}" \
     "$PBS_SCRIPT"
