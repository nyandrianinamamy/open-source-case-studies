#!/usr/bin/env bash
# The jsmn memexec pilot, run by the campaign runner: jsmn-main.eva and
# jsmn-example.eva, with memexec (cache) and with caching disabled
# (nocache), at the case-study revision of campaign/manifest.tsv.
# Usage: stage1-pilot.sh /absolute/fresh/output
# FRAMA_C_CHECKOUT names the Frama-C build (default ~/Project/frama-c), and
# FRAMA_C_SWITCH its opam switch (default: the local switch of the build).
# See campaign/README.md for the layout of the output.
set -euo pipefail
oscs=$(dirname "$(realpath "$0")")
output=$(realpath -m "${1:?Supply a fresh output directory}")
cases=$(mktemp)
trap 'rm -f "$cases"' EXIT
printf 'jsmn/jsmn-main.eva/default\njsmn/jsmn-example.eva/default\n' > "$cases"
checkout=${FRAMA_C_CHECKOUT:-$HOME/Project/frama-c}
bash "$oscs/campaign/run-campaign.sh" --cases "$cases" --modes nocache,cache \
  --test-checkout "$checkout" --switch "${FRAMA_C_SWITCH:-$checkout}" "$output"
