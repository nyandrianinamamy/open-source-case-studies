#!/usr/bin/env bash
# Packs the raw logs of a campaign into a compressed tar archive and writes
# its SHA-256 next to it.
# Usage: archive-logs.sh OUTPUT ARCHIVE
#   OUTPUT: a directory written by run-campaign.sh or pilot.sh
#   ARCHIVE: the .tar.gz file to write, outside any working tree
# The archive holds a copy of OUTPUT in which the paths under the home
# directory, as given in HOME (without a trailing slash) or by its physical
# path, are written from ~ (campaign.py home), without the compiled query
# modules of
# tools/. It keeps provenance/manifest.tsv, the manifest the runner used,
# which may differ from campaign/manifest.tsv (option --manifest).
# Its members are sorted and dated at the epoch, with no owner.
# The files whose SHA-256 the provenance records, the manifest
# (manifest.sha256) and the patches (column patch_sha256 of binaries.tsv),
# are archived unchanged: the script checks them against their digests and
# refuses one that holds the home directory (run-campaign.sh refuses them
# at the start of a run).
set -euo pipefail
output=$(realpath "${1:?Supply the campaign output directory}")
archive=$(realpath -m "${2:?Supply the archive to write}")
name=$(basename "$archive" .tar.gz)
tool=(python3 -I "$(dirname "$(realpath "$0")")/campaign.py")
home=("${tool[@]}" home)
if [[ -z ${HOME%/} ]]; then printf 'HOME is not set.\n' >&2; exit 2; fi

"${home[@]}" check-links "$output"

# The hashed files, as paths relative to OUTPUT, and their recorded digests.
hashed=()
check_hashed() {
  local file=$1 digest=$2
  if [[ ! -f $output/$file ]]; then
    printf 'The hashed file %s is missing.\n' "$file" >&2; exit 1
  fi
  if [[ $(sha256sum < "$output/$file" | cut -d' ' -f1) != "$digest" ]]; then
    printf 'The file %s does not match its recorded SHA-256.\n' "$file" >&2
    exit 1
  fi
  if ! "${home[@]}" check "$output/$file" 2> /dev/null; then
    printf 'The file %s holds the home directory; it is archived unchanged with its SHA-256, so it cannot be rewritten.\n' \
      "$file" >&2
    exit 1
  fi
  hashed+=("$file")
}
if [[ -f $output/provenance/manifest.sha256 ]]; then
  check_hashed provenance/manifest.tsv "$(cat "$output/provenance/manifest.sha256")"
fi
if [[ -f $output/provenance/binaries.tsv ]]; then
  patches=$("${tool[@]}" binaries-get \
    "$output/provenance/binaries.tsv" patch_sha256 patch)
  if [[ -n $patches ]]; then
    while IFS=$'\t' read -r digest file; do
      if [[ $digest != - && $file != - ]]; then check_hashed "$file" "$digest"; fi
    done <<< "$patches"
  fi
fi

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
cp -a "$output" "$stage/$name"
find "$stage/$name" -path '*/tools/*' \
  \( -name '*.cmxs' -o -name '*.cmx' -o -name '*.cmi' -o -name '*.o' \
     -o -name '*.ml' \) -delete
keep=()
for file in "${hashed[@]}"; do keep+=(--keep "$file"); done
"${home[@]}" redact-tree "$stage/$name" "${keep[@]}"
if ! "${home[@]}" check-tree "$stage/$name" --link-root "$output"; then
  printf 'The archive failed the final path check.\n' >&2
  exit 1
fi
tar --sort=name --owner=0 --group=0 --numeric-owner --mtime=@0 \
  -C "$stage" -cf - "$name" | gzip -n > "$archive"
(cd "$(dirname "$archive")" && sha256sum "$(basename "$archive")") \
  > "$archive.sha256"
cat "$archive.sha256"
