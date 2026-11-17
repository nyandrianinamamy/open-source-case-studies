#!/usr/bin/env bash
set -euo pipefail

frama_c=$(realpath "${FRAMA_C_CHECKOUT:-$HOME/Project/frama-c}")
oscs=$(dirname "$(realpath "$0")")
output=$(realpath -m "${1:?Supply a fresh output directory}")
revision=168321b6306abdacee95b22c9c94996f1174ab2c
frama_c_bin="$frama_c/_build/install/default/bin"

mkdir "$output"
cd "$frama_c"
eval "$(opam env --switch=. --set-switch)"
export PATH="$frama_c/_opam/setup-venv/bin:$PATH"
dune exec --no-build -- env |
  grep -E '^(OCAMLPATH|DUNE_SOURCEROOT|DUNE_OCAML_STDLIB|DUNE_OCAML_HARDCODED|DUNE_DIR_LOCATIONS)=' > "$output/dune-sites.env"
while IFS= read -r setting; do
  export "$setting"
done < "$output/dune-sites.env"
export LC_ALL=C TERM=dumb
{
  git log -1 --format=fuller
  git status --short
  git -C "$oscs" log -1 --format=fuller "$revision"
  git -C "$oscs" status --short --branch
  ocamlc -version
  dune --version
  "$frama_c_bin/frama-c" -version
  "$frama_c_bin/frama-c" -print-lib-path
  printf '\n'
  sha256sum "$frama_c_bin/frama-c" "$frama_c/_build/default/plugins/eva/src/eva.cmxs"
  "$frama_c_bin/frama-c" -plugins
} > "$output/provenance.log" 2>&1
test -s "$output/provenance.log"
grep -q '^Eva ' "$output/provenance.log"
if grep -q 'failed to load plugin' "$output/provenance.log"; then
  printf 'Plugin loading failed. See %s/provenance.log\n' "$output" >&2
  exit 1
fi

status=0
for target in jsmn-main jsmn-example; do
  for mode in on off; do
    run="$output/$target-$mode"
    mkdir "$run"
    git -C "$oscs" archive "$revision" -- Makefile Makefile.common path.mk jsmn | tar -x -C "$run"
    rm -rf -- "$run/jsmn/.frama-c/"*.parse "$run/jsmn/.frama-c/"*.eva
    case "$mode" in
      on) flag=-eva-memexec ;;
      off) flag=-eva-no-memexec ;;
    esac
    printf 'EVAFLAGS += %s -eva-msg-key=+progress,+final-states\n' "$flag" > "$run/pilot.mk"
    args=( make -C "$run/jsmn/.frama-c" -B --trace -f GNUmakefile
           -f "$run/pilot.mk" "FRAMAC_DIR=$frama_c_bin" "$target.eva" )
    printf '%q ' /usr/bin/time -o "$run/make-time.txt" -f \
      '%e wall_s %U user_s %S sys_s %M maxrss_kib %x exit' timeout 3600 "${args[@]}" > "$run/command.sh"
    printf '\n' >> "$run/command.sh"
    result=0
    bash "$run/command.sh" > "$run/make.log" 2>&1 || result=$?
    printf '%s\n' "$result" > "$run/exit"
    if [[ "$result" != 0 ]]; then status=1; fi
    printf '%s %s exit=%s\n' "$target" "$mode" "$result"
  done
done
exit "$status"
