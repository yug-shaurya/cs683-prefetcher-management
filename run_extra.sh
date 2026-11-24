#!/usr/bin/env bash
set -uo pipefail
cd ~/Documents/CS683/ipop_project/champsim
WARM=10000000
SIM=50000000
OUT=../results_ckpt2
mkdir -p "$OUT/logs" "$OUT/windows"

run_one() {
  local tag=$1; local k=$2; local tr=$3; shift 3
  local json="$OUT/${k}.${tag}.json"
  if [[ -e "$json" ]]; then echo "skip $k $tag"; return 0; fi
  echo "=== $k $tag start $(date +%H:%M:%S) ==="
  env "$@" IPOP_LOG="$OUT/windows/${k}.${tag}.csv" stdbuf -oL ./bin/champsim_ipop \
    --warmup-instructions $WARM --simulation-instructions $SIM \
    --json "$json" "../traces/${tr}.champsimtrace.xz" \
    > "$OUT/logs/${k}.${tag}.log" 2>&1
  if [[ $? -ne 0 ]]; then echo "FAILED $k $tag"; rm -f "$json"; return 0; fi
  echo "=== $k $tag done $(date +%H:%M:%S) ==="
}

# Experiment 1: does the PE controller act on lbm with a reachable threshold?
run_one T1 lbm 619.lbm_s-2676B \
  IPOP_POLICY=pe IPOP_ADAPTIVE=0 IPOP_WINDOW=1024 IPOP_PE_UP=2 IPOP_PE_DOWN=-2 &
run_one T1a lbm 619.lbm_s-2676B \
  IPOP_POLICY=pe IPOP_ADAPTIVE=1 IPOP_WINDOW=1024 IPOP_PE_UP=2 IPOP_PE_DOWN=-2 \
  IPOP_DELTA_HI=5 IPOP_DELTA_LO=1 &

# Experiment 2: is the 256-access window floor binding?
run_one W64 mcf 605.mcf_s-782B \
  IPOP_POLICY=pe IPOP_ADAPTIVE=1 IPOP_WINDOW=1024 IPOP_WMIN=64 \
  IPOP_PE_UP=20 IPOP_PE_DOWN=5 IPOP_DELTA_HI=5 IPOP_DELTA_LO=1 &
run_one W64 lbm 619.lbm_s-2676B \
  IPOP_POLICY=pe IPOP_ADAPTIVE=1 IPOP_WINDOW=1024 IPOP_WMIN=64 \
  IPOP_PE_UP=2 IPOP_PE_DOWN=-2 IPOP_DELTA_HI=5 IPOP_DELTA_LO=1 &
run_one W64 xz 657.xz_s-2302B \
  IPOP_POLICY=pe IPOP_ADAPTIVE=1 IPOP_WINDOW=1024 IPOP_WMIN=64 \
  IPOP_PE_UP=20 IPOP_PE_DOWN=5 IPOP_DELTA_HI=5 IPOP_DELTA_LO=1 &
run_one W64 gcc 602.gcc_s-2226B \
  IPOP_POLICY=pe IPOP_ADAPTIVE=1 IPOP_WINDOW=1024 IPOP_WMIN=64 \
  IPOP_PE_UP=20 IPOP_PE_DOWN=5 IPOP_DELTA_HI=5 IPOP_DELTA_LO=1 &
wait
echo "EXTRA DONE $(date +%H:%M:%S)"
