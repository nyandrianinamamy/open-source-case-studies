#!/usr/bin/env bash
# Packs the raw logs of a campaign into a compressed tar archive and writes
# its SHA-256 next to it.
# Usage: archive-logs.sh OUTPUT ARCHIVE
#   OUTPUT: a directory written by run-campaign.sh or pilot.sh
#   ARCHIVE: the .tar.gz file to write, outside any working tree
# The archive holds a copy of OUTPUT in which the paths under the home
# directory are written from ~, without the compiled query modules of
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
home=${HOME%/}
if [[ -z $home ]]; then printf 'HOME is not set.\n' >&2; exit 2; fi

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
  if grep -qF -- "$home" "$output/$file"; then
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
  while IFS=$'\t' read -r digest file; do
    if [[ $digest != - && $file != - ]]; then check_hashed "$file" "$digest"; fi
  done < <(awk -F'\t' '
      NR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
      col["patch"] { print $col["patch_sha256"] "\t" $col["patch"] }' \
      "$output/provenance/binaries.tsv")
fi

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
cp -a "$output" "$stage/$name"
find "$stage/$name" -path '*/tools/*' \
  \( -name '*.cmxs' -o -name '*.cmx' -o -name '*.cmi' -o -name '*.o' \
     -o -name '*.ml' \) -delete
exclude=()
for file in "${hashed[@]}"; do exclude+=(! -path "$stage/$name/$file"); done
# grep exits 1 when no file holds the path, and xargs then exits 123.
find "$stage/$name" -type f ! -name '*.gz' "${exclude[@]}" -print0 |
  { xargs -0 -r grep -lIZF "$HOME" || [[ $? == 123 ]]; } |
  xargs -0 -r sed -i "s|$HOME|~|g"
find "$stage/$name" -type f -name '*.gz' -print0 |
  while IFS= read -r -d '' file; do
    if zgrep -qF "$HOME" "$file"; then
      gzip -dc "$file" | sed "s|$HOME|~|g" | gzip -n > "$file.new"
      mv "$file.new" "$file"
    fi
  done
if grep -rqIF "$HOME" "$stage" ||
   find "$stage" -name '*.gz' -exec zgrep -qF "$HOME" {} \; -print | grep -q .; then
  printf 'A path under the home directory is left in the archive.\n' >&2
  exit 1
fi
tar --sort=name --owner=0 --group=0 --numeric-owner --mtime=@0 \
  -C "$stage" -cf - "$name" | gzip -n > "$archive"
(cd "$(dirname "$archive")" && sha256sum "$(basename "$archive")") \
  > "$archive.sha256"
cat "$archive.sha256"
