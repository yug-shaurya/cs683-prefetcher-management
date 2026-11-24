#!/usr/bin/env bash
set -uo pipefail
cd ~/Documents/CS683/ipop_project/champsim
WARM=10000000
SIM=50000000
OUT=../results_ckpt2
mkdir -p "$OUT/logs"

run_one() {
  local k=$1
  local tr=$2
  local json="$OUT/${k}.R0.json"
  if [[ -e "$json" ]]; then echo "skip $k"; return 0; fi
  echo "=== R0 $k start $(date +%H:%M:%S) ==="
  stdbuf -oL ./bin/champsim_baseline \
    --warmup-instructions $WARM --simulation-instructions $SIM \
    --json "$json" "../traces/${tr}.champsimtrace.xz" \
    > "$OUT/logs/${k}.R0.log" 2>&1
  if [[ $? -ne 0 ]]; then echo "FAILED $k"; rm -f "$json"; return 0; fi
  echo "=== R0 $k done $(date +%H:%M:%S) ==="
}

run_one gcc 602.gcc_s-2226B &
run_one mcf 605.mcf_s-782B &
run_one lbm 619.lbm_s-2676B &
run_one xz  657.xz_s-2302B &
wait
echo "ALL R0 DONE $(date +%H:%M:%S)"
