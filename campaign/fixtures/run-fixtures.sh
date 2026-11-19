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
# (cache) and with memexec again (cache.2). Each run lists its AST from a
# parse alone (ast.tsv), as the runner lists it from the parse session, and
# from the session saved by Eva (ast-eva.tsv). The parse alone runs as the
# runner runs the parse step, with -keep-temp-files and -kernel-msg-key pp
# and a temporary directory of its own, and its run.tsv records the digest
# of the first listing and the digests of the preprocessing (campaign.py
# preprocessing), which the comparisons take as evidence that two runs
# number the statements alike (campaign.py compare). Checks:
# - every run: the two listings of its AST have the same digest, and the
#   run has the digests of its preprocessing.
# - nested-hit.c: the per-call records of cache and cache.2 align
#   completely, with equal digests; between nocache and cache, the second
#   call to outer is reported as analysed in one run and a hit in the other,
#   and the two calls to leaf nested in it as nested under a hit, not
#   aligned. With the unused macro UNUSED set to 0 (unused0) and to 1
#   (unused1), the two runs have equal AST digests and their preprocessing
#   differs: the calls below the entry point are not aligned.
# - frame.c: the state queries show the difference of the example run of
#   issue #3: before "r = 0;" in get, the raw answers are {3} in both runs
#   for the first call, {5} with caching disabled and none with memexec for
#   the second call, and over all callstacks {3; 5} with caching disabled
#   against {3} with memexec, which the comparison reports as narrower. At
#   the exit of get, r is {0}. With -eva-no-results (noresults), no state
#   is saved, and with -eva-no-results-domain cvalue (nodomain), no state of
#   the domain cvalue: no query is answered, each one, the exit queries
#   included, is written unavailable for that reason, and the done line
#   counts these lines.
# - same-line.c, analysed with memexec as it is (entry) and with -lib-entry
#   (libentry): the two runs parse the same program and the numbering is
#   the same; the second run reaches a second call of the line, which the
#   alignment reports as unmatched, not aligned with the first.
# - sites.c, analysed twice with memexec, with SIDE 0 (side0) and SIDE 1
#   (side1): the macro is the condition of the two calls, so the two runs
#   give one statement number to different calls; the digests differ, and
#   the alignment leaves the calls undecided and is not complete. The
#   queries under the callstack of that call are unpaired, not compared,
#   and the comparison of the queries is not complete.
# - branches.c, analysed as sites.c: if (SIDE) f(1); else f(1); on one line.
#   The statement lines of the two listings differ in the columns only, the
#   digests differ, and the calls are not aligned.
# - header.c, analysed as sites.c: the macro sets the initial value of a
#   global of the included header.h. The two listings differ in that global
#   only, the digests differ, and the calls are not aligned.
# - every run, in the tables of campaign.py tables: the statistics file is
#   a complete export, the log has one analysis start, and the rows of the
#   file and the disposition lines of the log give the same number for
#   every kind that both count. For nested-hit.c, the hit with memexec is a
#   row of the file and a line of the log; with caching disabled the file
#   has no memexec row (-) and the log no hit line (0 among its lines).
# The outcome of a run is completed only when its records show the analysed
# call of main (campaign.py invocation-outcome).
# Prints one line per check, PASS or FAIL, and exits with 1 if one fails.
set -euo pipefail
fixtures=$(dirname "$(realpath "$0")")
campaign=$(dirname "$fixtures")
tool=(python3 -I "$campaign/tools/campaign.py")
output=$(realpath "${1:?Supply the campaign output directory}")
tools=$(realpath "${2:?Supply the prepared tools directory}")
checkout=$(realpath "${3:?Supply the Frama-C build}")
bin="$checkout/_build/install/default/bin/frama-c"
revision=$("${tool[@]}" binaries-get "$output/provenance/binaries.tsv" revision --role test)

status=0
check() {
  local name=$1; shift
  if "$@"; then printf 'PASS %s\n' "$name"
  else printf 'FAIL %s\n' "$name"; status=1; fi
}

