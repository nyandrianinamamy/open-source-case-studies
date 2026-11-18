#!/usr/bin/env bash
# Runs cases of the campaign manifest in the modes of the campaign, then
# compares the runs of each case and writes the result tables.
#
# Usage: run-campaign.sh [OPTIONS] OUTPUT
#
#   OUTPUT                  fresh directory for the logs and tables
#   --manifest FILE         manifest of the cases (campaign/manifest.tsv)
#   --cases FILE            case identifiers to run, one per line
#                           (default: every case of the manifest)
#   --modes LIST            comma-separated modes, among
#                           cache:     the binary under test, -eva-memexec
#                           nocache:   the binary under test, -eva-no-memexec
#                           reference: the reference binary, -eva-memexec
#                           (default: nocache,cache,reference)
#   --repeat MODE           run MODE a second time, as MODE.2
#   --timeout SECONDS       wall-time limit of each Eva invocation (3600)
#   --memory-limit BYTES    address-space limit of each Eva invocation
#                           (default: none)
#   --extra-eva-flags FLAGS Eva options added in every mode, such as a
#                           compatibility fix; recorded with each run
#   --test-checkout DIR     Frama-C build of the binary under test
#                           (default: $FRAMA_C_CHECKOUT or ~/Project/frama-c)
#   --reference-checkout DIR  Frama-C build of the reference binary
#   --switch DIR            opam switch of the builds (default: the local
#                           switch of the test checkout)
#   --keep                  keep the sessions and source snapshots
#
# A checkout is a git working tree with no local change, or a directory made
# by tools/build-reference.sh, which records its revision in the file
# CAMPAIGN_REVISION. Each run is a fresh Eva invocation in a fresh snapshot
# of the case-study sources at the revision pinned by the manifest. Runs are
# serial and never retried. See campaign/README.md.
set -euo pipefail

campaign=$(dirname "$(realpath "$0")")
oscs=$(dirname "$campaign")
tool=(python3 -I "$campaign/tools/campaign.py")
manifest=$campaign/manifest.tsv
cases_file=
modes=nocache,cache,reference
repeat=
timeout_s=3600
memory_limit=
extra_flags=
test_checkout=${FRAMA_C_CHECKOUT:-$HOME/Project/frama-c}
reference_checkout=
switch=
keep=false
invocation=("$0" "$@")

while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest) manifest=$(realpath "$2"); shift 2 ;;
    --cases) cases_file=$(realpath "$2"); shift 2 ;;
    --modes) modes=$2; shift 2 ;;
    --repeat) repeat=$2; shift 2 ;;
    --timeout) timeout_s=$2; shift 2 ;;
    --memory-limit) memory_limit=$2; shift 2 ;;
    --extra-eva-flags) extra_flags=$2; shift 2 ;;
    --test-checkout) test_checkout=$2; shift 2 ;;
    --reference-checkout) reference_checkout=$2; shift 2 ;;
    --switch) switch=$2; shift 2 ;;
    --keep) keep=true; shift ;;
    -h|--help) sed -n '2,/^set -euo/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
    -*) printf 'Unknown option %s\n' "$1" >&2; exit 2 ;;
    *) break ;;
  esac
done
output=$(realpath -m "${1:?Supply a fresh output directory}")
test_checkout=$(realpath "$test_checkout")
switch=${switch:-$test_checkout}
IFS=, read -r -a mode_list <<< "$modes"
if [[ -n $repeat ]]; then mode_list+=("$repeat.2"); fi
for mode in "${mode_list[@]}"; do
  case "${mode%.2}" in
    cache|nocache) ;;
    reference)
      if [[ -z $reference_checkout ]]; then
        printf 'Mode reference needs --reference-checkout\n' >&2; exit 2
      fi ;;
    *) printf 'Unknown mode %s\n' "$mode" >&2; exit 2 ;;
  esac
done

mkdir "$output"
mkdir -p "$output/provenance" "$output/runs" "$output/tools"
# Paths under the home directory are written from ~ in the provenance.
private() { sed "s|$HOME|~|g"; }
printf '%q ' "${invocation[@]}" | sed 's/ $//' | private \
  > "$output/provenance/command.txt"
