#!/usr/bin/env bash
# Builds a Frama-C binary pinned by revision, outside any working tree.
# Usage: build-reference.sh REPOSITORY REVISION DESTINATION [SWITCH]
#   REPOSITORY: a clone of Frama-C that has REVISION
#   DESTINATION: fresh directory; it receives the sources of REVISION, their
#                build and the file CAMPAIGN_REVISION, and serves as
#                --reference-checkout or --test-checkout of run-campaign.sh
#   SWITCH: opam switch of the build (default: the local switch of
#           REPOSITORY)
# A patch to apply on top of REVISION can be given in CAMPAIGN_PATCH; its
# SHA-256 is then appended to CAMPAIGN_REVISION.
set -euo pipefail
repository=$(realpath "${1:?Supply a Frama-C repository}")
revision=$(git -C "$repository" rev-parse --verify "${2:?Supply a revision}^{commit}")
destination=$(realpath -m "${3:?Supply a fresh destination}")
switch=${4:-$repository}
mkdir "$destination"
git -C "$repository" archive "$revision" | tar -x -C "$destination"
printf '%s\n' "$revision" > "$destination/CAMPAIGN_REVISION"
if [[ -n ${CAMPAIGN_PATCH:-} ]]; then
  patch -d "$destination" -p1 < "$CAMPAIGN_PATCH"
  printf 'patch %s\n' "$(sha256sum < "$CAMPAIGN_PATCH" | cut -d' ' -f1)" \
    >> "$destination/CAMPAIGN_REVISION"
fi
cd "$destination"
eval "$(opam env --switch="$switch" --set-switch)"
export PATH="$switch/_opam/setup-venv/bin:$PATH"
dune build -j 8 @install
_build/install/default/bin/frama-c -version > /dev/null 2>&1 || true
printf 'Built %s in %s\n' "$revision" "$destination"