families=$("${tool[@]}" binaries-get "$output/provenance/binaries.tsv" counter_families --role test)
share=$(
  while IFS= read -r setting; do export "$setting"; done < "$tools/sites.env"
  "$bin" -print-share-path
)
for fixture in frame nested-hit same-line sites branches header; do
  modes=(nocache cache cache.2)
  case $fixture in
    frame) modes+=(noresults nodomain) ;;
    nested-hit) modes+=(unused0 unused1) ;;
    same-line) modes=(entry libentry) ;;
    sites|branches|header) modes=(side0 side1) ;;
  esac
  for mode in "${modes[@]}"; do
    case "$mode" in
      nocache|noresults|nodomain) flag=-eva-no-memexec ;;
      *) flag=-eva-memexec ;;
    esac
    cpp=() extra=()
    case "$mode" in
      side0|side1) cpp=(-cpp-extra-args=-DSIDE=${mode#side}) ;;
      unused0|unused1) cpp=(-cpp-extra-args=-DUNUSED=${mode#unused}) ;;
      noresults) extra=(-eva-no-results) ;;
      nodomain) extra=(-eva-no-results-domain cvalue) ;;
      libentry) extra=(-lib-entry) ;;
    esac
    case_id="fixtures/$fixture.c/default"
    run="$output/runs/$case_id/$mode"
    mkdir -p "$run/pp"
    cp "$fixtures/$fixture.c" "$run/"
    if [[ -f $fixtures/$fixture.h ]]; then cp "$fixtures/$fixture.h" "$run/"; fi
    (
      cd "$run"
      while IFS= read -r setting; do export "$setting"; done < "$tools/sites.env"
      TMPDIR="$run/pp" CAMPAIGN_AST_OUT=ast.tsv "$bin" -keep-temp-files \
        -kernel-msg-key pp "$fixture.c" "${cpp[@]}" \
        -load-module "$tools/campaign_queries.cmxs" > ast.log 2>&1
    ) || true
    "${tool[@]}" preprocessing "$run/ast.log" "$run/pp" --source-root "$run" \
      --share "$share" --commands "$run/preprocessing.txt" \
      > "$run/preprocessing.tsv"
    rm -rf -- "$run/pp"
    args=("$bin" -eva "$fixture.c" "$flag" "${cpp[@]}" "${extra[@]}"
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
      CAMPAIGN_QUERIES_OUT=queries.tsv CAMPAIGN_AST_OUT=ast-eva.tsv \
        "$bin" -load framac.sav \
        -load-module "$tools/campaign_queries.cmxs" > queries.log 2>&1
    )
    "${tool[@]}" records "$run/eva.log" "$run/records.jsonl" \
      2> "$run/records-problems.log"
    # A status of 0 does not make the run completed: its records must show
    # the analysed call of main, the entry point of every fixture.
    outcome=$("${tool[@]}" invocation-outcome "$run" "$exit_code" \
      --entry-point main | cut -f1)
    flags="${cpp[*]} ${extra[*]}"
    flags=${flags# }
    {
      printf 'case\t%s\nmode\t%s\nrole\ttest\nflag\t%s\nextra_eva_flags\t%s\nrevision\t%s\ncounter_families\t%s\nentry_point\tmain\noutcome\t%s\nexit\t%s\n' \
        "$case_id" "$mode" "$flag" "${flags:--}" "$revision" "$families" \
        "$outcome" "$exit_code"
      "${tool[@]}" ast "$run/ast.tsv"
      cat "$run/preprocessing.tsv"
    } > "$run/run.tsv"
    rm -f -- "$run/preprocessing.tsv"
    rm -f "$run/framac.sav"
    for file in eva.log records.jsonl queries.tsv ast.tsv ast-eva.tsv; do
      if [[ -f $run/$file ]]; then gzip -nf "$run/$file"; fi
    done
  done
  pairs=(nocache:cache cache:cache.2)
  case $fixture in
    frame) pairs+=(nocache:noresults nocache:nodomain) ;;
    nested-hit) pairs+=(unused0:unused1) ;;
    same-line) pairs=(entry:libentry) ;;
    sites|branches|header) pairs=(side0:side1) ;;
  esac
  for pair in "${pairs[@]}"; do
    "${tool[@]}" compare "$output" "fixtures/$fixture.c/default" \
      "${pair%%:*}" "${pair##*:}"
  done