printf '\n' >> "$output/provenance/command.txt"
# The manifest actually used, kept in the provenance and in the archive.
cp "$manifest" "$output/provenance/manifest.tsv"
sha256sum < "$manifest" | cut -d' ' -f1 > "$output/provenance/manifest.sha256"

eval "$(opam env --switch="$switch" --set-switch)"
export PATH="$switch/_opam/setup-venv/bin:$PATH"
export LC_ALL=C TERM=dumb

# ----- Binaries -------------------------------------------------------------

# Records the binary of a role: its revision and the patch applied on top of
# it (see campaign.py provenance), the SHA-256 of the executable and of the
# Eva plugin, the counter families of the plugin, and the version.
prepare_binary() {
  local role=$1 dir=$2 provenance
  dir=$(realpath "$dir")
  provenance=$("${tool[@]}" provenance "$dir" "$role" "$output/provenance/patches")
  local tools="$output/tools/$role"
  mkdir -p "$tools"
  (cd "$dir" && dune exec --no-build -- env) |
    grep -E '^(OCAMLPATH|DUNE_SOURCEROOT|DUNE_OCAML_STDLIB|DUNE_OCAML_HARDCODED|DUNE_DIR_LOCATIONS)=' \
      > "$tools/sites.env"
  local bin="$dir/_build/install/default/bin"
  (
    while IFS= read -r setting; do export "$setting"; done < "$tools/sites.env"
    "$bin/frama-c" -version > "$tools/version"
    "$bin/frama-c" -plugins > "$tools/plugins" 2>&1
  )
  if ! grep -q '^Eva ' "$tools/plugins" ||
     grep -q 'failed to load plugin' "$tools/plugins"; then
    printf 'Eva is not loaded by %s. See %s/plugins\n' "$bin" "$tools" >&2
    return 1
  fi
  bash "$campaign/tools/build-queries.sh" "$tools/sites.env" "$tools" \
    > "$tools/build-queries.log" 2>&1
  printf '%s\n' "$dir" > "$tools/checkout"
  local cmxs="$dir/_build/default/plugins/eva/src/eva.cmxs"
  "${tool[@]}" families "$cmxs" > "$tools/counter-families"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$role" "$(private <<< "$dir")" \
    "$provenance" \
    "$(sha256sum < "$bin/frama-c" | cut -d' ' -f1)" \
    "$(sha256sum < "$cmxs" | cut -d' ' -f1)" \
    "$(cat "$tools/counter-families")" \
    "$(cat "$tools/version")" >> "$output/provenance/binaries.tsv"
}

printf 'role\tcheckout\trevision\tpatch_sha256\tpatch\tframa_c_sha256\teva_cmxs_sha256\tcounter_families\tversion\n' \
  > "$output/provenance/binaries.tsv"
prepare_binary test "$test_checkout"
if [[ -n $reference_checkout ]]; then
  prepare_binary reference "$reference_checkout"
fi

{
  printf '# Machine\n'; uname -srvmo; printf '\n'
  cat /etc/os-release 2>/dev/null || true; printf '\n'
  lscpu; printf '\n'; free -m; printf '\n'; nproc; printf '\n'
  printf '# Toolchain\n'
  ocamlc -version; dune --version; gcc --version | head -1; make --version | head -1
  python3 --version; /usr/bin/time --version 2>&1 | head -1; timeout --version | head -1
  printf '\n# Load at start\n'; uptime
} > "$output/provenance/machine.txt" 2>&1
{
  git -C "$oscs" log -1 --format='%H %s'
  git -C "$oscs" status --short --branch
} > "$output/provenance/campaign-revision.txt"

# ----- Cases ---------------------------------------------------------------

if [[ -n $cases_file ]]; then
  mapfile -t cases < <(grep -v '^#' "$cases_file" | sed '/^$/d')
else
  mapfile -t cases < <(grep -v '^#' "$manifest" | tail -n +2 | cut -f1)
fi
printf '%s\n' "${cases[@]}" > "$output/provenance/cases.txt"

field() { "${tool[@]}" manifest-get "$manifest" "$1" "$2"; }

