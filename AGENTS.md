# Working in this checkout

Keep personal-fork work on `dev`. Use the root [Makefile](Makefile) for
case-study targets. Read the selected case's `.frama-c/GNUmakefile` to confirm
the target, source inputs and Eva options before running a comparison.

## Select the sibling Frama-C build

Build from `~/Project/frama-c` using its local opam switch. Capture the Dune
site environment so Make uses the executable, plugins, analysis scripts and
libc from that build together.

```bash
cd "$HOME/Project/frama-c"
eval "$(opam env --switch=. --set-switch)"
export PATH="$PWD/_opam/setup-venv/bin:$PATH"
dune build -j 8 @install
framac_bin="$PWD/_build/install/default/bin"
sites=$(mktemp)
dune exec --no-build -- env |
  grep -E '^(OCAMLPATH|DUNE_SOURCEROOT|DUNE_OCAML_STDLIB|DUNE_OCAML_HARDCODED|DUNE_DIR_LOCATIONS)=' > "$sites"
while IFS= read -r setting; do
  export "$setting"
done < "$sites"
rm "$sites"
"$framac_bin/frama-c" -version
"$framac_bin/frama-c" -print-lib-path
"$framac_bin/frama-c" -plugins
```

The library path should end in `_build/install/default/lib/frama-c/lib`, and
the plugin list should include Eva without plugin loading errors. Rebuild
`@install` and repeat the checks if the local switch dependencies change.
Running the bare development executable without Dune site paths can fail
before processing arguments.

From the same shell, use a separate copy of the case inputs for each run
when comparing configurations. The analysis recipes write into `.parse`
and `.eva` directories beside the case Makefile. Use `-B` to force fresh
analysis after a build change. From a clean copy of this repository, a
single target can be selected with

```bash
timeout 3600 make -B FRAMAC_DIR="$framac_bin" jsmn/jsmn-main.eva
```

Record the two source revisions, effective Make command, exit code,
`.eva/command`, `.eva/eva.log`, and `.eva/stats.txt`. The case-study
statistics give Frama-C user CPU seconds and peak RSS in KiB for the Eva
recipe. If timing the entire Make command as well, report its wall time and
peak RSS separately because Make also runs parsing and setup.

## Replay the jsmn memexec pilot

From this checkout, run `bash stage1-pilot.sh /absolute/fresh/output` after
building Frama-C as above. The script captures the Dune sites itself and
accepts `FRAMA_C_CHECKOUT` for a different build checkout. It runs
`jsmn-main.eva` and `jsmn-example.eva` serially with memexec on and off.
Each run gets a fresh source snapshot and a one-hour timeout. Compare
`alarms.csv`, `metrics.log`, and `nonterm.log` across each pair. Count
actual memexec hits using `Reusing old results for call to` in `eva.log`.
Compare the `[eva:final-states]` entries for the available joined Cvalue
exit-state prints. See `provenance.log` for revisions and executable hashes,
and `make-time.txt` for the full Make invocation's resource use.