done

value() { awk -F'\t' -v k="$2" '$1==k{print $2}' "$1"; }
cmp_dir="$output/comparisons/fixtures"

# The digest of the AST of a run listed from the parse or from the session
# saved by Eva.
digest() {
  "${tool[@]}" ast "$1" | awk -F'\t' '$1=="ast_sha256"{print $2}'
}
differing=0 listed=0
for run in "$output"/runs/fixtures/*/default/*/; do
  parse=$(digest "$run/ast.tsv.gz") eva=$(digest "$run/ast-eva.tsv.gz")
  if [[ $parse != - ]]; then listed=$((listed + 1)); fi
  if [[ $parse == - || $parse != "$eva" ]]; then differing=$((differing + 1)); fi
done
check "every run: the AST listed from the parse is the AST of the Eva session" \
  test "$listed/$differing" = "$(ls -d "$output"/runs/fixtures/*/default/*/ | wc -l)/0"
evidence=0
for run in "$output"/runs/fixtures/*/default/*/; do
  if [[ $(value "$run/run.tsv" pp_problem) == - &&
        $(value "$run/run.tsv" pp_text_sha256) =~ ^[0-9a-f]{64}$ &&
        $(value "$run/run.tsv" pp_command_sha256) =~ ^[0-9a-f]{64}$ ]]; then
    evidence=$((evidence + 1))
  fi
done
check "every run: the digests of its preprocessing are recorded" \
  test "$evidence" = "$(ls -d "$output"/runs/fixtures/*/default/*/ | wc -l)"

nested="$cmp_dir/nested-hit.c/default"
check "nested-hit: the numbering of nocache and cache is the same" \
  test "$(value "$nested/nocache-vs-cache/alignment-summary.tsv" numbering)" = same
check "nested-hit: two runs of the same binary align completely" \
  test "$(value "$nested/cache-vs-cache.2/alignment-summary.tsv" complete)" = True
check "nested-hit: the two runs have equal AST digests" \
  test "$(value "$nested/cache-vs-cache.2/alignment-summary.tsv" numbering)" = same
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
# Lines of the answer file of a run of frame.c, by kind.
lines() {
  gzip -dc "$frame_runs/$1/queries.tsv.gz" | awk -F'\t' -v k="$2" '$1==k' | wc -l
}
# The exit queries answered over all callstacks without caching, and those
# written unavailable for a reason in another run: function, statement and
# lvalue of each.
exits_answered() {
  gzip -dc "$frame_runs/nocache/queries.tsv.gz" |
    awk -F'\t' '$1=="answer" && $4=="exit" && $5=="*" {print $2, $3, $6}' | sort
}
exits_unavailable() {
  gzip -dc "$frame_runs/$1/queries.tsv.gz" |
    awk -F'\t' -v r="$2" '$1=="unavailable" && $4=="exit" && $7==r {print $2, $3, $6}' |
    sort
}
for mode in noresults nodomain; do
  case $mode in
    noresults) reason=no-results option=-eva-no-results ;;
    nodomain) reason=disabled-domain option="-eva-no-results-domain cvalue" ;;
  esac
  check "frame: with $option, no query is answered" \
    test "$(lines $mode answer)" = 0
  check "frame: with $option, every query is unavailable ($reason)" \
    test "$(gzip -dc "$frame_runs/$mode/queries.tsv.gz" |
      awk -F'\t' -v r="$reason" '$1=="unavailable" && $NF!=r' | wc -l)/$(( $(lines $mode unavailable) > 0 ))" = 0/1
  check "frame: with $option, the exit queries are written unavailable ($reason)" \
    test "$(exits_unavailable $mode $reason | tr '\n' '|')" = "$(exits_answered | tr '\n' '|')"
  check "frame: with $option, the done line counts the unavailable lines" \
    test "$(gzip -dc "$frame_runs/$mode/queries.tsv.gz" |
      awk -F'\t' '$1=="done"{print $2}')" = "$(( $(lines $mode unavailable) + $(lines $mode error) ))"
  summary="$cmp_dir/frame.c/default/nocache-vs-$mode/queries-summary.tsv"
  check "frame: the comparison with the run with $option answers nothing in it, each query for its reason" \
    test "$(value "$summary" answered_b)/$(value "$summary" complete_b)/$(value "$summary" unavailable_b_missing)/$(value "$summary" unavailable_b_no-callstack)/$(value "$summary" "unavailable_b_$reason")" \
         = "0/complete/0/0/$(value "$summary" queries)"
