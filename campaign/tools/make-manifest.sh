#!/usr/bin/env bash
# Writes the manifest of the campaign: every Eva target of the case studies
# at a revision, each in its existing configuration.
# Usage: make-manifest.sh FRAMA_C_CHECKOUT REVISION OUTPUT [SWITCH]
#   FRAMA_C_CHECKOUT: a built Frama-C checkout, whose analysis scripts
#                     expand the makefiles of the case studies
#   REVISION: the case-study revision that pins the inputs
#   SWITCH: opam switch of the build (default: the local switch of the
#           checkout)
# The makefiles are evaluated with make -n, which runs no analysis but writes
# the parse and Eva command of each target into its command files.
set -euo pipefail
campaign=$(dirname "$(dirname "$(realpath "$0")")")
oscs=$(dirname "$campaign")
checkout=$(realpath "${1:?Supply a built Frama-C checkout}")
revision=$(git -C "$oscs" rev-parse --verify "${2:?Supply a revision}^{commit}")
output=$(realpath -m "${3:?Supply the output file}")
switch=${4:-$checkout}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
git -C "$oscs" archive "$revision" | tar -x -C "$work"
cd "$checkout"
eval "$(opam env --switch="$switch" --set-switch)"
dune exec --no-build -- env |
  grep -E '^(OCAMLPATH|DUNE_SOURCEROOT|DUNE_OCAML_STDLIB|DUNE_OCAML_HARDCODED|DUNE_DIR_LOCATIONS)=' \
    > "$work/sites.env"
while IFS= read -r setting; do export "$setting"; done < "$work/sites.env"
bin="$checkout/_build/install/default/bin"
export LC_ALL=C
make --no-print-directory -C "$work" FRAMAC_DIR="$bin" display-targets |
  tr ' ' '\n' | sed '/^$/d' > "$work/targets.txt"
cut -d/ -f1 "$work/targets.txt" | sort -u > "$work/directories.txt"
: > "$work/trees.tsv"
while IFS= read -r directory; do
  make --no-print-directory -s -n -B -C "$work/$directory/.frama-c" \
    FRAMAC_DIR="$bin" eva > /dev/null
  printf '%s\t%s\n' "$directory" \
    "$(git -C "$oscs" rev-parse "$revision:$directory")" >> "$work/trees.tsv"
done < "$work/directories.txt"
python3 -I "$campaign/tools/campaign.py" manifest "$work" "$work/targets.txt" \
  "$revision" "$output" --trees "$work/trees.tsv" \
  --share "$("$bin/frama-c" -print-share-path)" \
  --lib "$("$bin/frama-c" -print-lib-path)"
printf '%s cases written to %s\n' "$(wc -l < "$work/targets.txt")" "$output"
