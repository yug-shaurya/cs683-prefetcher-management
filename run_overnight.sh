#!/usr/bin/env bash
set -uo pipefail
cd ~/Documents/CS683/ipop_project/champsim
WARM=10000000
SIM=50000000
OUT=../results_ckpt2
mkdir -p "$OUT/logs" "$OUT/windows"

run_one() {
  local tag=$1; local bin=$2; local k=$3; local tr=$4; shift 4
  local json="$OUT/${k}.${tag}.json"
  if [[ -e "$json" ]]; then echo "skip $k $tag"; return 0; fi
  echo "=== $k $tag start $(date +%H:%M:%S) ==="
  env "$@" IPOP_LOG="$OUT/windows/${k}.${tag}.csv" stdbuf -oL ./bin/$bin \
    --warmup-instructions $WARM --simulation-instructions $SIM \
    --json "$json" "../traces/${tr}.champsimtrace.xz" \
    > "$OUT/logs/${k}.${tag}.log" 2>&1
  if [[ $? -ne 0 ]]; then echo "FAILED $k $tag"; rm -f "$json"; return 0; fi
  echo "=== $k $tag done $(date +%H:%M:%S) ==="
}

for t in "gcc 602.gcc_s-2226B" "mcf 605.mcf_s-782B" "lbm 619.lbm_s-2676B" "xz 657.xz_s-2302B"; do
  set -- $t
  K=$1; TR=$2
  run_one R1 champsim_ip_stride "$K" "$TR" &
  run_one R2 champsim_next_line "$K" "$TR" &
  run_one R3 champsim_spp_dev   "$K" "$TR" &
  run_one R4 champsim_abc       "$K" "$TR" &
  run_one A1 champsim_ipop "$K" "$TR" IPOP_POLICY=accuracy IPOP_ADAPTIVE=0 IPOP_WINDOW=1024 &
  run_one A2 champsim_ipop "$K" "$TR" IPOP_POLICY=accuracy IPOP_ADAPTIVE=1 IPOP_WINDOW=1024 &
  run_one A3 champsim_ipop "$K" "$TR" IPOP_POLICY=pe IPOP_ADAPTIVE=0 IPOP_WINDOW=1024 IPOP_PE_UP=20 IPOP_PE_DOWN=5 &
  run_one A4 champsim_ipop "$K" "$TR" IPOP_POLICY=pe IPOP_ADAPTIVE=1 IPOP_WINDOW=1024 IPOP_PE_UP=20 IPOP_PE_DOWN=5 IPOP_DELTA_HI=5 IPOP_DELTA_LO=1 &
  run_one S2048 champsim_ipop "$K" "$TR" IPOP_POLICY=pe IPOP_ADAPTIVE=0 IPOP_WINDOW=2048 IPOP_PE_UP=20 IPOP_PE_DOWN=5 &
  run_one S4096 champsim_ipop "$K" "$TR" IPOP_POLICY=pe IPOP_ADAPTIVE=0 IPOP_WINDOW=4096 IPOP_PE_UP=20 IPOP_PE_DOWN=5 &
  run_one S8192 champsim_ipop "$K" "$TR" IPOP_POLICY=pe IPOP_ADAPTIVE=0 IPOP_WINDOW=8192 IPOP_PE_UP=20 IPOP_PE_DOWN=5 &
  wait
  echo "--- trace $K complete $(date +%H:%M:%S) ---"
done
echo "ALL DONE $(date +%H:%M:%S)"