done
check "frame: the exit queries are answered without caching" \
  test -n "$(exits_answered)"
check "frame: the numbering of nocache and cache is the same" \
  test "$(value "$cmp_dir/frame.c/default/nocache-vs-cache/alignment-summary.tsv" numbering)" = same

unused="$cmp_dir/nested-hit.c/default/unused0-vs-unused1/alignment-summary.tsv"
unused_runs="$output/runs/fixtures/nested-hit.c/default"
check "unused macro: the two runs have equal AST digests" \
  test "$(digest "$unused_runs/unused0/ast.tsv.gz")" = "$(digest "$unused_runs/unused1/ast.tsv.gz")"
check "unused macro: the preprocessing of the two runs differs" \
  test "$(value "$unused" numbering)" = "preprocessing differs"
check "unused macro: only the entry point is aligned; the calls are undecided" \
  test "$(value "$unused" aligned)/$(value "$unused" complete)/$(tail -n +2 "${unused%summary.tsv}undecided.tsv" | cut -f8 | sort -u)" \
       = "1/False/preprocessing differs"

same_line="$cmp_dir/same-line.c/default/entry-vs-libentry/alignment-summary.tsv"
check "same-line: the two runs have the same numbering" \
  test "$(value "$same_line" numbering)" = same
check "same-line: the calls f(2) align, the call f(1) of the same line is unmatched" \
  test "$(value "$same_line" aligned)/$(value "$same_line" unmatched_a)/$(value "$same_line" unmatched_b)" = 2/0/1
check "same-line: the unmatched call is the call f(1), not the call f(2)" \
  test "$(tail -n +2 "${same_line%summary.tsv}unmatched.tsv" | cut -f2 | sed 's|.*/s\([0-9]*\)#.*|\1|')" \
       = "$(gzip -dc "$output/runs/fixtures/same-line.c/default/entry/ast.tsv.gz" |
            awk -F'\t' '$1=="stmt" && $5=="f(1);" {print $3}')"
check "same-line: the alignment is not complete" \
  test "$(value "$same_line" complete)" = False

sites="$cmp_dir/sites.c/default/side0-vs-side1/alignment-summary.tsv"
check "sites: the two runs have different AST digests" \
  test "$(value "$sites" numbering)" = different
check "sites: only the entry point is aligned; the calls are undecided" \
  test "$(value "$sites" aligned)/$(value "$sites" undecided_groups)" = 1/1
check "sites: the alignment is not complete" \
  test "$(value "$sites" complete)" = False
sites_queries="${sites%alignment-summary.tsv}queries-"
sites_call='main|f@main:9:0'
sites_asked=$(gzip -dc "$output/runs/fixtures/sites.c/default/side0/queries.tsv.gz" |
                grep -cF "$sites_call" || true)
check "sites: the queries of the call of line 9 are unpaired, not compared, and the comparison is not complete" \
  test "$(value "${sites_queries}summary.tsv" comparison)/$(grep -cF "$sites_call" "${sites_queries}differences.tsv")/$(grep -cF "$sites_call" "${sites_queries}unpaired.tsv")/$((sites_asked > 0))" \
       = "incomplete: AST digests differ/0/$sites_asked/1"

