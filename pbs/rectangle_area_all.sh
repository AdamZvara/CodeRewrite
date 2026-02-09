#!/bin/bash
# Submit all rectangle_area jobs.
# The edit jobs depend on the baseline finishing first (optional —
# they are independent, but this keeps logs tidy).
#
# Usage:  bash pbs/rectangle_area_all.sh

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p logs

BASELINE=$(qsub "$DIR/rectangle_area_baseline.pbs")
echo "Submitted baseline: $BASELINE"

POW=$(qsub -W depend=afterok:$BASELINE "$DIR/rectangle_area_edit_pow.pbs")
echo "Submitted edit_pow:  $POW"

ADD=$(qsub -W depend=afterok:$BASELINE "$DIR/rectangle_area_edit_add.pbs")
echo "Submitted edit_add:  $ADD"

SUB=$(qsub -W depend=afterok:$BASELINE "$DIR/rectangle_area_edit_sub.pbs")
echo "Submitted edit_sub:  $SUB"

echo "All jobs submitted."
