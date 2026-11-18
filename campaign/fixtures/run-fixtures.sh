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
#   issue #3: before "r = 0;" in get, the raw answers are {3} in both runs
#   for the first call, {5} with caching disabled and none with memexec for
#   the second call, and over all callstacks {3; 5} with caching disabled
#   against {3} with memexec, which the comparison reports as narrower. At
#   the exit of get, r is {0}. With -eva-no-results (noresults), no state
#   is saved: no query is answered, each is written unavailable, and the
#   done line counts these lines.
# - same-line.c, analysed twice with memexec, with SIDE 0 (side0) and SIDE 1
#   (side1): the two runs reach different calls of one line, which the
#   alignment reports as unmatched, not aligned.
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

families=$(awk -F'\t' 'NR==1{for(i=1;i<=NF;i++)c[$i]=i;next} $1=="test"{print $c["counter_families"]}' \
  "$output/provenance/binaries.tsv")
for fixture in frame nested-hit same-line; do
  modes=(nocache cache cache.2)
  if [[ $fixture == frame ]]; then modes+=(noresults); fi
  if [[ $fixture == same-line ]]; then modes=(side0 side1); fi
  for mode in "${modes[@]}"; do
    case "$mode" in
      nocache|noresults) flag=-eva-no-memexec ;;
      *) flag=-eva-memexec ;;
    esac
    extra=()
    case "$mode" in
      side0) extra=(-cpp-extra-args=-DSIDE=0) ;;
      side1) extra=(-cpp-extra-args=-DSIDE=1) ;;
      noresults) extra=(-eva-no-results) ;;
    esac
    case_id="fixtures/$fixture.c/default"
    run="$output/runs/$case_id/$mode"
    mkdir -p "$run"
    cp "$fixtures/$fixture.c" "$run/"
    args=("$bin" -eva "$fixture.c" "$flag" "${extra[@]}"
          -eva-msg-key cache,callstacks
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
    printf 'case\t%s\nmode\t%s\nrole\ttest\nflag\t%s\nextra_eva_flags\t%s\nrevision\t%s\ncounter_families\t%s\noutcome\t%s\nexit\t%s\n' \
      "$case_id" "$mode" "$flag" "${extra[*]:--}" "$revision" "$families" \
      "$outcome" "$exit_code" > "$run/run.tsv"
    rm -f "$run/framac.sav"
    gzip -nf "$run/eva.log" "$run/records.jsonl" "$run/queries.tsv"
  done
  pairs=(nocache:cache cache:cache.2)
  if [[ $fixture == frame ]]; then pairs+=(nocache:noresults); fi
  if [[ $fixture == same-line ]]; then pairs=(side0:side1); fi
  for pair in "${pairs[@]}"; do
    a=${pair%%:*} b=${pair##*:}
    dir="$output/comparisons/fixtures/$fixture.c/default/$a-vs-$b"
    ra="$output/runs/fixtures/$fixture.c/default/$a"
    rb="$output/runs/fixtures/$fixture.c/default/$b"
    mkdir -p "$dir"
    printf 'case\tfixtures/%s.c/default\nbaseline\t%s\ncandidate\t%s\n' \
      "$fixture" "$a" "$b" > "$dir/pair.tsv"
    "${tool[@]}" align --same-numbering "$ra/records.jsonl.gz" \
      "$rb/records.jsonl.gz" "$dir/alignment-" > /dev/null
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
# The identities of the nested records, without the statement numbers: the
# two calls to leaf on line 9 are two statements, each called once.
under_hit=$(tail -n +2 "$nested/nocache-vs-cache/alignment-under-hit.tsv" |
  cut -f2 | sed 's|/s[0-9]*#|#|g' | sort | tr '\n' '|')
check "nested-hit: the nested records are the calls to leaf under the second call to outer" \
  test "$under_hit" \
       = "main#0 > outer@nested-hit.c:14#0 > leaf@nested-hit.c:9#0|main#0 > outer@nested-hit.c:14#0 > leaf@nested-hit.c:9#0|"

# Raw answers of the query r before "r = 0;" (statement get:11:0) in each
# run: the lines of the answer files, not the comparison.
frame_runs="$output/runs/fixtures/frame.c/default"
raw() {
  gzip -dc "$frame_runs/$1/queries.tsv.gz" |
    awk -F'\t' -v cs="$2" '$1=="answer" && $3=="get:11:0" && $4=="before" && $5==cs && $6=="r" {print $9}'
}
check "frame: first call, raw answer {3} without caching" \
  test "$(raw nocache 'main|get@main:19:1')" = MNULL=S3
check "frame: first call, raw answer {3} with memexec" \
  test "$(raw cache 'main|get@main:19:1')" = MNULL=S3
check "frame: second call, raw answer {5} without caching" \
  test "$(raw nocache 'main|get@main:21:1')" = MNULL=S5
check "frame: second call, no raw answer with memexec" \
  test -z "$(raw cache 'main|get@main:21:1')"
check "frame: all callstacks, raw answer {3; 5} without caching" \
  test "$(raw nocache '*')" = MNULL=S3,5
check "frame: all callstacks, raw answer {3} with memexec" \
  test "$(raw cache '*')" = MNULL=S3
frame="$cmp_dir/frame.c/default/nocache-vs-cache/queries-differences.tsv"
check "frame: before r = 0, all callstacks, memexec answer {3} is narrower than {3; 5}" \
  grep -qxF "$(printf 'get\tget:11:0\tbefore\t*\tr\tnarrower\tMNULL=S3,5\tMNULL=S3')" "$frame"
check "frame: the callstack of the second call has no answer with memexec" \
  grep -qxF "$(printf 'get\tget:11:0\tbefore\tmain|get@main:21:1\tr\tunavailable in B (no-callstack)\tMNULL=S5\t')" "$frame"
check "frame: the callstack of the first call answers {3} in both runs" \
  bash -c "! grep -q \$'get\tget:11:0\tbefore\tmain|get@main:19:1\tr\t' '$frame'"

check "frame: at the exit of get, r is {0} without caching" \
  test "$(gzip -dc "$frame_runs/nocache/queries.tsv.gz" |
    awk -F'\t' '$1=="answer" && $3=="get:exit" && $4=="exit" && $5=="*" && $6=="r" {print $9}')" = MNULL=S0
# Lines of the answer file of the run without saved results, by kind.
lines() {
  gzip -dc "$frame_runs/noresults/queries.tsv.gz" | awk -F'\t' -v k="$1" '$1==k' | wc -l
}
check "frame: with -eva-no-results, no query is answered" \
  test "$(lines answer)" = 0
check "frame: with -eva-no-results, the queries are unavailable for lack of results" \
  test "$(gzip -dc "$frame_runs/noresults/queries.tsv.gz" |
    awk -F'\t' '$1=="unavailable" && $NF!="no-results"' | wc -l)/$(( $(lines unavailable) > 0 ))" = 0/1
check "frame: with -eva-no-results, the done line counts the unavailable lines" \
  test "$(gzip -dc "$frame_runs/noresults/queries.tsv.gz" |
    awk -F'\t' '$1=="done"{print $2}')" = "$(( $(lines unavailable) + $(lines error) ))"
noresults="$cmp_dir/frame.c/default/nocache-vs-noresults/queries-summary.tsv"
check "frame: the comparison with the run without results answers nothing in it" \
  test "$(value "$noresults" answered_b)/$(value "$noresults" complete_b)" = 0/complete

same_line="$cmp_dir/same-line.c/default/side0-vs-side1/alignment-summary.tsv"
check "same-line: the two calls of line 10 are unmatched, not aligned" \
  test "$(value "$same_line" aligned)/$(value "$same_line" unmatched_a)/$(value "$same_line" unmatched_b)" = 1/1/1
check "same-line: the alignment is not complete" \
  test "$(value "$same_line" complete)" = False
exit "$status"
