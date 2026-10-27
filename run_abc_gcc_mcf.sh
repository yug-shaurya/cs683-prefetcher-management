#!/usr/bin/env bash
set -euo pipefail

PROJECT="$HOME/Documents/CS683/ipop_project"
CHAMPSIM="$PROJECT/champsim"
TRACE_DIR="$PROJECT/traces"

run_abc() {
    local benchmark="$1"
    local -a matches

    mapfile -t matches < <(
        find "$TRACE_DIR" -maxdepth 1 -type f \
            -iname "*${benchmark}*.champsimtrace.xz" | sort
    )

    if [[ "${#matches[@]}" -ne 1 ]]; then
        echo "ERROR: Expected exactly one ${benchmark} trace; found ${#matches[@]}."
        printf '  %s\n' "${matches[@]}"
        return 1
    fi

    local trace="${matches[0]}"
    local filename
    filename="$(basename "$trace" .champsimtrace.xz)"

    local result_dir="$CHAMPSIM/results/$filename/ABC"
    local result="$result_dir/$filename.ABC.json"
    local log="$CHAMPSIM/run_logs/$filename.ABC.log"

    mkdir -p "$result_dir" "$CHAMPSIM/run_logs"

    if [[ -e "$result" ]]; then
        echo "SKIPPING: Existing result will not be overwritten:"
        echo "$result"
        return 0
    fi

    echo
    echo "Running ABC on $filename"
    echo "Trace: $trace"
    echo "Result: $result"
    echo "Log: $log"

    "$CHAMPSIM/bin/champsim_abc" \
        --warmup-instructions 100000 \
        --simulation-instructions 1000000 \
        --json "$result" \
        "$trace" 2>&1 | tee "$log"

    python3 -m json.tool "$result" > /dev/null
    echo "SUCCESS: $filename"
}

run_abc gcc
run_abc mcf

echo
echo "ABC simulations finished successfully or existing results were skipped."
