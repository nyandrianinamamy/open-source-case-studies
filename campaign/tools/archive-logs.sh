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
set -euo pipefail
output=$(realpath "${1:?Supply the campaign output directory}")
archive=$(realpath -m "${2:?Supply the archive to write}")
name=$(basename "$archive" .tar.gz)
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
cp -a "$output" "$stage/$name"
find "$stage/$name" -path '*/tools/*' \
  \( -name '*.cmxs' -o -name '*.cmx' -o -name '*.cmi' -o -name '*.o' \
     -o -name '*.ml' \) -delete
# grep exits 1 when no file holds the path, and xargs then exits 123.
find "$stage/$name" -type f ! -name '*.gz' -print0 |
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