# Writes the outcome of a run and the evidence of exhausted memory, from its
# measure, its exit status, its log and its records (see classify_outcome
# in tools/campaign.py).
classify() {
  "${tool[@]}" outcome "$1" "$2" "$3" "$timeout_s"
}

# A column of the row of a role in binaries.tsv.
binary_field() {
  awk -F'\t' -v r="$1" -v c="$2" '
    NR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
    $1 == r { print $col[c] }' "$output/provenance/binaries.tsv"
}

run_one() {
  local id=$1 mode=$2
  local base=${mode%.2} role flag
  case "$base" in
    cache) role=test; flag=-eva-memexec ;;
    nocache) role=test; flag=-eva-no-memexec ;;
    reference) role=reference; flag=-eva-memexec ;;
  esac
  local tools="$output/tools/$role"
  local bin
  bin="$(cat "$tools/checkout")/_build/install/default/bin"
  local directory target revision
  directory=$(field directory "$id")
  target=$(field target "$id")
  revision=$(field oscs_revision "$id")
  local run="$output/runs/$id/$mode" src
  src="$run/src"
  mkdir -p "$src"
  git -C "$oscs" archive "$revision" -- Makefile Makefile.common path.mk "$directory" |
    tar -x -C "$src"
  rm -rf -- "$src/$directory/.frama-c/"*.parse "$src/$directory/.frama-c/"*.eva
  printf 'EVAFLAGS += %s -eva-msg-key=+cache,+callstacks %s\n' "$flag" \
    "$extra_flags" > "$run/mode.mk"
  local make_args=(make -C "$src/$directory/.frama-c" -f GNUmakefile
                   -f "$run/mode.mk" "FRAMAC_DIR=$bin"
                   "FRAMAC=$campaign/bin/frama-c-measure")
  local started parse_exit=0 make_exit=0
  started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  (
    while IFS= read -r setting; do export "$setting"; done < "$tools/sites.env"
    export CAMPAIGN_FRAMAC="$bin/frama-c"
    printf '%q ' "${make_args[@]}" "${target%.eva}.parse" > "$run/parse-command"
    timeout "$timeout_s" "${make_args[@]}" "${target%.eva}.parse" \
      > "$run/parse.log" 2>&1
  ) || parse_exit=$?
  if [[ $parse_exit == 0 ]]; then
    (
      while IFS= read -r setting; do export "$setting"; done < "$tools/sites.env"
      export CAMPAIGN_FRAMAC="$bin/frama-c" CAMPAIGN_MEASURE="$run/measure" \
             CAMPAIGN_TIMEOUT="$timeout_s" CAMPAIGN_MEMORY_LIMIT="$memory_limit"
      printf '%q ' "${make_args[@]}" "$target" > "$run/eva-command"
      "${make_args[@]}" "$target" > "$run/make-eva.log" 2>&1
    ) || make_exit=$?
  fi
  local analysis="$src/$directory/.frama-c/$target"
  for artifact in command eva.log stats.txt alarms.csv metrics.log nonterm.log \
                  warnings.log eva-stats.csv; do
    if [[ -f $analysis/$artifact ]]; then cp "$analysis/$artifact" "$run/$artifact"; fi
  done
  if [[ -f $run/eva.log ]]; then
    "${tool[@]}" records "$run/eva.log" "$run/records.jsonl" \
      2> "$run/records-problems.log" || true
  fi
  local outcome evidence
  IFS=$'\t' read -r outcome evidence < <(classify "$run" "$parse_exit" "$make_exit")
  # Untimed: state queries on the saved session, with the same limits.
  local queries_exit=-
  if [[ $outcome == completed && -f $analysis/framac.sav ]]; then
    queries_exit=0
    (
      while IFS= read -r setting; do export "$setting"; done < "$tools/sites.env"
      export CAMPAIGN_QUERIES_OUT="$run/queries.tsv"
      limit=()
      if [[ -n $memory_limit ]]; then limit=(prlimit "--as=$memory_limit"); fi
      timeout "$timeout_s" "${limit[@]}" "$bin/frama-c" \
        -load "$analysis/framac.sav" -load-module "$tools/campaign_queries.cmxs" \
        > "$run/queries.log" 2>&1
    ) || queries_exit=$?
  fi
  {
    printf 'case\t%s\nmode\t%s\nrole\t%s\nflag\t%s\n' "$id" "$mode" "$role" "$flag"
    printf 'revision\t%s\n' "$(binary_field "$role" revision)"
    printf 'patch_sha256\t%s\n' "$(binary_field "$role" patch_sha256)"
    printf 'counter_families\t%s\n' "$(binary_field "$role" counter_families)"
    printf 'oscs_revision\t%s\nstarted\t%s\n' "$revision" "$started"
    printf 'outcome\t%s\noom_evidence\t%s\n' "$outcome" "$evidence"
    printf 'parse_exit\t%s\nmake_exit\t%s\n' "$parse_exit" "$make_exit"
    if [[ -f $run/measure ]]; then "${tool[@]}" measure "$run/measure"; fi
    printf 'timeout_s\t%s\nmemory_limit\t%s\nextra_eva_flags\t%s\nqueries_exit\t%s\n' \
      "$timeout_s" "${memory_limit:--}" "${extra_flags:--}" "$queries_exit"
  } > "$run/run.tsv"
  for file in eva.log records.jsonl queries.tsv make-eva.log parse.log; do
    if [[ -f $run/$file ]]; then gzip -n "$run/$file"; fi
  done
  if ! $keep; then rm -rf -- "$src"; fi
  printf '%s %s %s\n' "$id" "$mode" "$outcome"
}

