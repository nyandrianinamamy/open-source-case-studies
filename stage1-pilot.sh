#!/usr/bin/env bash
# The jsmn memexec pilot, run by the campaign runner: jsmn-main.eva and
# jsmn-example.eva, with memexec (cache) and with caching disabled
# (nocache), at the case-study revision of campaign/manifest.tsv.
# Usage: stage1-pilot.sh /absolute/fresh/output
# FRAMA_C_CHECKOUT names the Frama-C build (default ~/Project/frama-c), and
# FRAMA_C_SWITCH its opam switch (default: the local switch of the build).
# CAMPAIGN_RUNNER replaces campaign/run-campaign.sh, for the tests of this
# script. See campaign/README.md for the layout of the output.
# Exits with 1 unless each of the four runs completed.
set -euo pipefail
oscs=$(dirname "$(realpath "$0")")
output=$(realpath -m "${1:?Supply a fresh output directory}")
cases=$(mktemp)
trap 'rm -f "$cases"' EXIT
printf 'jsmn/jsmn-main.eva/default\njsmn/jsmn-example.eva/default\n' > "$cases"
checkout=${FRAMA_C_CHECKOUT:-$HOME/Project/frama-c}
runner=${CAMPAIGN_RUNNER:-$oscs/campaign/run-campaign.sh}
bash "$runner" --cases "$cases" --modes nocache,cache \
  --test-checkout "$checkout" --switch "${FRAMA_C_SWITCH:-$checkout}" "$output"
status=0
while IFS= read -r id; do
  for mode in nocache cache; do
    run_tsv="$output/runs/$id/$mode/run.tsv"
    outcome=$(awk -F'\t' '$1=="outcome"{print $2}' "$run_tsv" 2> /dev/null || true)
    if [[ $outcome != completed ]]; then
      printf 'FAIL %s %s: outcome %s\n' "$id" "$mode" "${outcome:-missing}" >&2
      status=1
    fi
  done
done < "$cases"
exit "$status"
