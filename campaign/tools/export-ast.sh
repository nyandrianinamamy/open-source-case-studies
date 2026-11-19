#!/usr/bin/env bash
# Lists again the AST of the runs of a campaign output directory written
# before the runner recorded its digest, by re-running only the parsing step
# of each run, and prints the digests for campaign.py recompute.
#
# Usage: export-ast.sh OUTPUT ROLE CHECKOUT [SWITCH] > DIGESTS
#   OUTPUT    a directory written by run-campaign.sh or pilot.sh, or
#             extracted from its archive
#   ROLE      the role whose runs are listed: test or reference
#   CHECKOUT  the Frama-C build of that role; its frama-c and Eva plugin must
#             have the SHA-256 recorded in OUTPUT/provenance/binaries.tsv
#   SWITCH    opam switch of the build (default: the local switch of
#             CHECKOUT)
#
# It uses the Dune site settings recorded in OUTPUT/tools/ROLE/sites.env,
# with ~ written for the home directory, and compiles the query module in a
# temporary directory. For a run of a case of the manifest
# OUTPUT/provenance/manifest.tsv, it snapshots the sources of the case
# studies at the revision recorded in run.tsv, as the runner does, makes the
# target TARGET.parse with the mode.mk of the run, and lists the AST of the
# parse session from the directory of the analysis. For a run of a fixture
# (case fixtures/FILE.c/default), it parses the copy of FILE.c kept in the
# run with the preprocessing options (-cpp-*) of extra_eva_flags. No
# analysis is run. Prints the columns case, mode, ast_sha256,
# ast_statements and parse_exit, after comment lines that name the binary.
set -euo pipefail
campaign=$(dirname "$(dirname "$(realpath "$0")")")
oscs=$(dirname "$campaign")
tool=(python3 -I "$campaign/tools/campaign.py")
output=$(realpath "${1:?Supply the campaign output directory}")
role=${2:?Supply the role: test or reference}
checkout=$(realpath "${3:?Supply the Frama-C build of the role}")
switch=${4:-$checkout}
bin="$checkout/_build/install/default/bin"
cmxs="$checkout/_build/default/plugins/eva/src/eva.cmxs"

binary_field() {
  awk -F'\t' -v r="$role" -v c="$1" '
    NR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
    $1 == r { print $col[c] }' "$output/provenance/binaries.tsv"
}
for pair in "frama_c_sha256:$bin/frama-c" "eva_cmxs_sha256:$cmxs"; do
  recorded=$(binary_field "${pair%%:*}")
  if [[ $(sha256sum < "${pair#*:}" | cut -d' ' -f1) != "$recorded" ]]; then
    printf '%s does not have the SHA-256 recorded for the role %s.\n' \
      "${pair#*:}" "$role" >&2
    exit 1
  fi
done

eval "$(opam env --switch="$switch" --set-switch)"
export PATH="$switch/_opam/setup-venv/bin:$PATH"
export LC_ALL=C TERM=dumb
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
home=$HOME
while [[ $home == */ ]]; do home=${home%/}; done
sed "s|~|$home|g" "$output/tools/$role/sites.env" > "$work/sites.env"
bash "$campaign/tools/build-queries.sh" "$work/sites.env" "$work/tools" \
  > "$work/build-queries.log" 2>&1
module="$work/tools/campaign_queries.cmxs"
manifest="$output/provenance/manifest.tsv"

run_field() { awk -F'\t' -v k="$2" '$1==k{print $2}' "$1/run.tsv"; }

printf '# Listed by tools/export-ast.sh from a parse alone, role %s, revision %s,\n' \
  "$role" "$(binary_field revision)"
printf '# frama-c SHA-256 %s.\n' "$(binary_field frama_c_sha256)"
printf 'case\tmode\tast_sha256\tast_statements\tparse_exit\n'
while IFS= read -r -d '' tsv; do
  run=$(dirname "$tsv")
  [[ $(run_field "$run" role) == "$role" ]] || continue
  id=$(run_field "$run" case) mode=$(run_field "$run" mode)
  limit=$(run_field "$run" timeout_s)
  listing="$work/runs/$id/$mode/ast.tsv"
  mkdir -p "$(dirname "$listing")"
  parse_exit=0
  if [[ $id == fixtures/*/default ]]; then
    file=$(basename "$(dirname "$id")")
    read -r -a flags <<< "$(run_field "$run" extra_eva_flags)"
    cpp=()
    for flag in "${flags[@]}"; do
      if [[ $flag == -cpp-* ]]; then cpp+=("$flag"); fi
    done
    dir="$work/runs/$id/$mode/src"
    mkdir -p "$dir"
    cp "$run/$file" "$dir/"
    (
      while IFS= read -r setting; do export "$setting"; done < "$work/sites.env"
      cd "$dir"
      CAMPAIGN_AST_OUT="$listing" timeout "${limit:-3600}" "$bin/frama-c" \
        "$file" "${cpp[@]}" -load-module "$module" > "$dir/parse.log" 2>&1
    ) || parse_exit=$?
  else
    directory=$("${tool[@]}" manifest-get "$manifest" directory "$id")
    target=$("${tool[@]}" manifest-get "$manifest" target "$id")
    src="$work/runs/$id/$mode/src"
    mkdir -p "$src"
    git -C "$oscs" archive "$(run_field "$run" oscs_revision)" -- \
      Makefile Makefile.common path.mk "$directory" | tar -x -C "$src"
    analysis="$src/$directory/.frama-c"
    rm -rf -- "$analysis/"*.parse "$analysis/"*.eva
    (
      while IFS= read -r setting; do export "$setting"; done < "$work/sites.env"
      export CAMPAIGN_FRAMAC="$bin/frama-c"
      timeout "${limit:-3600}" make -C "$analysis" -f GNUmakefile \
        -f "$run/mode.mk" "FRAMAC_DIR=$bin" \
        "FRAMAC=$campaign/bin/frama-c-measure" "${target%.eva}.parse" \
        > "$work/parse.log" 2>&1
      cd "$analysis"
      CAMPAIGN_AST_OUT="$listing" timeout "${limit:-3600}" "$bin/frama-c" \
        -load "${target%.eva}.parse/framac.sav" -load-module "$module" \
        > "$work/ast.log" 2>&1
    ) || parse_exit=$?
    rm -rf -- "$src"
  fi
  "${tool[@]}" ast "$listing" |
    awk -F'\t' -v c="$id" -v m="$mode" -v e="$parse_exit" '
      { v[$1] = $2 }
      END { print c "\t" m "\t" v["ast_sha256"] "\t" v["ast_statements"] "\t" e }'
done < <(find "$output/runs" -name run.tsv -print0 | sort -z)