# The statement lines of a listing without their ranges, and its global
# lines.
statements() {
  gzip -dc "$1" | awk -F'\t' -v OFS='\t' '$1=="stmt" {$4=""; print}'
}
globals() { gzip -dc "$1" | awk -F'\t' '$1=="global"'; }
branch_runs="$output/runs/fixtures/branches.c/default"
branches="$cmp_dir/branches.c/default/side0-vs-side1/alignment-summary.tsv"
check "branches: the statements have the same numbers, lines and texts" \
  test "$(statements "$branch_runs/side0/ast.tsv.gz")" = "$(statements "$branch_runs/side1/ast.tsv.gz")"
check "branches: the two runs have different AST digests" \
  test "$(value "$branches" numbering)" = different
check "branches: only the entry point is aligned; the calls are undecided" \
  test "$(value "$branches" aligned)/$(value "$branches" undecided_groups)/$(value "$branches" complete)" = 1/1/False
header_runs="$output/runs/fixtures/header.c/default"
header="$cmp_dir/header.c/default/side0-vs-side1/alignment-summary.tsv"
check "header: the statement lines are the same, the global side differs" \
  test "$(statements "$header_runs/side0/ast.tsv.gz" | md5sum)/$(diff <(globals "$header_runs/side0/ast.tsv.gz") <(globals "$header_runs/side1/ast.tsv.gz") | grep -c '^[<>]')" \
       = "$(statements "$header_runs/side1/ast.tsv.gz" | md5sum)/2"
check "header: the two runs have different AST digests" \
  test "$(value "$header" numbering)" = different
check "header: only the entry point is aligned; the calls are undecided" \
  test "$(value "$header" aligned)/$(value "$header" complete)" = 1/False

# The two sources of the activity tables on the runs of the fixtures: the
# rows of the statistics file and the disposition lines of the log.
"${tool[@]}" tables "$output" > /dev/null
tables="$output/tables"
fixture_runs=$(ls -d "$output"/runs/fixtures/*/default/*/ | wc -l)
# The rows of the fixtures in a table for which an awk condition holds; the
# condition reads the column NAME as $col["NAME"].
fixture_rows() {
  awk -F'\t' 'NR==1 {for (i = 1; i <= NF; i++) col[$i] = i; next}
               $1 ~ /^fixtures\// && ('"$2"')' "$tables/$1.tsv" | wc -l
}
# The cell of a column for a run of a fixture.
table_cell() {
  awk -F'\t' -v c="fixtures/$2.c/default" -v m="$3" -v k="$4" \
    'NR==1 {for (i = 1; i <= NF; i++) if ($i == k) n = i; next}
     $1 == c && $2 == m {print $n}' "$tables/$1.tsv"
}
check "every run: the outcome is completed, with the record of main" \
  test "$(fixture_rows outcomes '$col["outcome"] == "completed"')" = "$fixture_runs"
check "every run: the statistics file is a complete export" \
  test "$(fixture_rows activity '$col["export_rows"] ~ /^[0-9]+$/')" = "$fixture_runs"
check "every run: the log has one analysis start and its disposition lines are counted" \
  test "$(fixture_rows log '$col["analysis_starts"] == 1 && $col["log_note"] == "-"')" = "$fixture_runs"
check "every run: the rows of the statistics file and the lines of the log give the same numbers" \
  test "$(fixture_rows log '$col["sources"] ~ /^agree on /')" = "$fixture_runs"
check "nested-hit: with memexec, the hit is a row of the statistics file and a line of the log" \
  test "$(table_cell activity nested-hit cache hits)/$(table_cell log nested-hit cache lookup_hit)" = 1/1
check "nested-hit: without caching, the statistics file has no memexec row and the log no hit line among its 7 disposition lines" \
  test "$(table_cell activity nested-hit nocache hits)/$(table_cell activity nested-hit nocache misses)/$(table_cell log nested-hit nocache lookup_hit)/$(table_cell log nested-hit nocache disposition_lines)" = -/-/0/7
exit "$status"
