#!/usr/bin/env bash
# The pilot of the campaign: memexec against caching disabled on the cases of
# pilot-cases.txt, the constructed cases of fixtures/, and the outcome
# classes of the runner. Writes the result tables to OUTPUT/tables/.
#
# Usage: pilot.sh OUTPUT TEST_CHECKOUT REFERENCE_CHECKOUT [SWITCH]
#   OUTPUT: fresh directory for the logs and tables
#   TEST_CHECKOUT, REFERENCE_CHECKOUT: Frama-C builds (see run-campaign.sh)
#   SWITCH: opam switch of the builds (default: local switch of the test
#           checkout)
# Environment: PILOT_TIMEOUT, wall-time limit of each Eva invocation in
# seconds (default 180); PILOT_MEMORY_LIMIT, address-space limit of each Eva
# invocation in bytes (default 8000000000).
#
# Modes: nocache and cache with the binary under test, cache a second time
# (cache.2), and reference. Runs are serial; nothing is retried.
set -euo pipefail
campaign=$(dirname "$(realpath "$0")")
output=$(realpath -m "${1:?Supply a fresh output directory}")
test_checkout=$(realpath "${2:?Supply the build under test}")
reference_checkout=$(realpath "${3:?Supply the reference build}")
switch=${4:-$test_checkout}

bash "$campaign/run-campaign.sh" --cases "$campaign/pilot-cases.txt" \
  --modes nocache,cache,reference --repeat cache \
  --timeout "${PILOT_TIMEOUT:-180}" \
  --memory-limit "${PILOT_MEMORY_LIMIT:-8000000000}" \
  --test-checkout "$test_checkout" \
  --reference-checkout "$reference_checkout" --switch "$switch" "$output"

status=0
bash "$campaign/fixtures/run-fixtures.sh" "$output" "$output/tools/test" \
  "$test_checkout" > "$output/fixtures.txt" || status=1
bash "$campaign/tools/outcome-demo.sh" "$output/outcome-demo" \
  "$test_checkout" "$switch" > "$output/outcome-demo.txt" || status=1

python3 -I "$campaign/tools/campaign.py" tables "$output" \
  --recorded-set-a "$campaign/reference/set-a-recorded.tsv" > /dev/null
{
  printf '## Checks on the constructed cases\n\n```\n'
  cat "$output/fixtures.txt"
  printf '```\n\n## Outcome classes of the runner\n\n'
  printf 'Constructed runs of tools/outcome-demo.sh, caching disabled.\n\n```\n'
  cat "$output/outcome-demo.txt"
  printf '```\n'
} >> "$output/tables/tables.md"
printf 'Tables: %s/tables/tables.md\n' "$output"
exit "$status"