for id in "${cases[@]}"; do
  for mode in "${mode_list[@]}"; do
    run_one "$id" "$mode"
  done
done

# ----- Comparisons ---------------------------------------------------------

compare() {
  local id=$1 a=$2 b=$3
  local ra="$output/runs/$id/$a" rb="$output/runs/$id/$b"
  [[ -d $ra && -d $rb ]] || return 0
  local dir="$output/comparisons/$id/$a-vs-$b"
  mkdir -p "$dir"
  printf 'case\t%s\nbaseline\t%s\ncandidate\t%s\n' "$id" "$a" "$b" > "$dir/pair.tsv"
  # Statement numbers are comparable when both runs used the same revision
  # and patch of the analyzer: they parse the same sources alike.
  local numbering=()
  if [[ $(run_field "$ra" revision)/$(run_field "$ra" patch_sha256) == \
        "$(run_field "$rb" revision)/$(run_field "$rb" patch_sha256)" ]]; then
    numbering=(--same-numbering)
  fi
  if [[ -f $ra/records.jsonl.gz && -f $rb/records.jsonl.gz ]]; then
    "${tool[@]}" align "${numbering[@]}" "$ra/records.jsonl.gz" \
      "$rb/records.jsonl.gz" "$dir/alignment-" > /dev/null
  fi
  if [[ -f $ra/queries.tsv.gz && -f $rb/queries.tsv.gz ]]; then
    "${tool[@]}" queries "$ra/queries.tsv.gz" "$rb/queries.tsv.gz" "$dir/queries-" \
      > /dev/null
  fi
  if [[ -f $ra/alarms.csv && -f $rb/alarms.csv ]]; then
    "${tool[@]}" alarms --root-a "$ra/src" --root-b "$rb/src" \
      "$ra/alarms.csv" "$rb/alarms.csv" > "$dir/alarms.out"
    grep -v '^difference' "$dir/alarms.out" > "$dir/alarms-summary.tsv"
    grep '^difference' "$dir/alarms.out" > "$dir/alarms-differences.tsv" || true
    rm "$dir/alarms.out"
  fi
}

run_field() { awk -F'\t' -v k="$2" '$1==k{print $2}' "$1/run.tsv"; }

for id in "${cases[@]}"; do
  compare "$id" nocache cache
  compare "$id" nocache reference
  compare "$id" reference cache
  if [[ -n $repeat ]]; then compare "$id" "$repeat" "$repeat.2"; fi
done

"${tool[@]}" tables "$output" \
  --recorded-set-a "$campaign/reference/set-a-recorded.tsv" > /dev/null
printf 'Tables: %s/tables/tables.md\n' "$output"
