#!/usr/bin/env bash
# Runs the constructed cases of the campaign tools and checks what the
# tools report on them.
#
# Usage: run-fixtures.sh OUTPUT TOOLS_DIR CHECKOUT
#   OUTPUT: campaign output directory; the runs go to runs/fixtures/ and the
#           comparisons to comparisons/fixtures/
#   TOOLS_DIR: the directory where run-campaign.sh prepared the binary
#              (sites.env and campaign_queries.cmxs)
#   CHECKOUT: the Frama-C build of that binary
#
# Each fixture is analysed with caching disabled (nocache), with memexec
# (cache) and with memexec again (cache.2). Checks:
# - nested-hit.c: the per-call records of cache and cache.2 align
#   completely; between nocache and cache, the second call to outer is
#   reported as analysed in one run and a hit in the other, and the two
#   calls to leaf nested in it as nested under a hit, not aligned.
# - frame.c: the state queries show the difference of the example run of
#   issue #3: before "r = 0;" in get, over all callstacks, r is {3; 5} with
#   caching disabled and {3} with memexec, which is narrower; the callstack
#   of the second call has no answer with memexec.
# Prints one line per check, PASS or FAIL, and exits with 1 if one fails.
set -euo pipefail
fixtures=$(dirname "$(realpath "$0")")
campaign=$(dirname "$fixtures")
tool=(python3 -I "$campaign/tools/campaign.py")
output=$(realpath "${1:?Supply the campaign output directory}")
tools=$(realpath "${2:?Supply the prepared tools directory}")
checkout=$(realpath "${3:?Supply the Frama-C build}")
bin="$checkout/_build/install/default/bin/frama-c"
revision=$(awk -F'\t' '$1=="test"{print $3}' "$output/provenance/binaries.tsv")

status=0
check() {
  local name=$1; shift
  if "$@"; then printf 'PASS %s\n' "$name"
  else printf 'FAIL %s\n' "$name"; status=1; fi
}

for fixture in frame nested-hit; do
  for mode in nocache cache cache.2; do
    case "$mode" in
      nocache) flag=-eva-no-memexec ;;
      *) flag=-eva-memexec ;;
    esac
    case_id="fixtures/$fixture.c/default"
    run="$output/runs/$case_id/$mode"
    mkdir -p "$run"
    cp "$fixtures/$fixture.c" "$run/"
    args=("$bin" -eva "$fixture.c" "$flag" -eva-msg-key cache,callstacks
          -eva-statistics-file eva-stats.csv -save framac.sav)
    printf '%q ' "${args[@]}" > "$run/eva-command"
    exit_code=0
    (
      cd "$run"
      while IFS= read -r setting; do export "$setting"; done < "$tools/sites.env"
      "${args[@]}" > eva.log 2>&1
    ) || exit_code=$?
    (
      cd "$run"
      while IFS= read -r setting; do export "$setting"; done < "$tools/sites.env"
      CAMPAIGN_QUERIES_OUT=queries.tsv "$bin" -load framac.sav \
        -load-module "$tools/campaign_queries.cmxs" > queries.log 2>&1
    )
    "${tool[@]}" records "$run/eva.log" "$run/records.jsonl" \
      2> "$run/records-problems.log"
    outcome=completed
    if [[ $exit_code != 0 ]]; then outcome=error; fi
    printf 'case\t%s\nmode\t%s\nrole\ttest\nflag\t%s\nrevision\t%s\noutcome\t%s\nexit\t%s\n' \
      "$case_id" "$mode" "$flag" "$revision" "$outcome" "$exit_code" > "$run/run.tsv"
    rm -f "$run/framac.sav"
    gzip -nf "$run/eva.log" "$run/records.jsonl" "$run/queries.tsv"
  done
  for pair in nocache:cache cache:cache.2; do
    a=${pair%%:*} b=${pair##*:}
    dir="$output/comparisons/fixtures/$fixture.c/default/$a-vs-$b"
    ra="$output/runs/fixtures/$fixture.c/default/$a"
    rb="$output/runs/fixtures/$fixture.c/default/$b"
    mkdir -p "$dir"
    printf 'case\tfixtures/%s.c/default\nbaseline\t%s\ncandidate\t%s\n' \
      "$fixture" "$a" "$b" > "$dir/pair.tsv"
    "${tool[@]}" align "$ra/records.jsonl.gz" "$rb/records.jsonl.gz" \
      "$dir/alignment-" > /dev/null
    "${tool[@]}" queries "$ra/queries.tsv.gz" "$rb/queries.tsv.gz" \
      "$dir/queries-" > /dev/null
  done
done

value() { awk -F'\t' -v k="$2" '$1==k{print $2}' "$1"; }
cmp_dir="$output/comparisons/fixtures"

nested="$cmp_dir/nested-hit.c/default"
check "nested-hit: two runs of the same binary align completely" \
  test "$(value "$nested/cache-vs-cache.2/alignment-summary.tsv" complete)" = True
check "nested-hit: one call analysed without caching is a hit with memexec" \
  test "$(value "$nested/nocache-vs-cache/alignment-summary.tsv" analysed_a_hit_b)" = 1
check "nested-hit: the two nested calls are reported under the hit" \
  test "$(value "$nested/nocache-vs-cache/alignment-summary.tsv" nested_under_hit_b)" = 2
check "nested-hit: no alignment is undecided or unmatched" \
  test "$(value "$nested/nocache-vs-cache/alignment-summary.tsv" undecided_groups)/$(value "$nested/nocache-vs-cache/alignment-summary.tsv" unmatched_a)/$(value "$nested/nocache-vs-cache/alignment-summary.tsv" unmatched_b)" = 0/0/0
check "nested-hit: every record is aligned or nested under the hit" \
  test "$(value "$nested/nocache-vs-cache/alignment-summary.tsv" accounted)" = True
check "nested-hit: the nested records are the calls to leaf under the second call to outer" \
  test "$(tail -n +2 "$nested/nocache-vs-cache/alignment-under-hit.tsv" | cut -f2 | sort | tr '\n' '|')" \
       = "main#0 > outer@nested-hit.c:14#0 > leaf@nested-hit.c:9#0|main#0 > outer@nested-hit.c:14#0 > leaf@nested-hit.c:9#1|"

frame="$cmp_dir/frame.c/default/nocache-vs-cache/queries-differences.tsv"
check "frame: before r = 0, all callstacks, memexec answer {3} is narrower than {3; 5}" \
  grep -qxF "$(printf 'get\tget:11:0\tbefore\t*\tr\tnarrower\tMNULL=S3,5\tMNULL=S3')" "$frame"
check "frame: the callstack of the second call has no answer with memexec" \
  grep -qxF "$(printf 'get\tget:11:0\tbefore\tmain|get@main:21:1\tr\tunavailable in B (no-callstack)\tMNULL=S5\t')" "$frame"
check "frame: the callstack of the first call answers {3} in both runs" \
  bash -c "! grep -q \$'get\tget:11:0\tbefore\tmain|get@main:19:1\tr\t' '$frame'"
exit "$status"
