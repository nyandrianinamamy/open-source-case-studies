#!/usr/bin/env bash
# Builds a Frama-C binary pinned by revision, outside any working tree.
# Usage: build-reference.sh [--no-build] REPOSITORY REVISION DESTINATION [SWITCH]
#   REPOSITORY: a clone of Frama-C that has REVISION
#   DESTINATION: fresh directory; it receives the sources of REVISION, their
#                build and the provenance files below, and serves as
#                --reference-checkout or --test-checkout of run-campaign.sh
#   SWITCH: opam switch of the build (default: the local switch of
#           REPOSITORY)
#   --no-build: write the sources and the provenance files, without building
# Provenance files in DESTINATION:
#   CAMPAIGN_REVISION      the full revision, alone on its line
#   CAMPAIGN_PATCH.patch   a copy of the patch named by CAMPAIGN_PATCH, applied
#                          on top of REVISION, if any
#   CAMPAIGN_PATCH_SHA256  the SHA-256 of that patch
# run-campaign.sh records the revision and the SHA-256 in separate columns of
# provenance/binaries.tsv and keeps the patch in provenance/patches/.
set -euo pipefail
build=true
if [[ ${1:-} == --no-build ]]; then build=false; shift; fi
repository=$(realpath "${1:?Supply a Frama-C repository}")
revision=$(git -C "$repository" rev-parse --verify "${2:?Supply a revision}^{commit}")
destination=$(realpath -m "${3:?Supply a fresh destination}")
switch=${4:-$repository}
mkdir "$destination"
git -C "$repository" archive "$revision" | tar -x -C "$destination"
printf '%s\n' "$revision" > "$destination/CAMPAIGN_REVISION"
if [[ -n ${CAMPAIGN_PATCH:-} ]]; then
  cp "$CAMPAIGN_PATCH" "$destination/CAMPAIGN_PATCH.patch"
  patch -s -d "$destination" -p1 < "$destination/CAMPAIGN_PATCH.patch"
  sha256sum < "$destination/CAMPAIGN_PATCH.patch" | cut -d' ' -f1 \
    > "$destination/CAMPAIGN_PATCH_SHA256"
fi
if ! $build; then
  printf 'Prepared %s in %s\n' "$revision" "$destination"
  exit 0
fi
cd "$destination"
eval "$(opam env --switch="$switch" --set-switch)"
export PATH="$switch/_opam/setup-venv/bin:$PATH"
dune build -j 8 @install
_build/install/default/bin/frama-c -version > /dev/null 2>&1 || true
printf 'Built %s in %s\n' "$revision" "$destination"
