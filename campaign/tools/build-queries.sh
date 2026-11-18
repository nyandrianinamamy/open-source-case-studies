#!/usr/bin/env bash
# Compiles the state-query module against one Frama-C build.
# Usage: build-queries.sh SITES_ENV OUTPUT_DIR
#   SITES_ENV: the Dune site settings of the build (see run-campaign.sh).
#   OUTPUT_DIR: receives campaign_queries.cmxs.
set -euo pipefail
sites=${1:?Supply the Dune site settings of the build}
output=$(realpath -m "${2:?Supply an output directory}")
source=$(dirname "$(realpath "$0")")/../queries/campaign_queries.ml
while IFS= read -r setting; do
  export "$setting"
done < "$sites"
mkdir -p "$output"
cp "$source" "$output/campaign_queries.ml"
cd "$output"
ocamlfind ocamlopt -shared -w +a-4-9-40-41-42-44-45-70 \
  -package frama-c.kernel,frama-c-eva.core -open Frama_c_kernel \
  -o campaign_queries.cmxs campaign_queries.ml
