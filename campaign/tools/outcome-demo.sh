#!/usr/bin/env bash
# Shows that the runner tells the outcomes of a run apart, on constructed
# runs of the case studies:
# - timeout: jsmn-main with a limit of 1 s, at which the watchdog fires;
# - oom: jsmn-main with an address-space limit of 550 MB, at which Frama-C
#   reports that memory is exhausted;
# - error: 2048 with -eva-stop-at-nth-alarm 1, which aborts the analysis;
# - killed: jsmn-main killed with SIGKILL from outside the watchdog after
#   1.5 s. The demonstration cannot make the out-of-memory killer of the
#   system act, so there is no evidence of it, and the cause is unknown.
# None of these runs is retried.
#
# Usage: outcome-demo.sh OUTPUT TEST_CHECKOUT [SWITCH]
# Prints one line per run: expected outcome, observed outcome, PASS or FAIL.
set -euo pipefail
campaign=$(dirname "$(dirname "$(realpath "$0")")")
output=$(realpath -m "${1:?Supply a fresh output directory}")
checkout=$(realpath "${2:?Supply the Frama-C build}")
switch=${3:-$checkout}
mkdir "$output"
printf 'jsmn/jsmn-main.eva/default\n' > "$output/jsmn-main.txt"
printf '2048/2048.eva/default\n' > "$output/2048.txt"
runner=(bash "$campaign/run-campaign.sh" --modes nocache
        --test-checkout "$checkout" --switch "$switch")

"${runner[@]}" --cases "$output/jsmn-main.txt" --timeout 1 \
  "$output/timeout" > "$output/timeout.log" 2>&1
"${runner[@]}" --cases "$output/jsmn-main.txt" --timeout 120 \
  --memory-limit 550000000 "$output/oom" > "$output/oom.log" 2>&1
"${runner[@]}" --cases "$output/2048.txt" --timeout 120 \
  --extra-eva-flags '-eva-stop-at-nth-alarm 1' \
  "$output/error" > "$output/error.log" 2>&1

# Kills the Eva invocation of the run, found by its working directory.
"${runner[@]}" --cases "$output/jsmn-main.txt" --timeout 120 \
  "$output/killed" > "$output/killed.log" 2>&1 &
runner_pid=$!
killed=false
for _ in $(seq 1 600); do
  for pid in $(pgrep -x frama-c || true); do
    cwd=$(readlink "/proc/$pid/cwd" || true)
    if [[ $cwd == "$output/killed/"* ]] &&
       tr '\0' ' ' < "/proc/$pid/cmdline" | grep -q -- ' -eva '; then
      sleep 1.5
      kill -KILL "$pid" 2> /dev/null && killed=true
    fi
  done
  if $killed || ! kill -0 "$runner_pid" 2> /dev/null; then break; fi
  sleep 0.1
done
wait "$runner_pid" || true

status=0
: > "$output/summary.tsv"
for expected in timeout oom error killed; do
  run_tsv=$(echo "$output/$expected/runs/"*/*.eva/default/nocache/run.tsv)
  observed=$(awk -F'\t' '$1=="outcome"{print $2}' "$run_tsv")
  verdict=PASS
  if [[ $observed != "$expected" ]]; then verdict=FAIL; status=1; fi
  field() { awk -F'\t' -v k="$1" '$1==k{print $2}' "$run_tsv"; }
  printf '%s\texpected %s\tobserved %s\texit %s\tsignal %s\twatchdog %s\toom_evidence %s\telapsed_s %s\n' \
    "$verdict" "$expected" "$observed" "$(field exit)" "$(field signal)" \
    "$(field watchdog)" "$(field oom_evidence)" "$(field elapsed_s)" \
    >> "$output/summary.tsv"
done
cat "$output/summary.tsv"
exit "$status"
