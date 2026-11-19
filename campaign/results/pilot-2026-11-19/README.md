# Pilot of 2026-11-19

Memexec against caching disabled on eight case-study targets, with the
constructed cases of `campaign/fixtures/` and the outcome demonstration.

## How it ran

```sh
campaign/pilot.sh ~/.t3/worktrees/campaign-pilot-2026-11-19 \
  ~/.t3/worktrees/frama-c/t3-7ff6e3ed-f506bb46ca39d7d6 \
  ~/.t3/worktrees/campaign-ref-9168ba2e23 ~/Project/frama-c
```

- Limits: 180 s of wall time and 8,000,000,000 bytes of address space per
  Eva invocation (the defaults of `pilot.sh`; the runner's default limit is
  3,600 s). The runs were serial. The whole command took 151 s.
- Harness: the runs were made at revision `12644c58` of this repository
  (`provenance/campaign-revision.txt`); the command it ran is
  `provenance/command.txt`. The tables were then recomputed from the raw
  logs, last with the tools at `2ade013e`; see "Recomputed tables" below.
- Case studies: revision `168321b6306abdacee95b22c9c94996f1174ab2c`, the
  manifest `campaign/manifest.tsv` at the harness revision (its SHA-256 is
  `provenance/manifest.sha256`).
- Binaries (`provenance/binaries.tsv`): both at revision
  `9168ba2e235fc436b2c1bbf393b04447312a5504` of `nyandrianinamamy/frama-c`,
  with no patch. The test binary is a git worktree at that revision; the
  reference binary was built from the same revision by
  `tools/build-reference.sh`. Their `eva.cmxs` are identical; the `frama-c`
  executables differ, each holding the path of its build. The mode
  `reference` is therefore a second build of the binary under test, not an
  earlier memexec.
- Collector and producer: at this revision, the body access collector and
  the producer of cache entries are on by default. Every run of the pilot
  ran with both, and the statistics give their verdicts (table
  `collector.tsv`). The producer stores entries that no lookup reads.
- Machine (`provenance/machine.txt`): Intel Core i5-14600KF, 20 hardware
  threads, 31 GB, Ubuntu 24.04, OCaml 5.2.1, Dune 3.21.1. The machine was
  shared with other jobs, so the times are not a timing series.
- Raw logs: `campaign-pilot-2026-11-19.tar.gz`, outside this repository,
  made by `tools/archive-logs.sh`; its SHA-256 is in `raw-logs.sha256`.

## Cases

| Case | Chosen as |
|---|---|
| `2048/2048.eva/default` | set A, hits |
| `jsmn/jsmn-example.eva/default` | set A, no hit |
| `jsmn/jsmn-main.eva/default` | allocates, hits |
| `kgflags/kgflags-simple.eva/default` | set A, hits |
| `libyaml/test-version.eva/default` | set A, no hit |
| `solitaire/solitaire.eva/default` | set A, hits |
| `genann/genann.eva/default` | allocates, hits |
| `khash/khash.eva/default` | allocates, no hit |

## Recomputed tables

The second, third and fourth reviews of issue #54 found cases where the tools
reported a result they had not established. After each, the tables were
recomputed from the archive of the raw logs, without running the pilot
again:

```sh
campaign/tools/export-ast.sh OUTPUT test ~/.t3/worktrees/frama-c/t3-7ff6e3ed-f506bb46ca39d7d6 ~/Project/frama-c \
  > SCRATCH/ast-digests.tsv
diff SCRATCH/ast-digests.tsv campaign/results/pilot-2026-11-19/ast-digests.tsv
python3 -I campaign/tools/campaign.py recompute OUTPUT \
  --ast-digests campaign/results/pilot-2026-11-19/ast-digests.tsv \
  --recorded-set-a campaign/reference/set-a-recorded.tsv
```

where `OUTPUT` is the directory `campaign-pilot-2026-11-19` extracted from
the archive, whose SHA-256 was checked against `raw-logs.sha256` (the name
of the directory is written in `tables/tables.md`), and `SCRATCH` a
directory outside the working tree: the listing is written there and
compared with the committed one, which the replay does not overwrite. The
tables of `OUTPUT/tables/` are those committed here. A second `recompute`
with the same file gives the same tables.

### After the fourth review

- `collector.tsv` now shows `-` in the five supplied-entry columns in
  all 41 runs. The archive contains neither supplied-entry counters nor
  dispositions that identify supplied lookup. Collector and producer
  counts and the memexec counts in `activity.tsv` are unchanged.
- The recorded preprocessing comparison now keeps option operands and
  argument boundaries. The corrected decoder leaves the numbering of all
  38 pairs as it was: 21 `recorded command`, 16 `asserted`, and one
  `different`. No alignment is complete. The two archived memexec runs
  of `nested-hit.c` pair all five calls with `recorded command` numbering
  and `complete=False`.
- `tables.md` shows the current result beside the historical fixture
  checks from harness revision `12644c58` and labels the historical
  alignment as superseded. The raw fixture and outcome check files and
  the other TSV tables are unchanged. The current fixture replay with
  preprocessing digests still gives `same` numbering and a complete
  alignment for the two memexec runs of `nested-hit.c`.

### After the third review

- `ast-digests.tsv` was listed again with the listing of format 2, which
  records the columns of each statement and the global declarations with
  their initial values. It has 33 runs of the binary under test: three for
  each of the eight cases (`nocache`, `cache`, `cache.2`), four for
  `frame.c`, three for `nested-hit.c` and two for `same-line.c`. Each case
  and fixture has one digest over its runs, except `same-line.c`: its two
  runs set the initial value of a global with `-DSIDE=0` and `-DSIDE=1`, and
  their digests now differ. Every row passed the checks of the import.
- The archived runs have no digest of their preprocessing, and
  `export-ast.sh` does not list it again: its parse is not the parse of the
  run. They are compared by the preprocessing their commands record (the
  `Command:` lines of `parse.log`, with the snapshot written `${SRC}`, and
  the revision and patch of the binary; for a fixture, its source and its
  `-cpp` options). Of the 22 pairs of runs of the binary under test that had
  the numbering `same`, the 21 other than `same-line.c` have equal AST
  digests and equal recorded preprocessing: their numbering is now `recorded
  command`. Their calls and queries are still paired, but no alignment and
  no query comparison of the pilot is complete. The 16 that were complete
  now have the verdict `AST digests equal, preprocessing compared by the
  recorded command only`; the 5 others (`nocache` against `cache` where hits
  nest calls) add this reason to `not every record aligned`. The 16 pairs
  with a `reference` run keep the numbering `asserted`.
- `same-line.c`, `side0` against `side1`: the numbering is `different`. Its
  two calls on one line, unmatched before, are 2 undecided groups. Of its 34
  queries, the 28 that name a statement or a callstack below the entry point
  are unpaired; the 6 exit queries over all callstacks are compared (3
  equal, 3 incomparable).
- `queries.tsv` gains the columns `numbering` and `unpaired`, and
  `comparison` gives its reasons: `incomplete: preprocessing compared by the
  recorded command only` for 21 pairs, `incomplete: numbering asserted, not
  checked by digest` for 16, `incomplete: AST digests differ` for
  `same-line.c`. All 38 were `complete` before. Over the 38 comparisons, the
  unanswered queries are B `no-callstack` 13,474, B `no-results` 78 and B
  `missing` 30, and 0 for every other reason and side; the 6 A and 6 B
  `no-callstack` of `same-line.c` are now unpaired.
- `activity.tsv`, `collector.tsv`, `functions.tsv`, `outcomes.tsv`,
  `times.tsv` and `alarms.tsv` are unchanged. The counter families are now
  read from the evidence of each run; the Eva command of each run of the
  pilot has one stage, and the families measured are the same as before. The
  outcomes now require one tree of the entry point `main`, which every
  completed run of the pilot has.

### After the second review

- The runs of the pilot have no digest of their AST: the runner did not list
  it yet. `export-ast.sh` listed it again for each run of the binary under
  test, fixtures included, by re-running only the parsing step with that
  binary, whose SHA-256 it checked against `binaries.tsv` (it took 28 s).
  Each case had one digest over its three runs (`nocache`, `cache`,
  `cache.2`), and each fixture over its runs: four for `frame.c`, three for
  `nested-hit.c`, two for `same-line.c`, whose listing had the statements
  only. The reference binary is no longer on the machine, so the runs of the
  mode `reference` have no digest: the 16 pairs that involve one have the
  numbering `asserted` (same case, revision, patch, case-study revision and
  options), not checked by digest. The 22 other pairs had the numbering
  `same`.
- `alignment.tsv` gained the column `numbering`. The 12 pairs with a
  reference run that were `complete` got the verdict `numbering asserted
  from equal revision, patch, options and preprocessing, not checked by
  digest`, and `complete` False; the 4 others (`nocache` against `reference`
  where hits nest calls) added this reason. No other cell of the alignment
  changed.
- `activity.tsv`: `refused_by_reason` became `none` instead of `-` in the 21
  runs where memexec was measured and refused nothing; `-` means only that
  the family was not measured.
- `collector.tsv` gained `supplied_refused_by_reason`, `none` in every run;
  `supplied_rejected_by_reason` became `none` instead of `-` for the same
  reason.
- `queries.tsv` gained a column per side for each reason of an unanswered
  query. Over the 38 comparisons, they were A `no-callstack` 6, B
  `no-callstack` 13,480, B `no-results` 78 and B `missing` 30, and 0 for
  every other reason and side. In the comparison of `frame.c` without
  caching against the run with `-eva-no-results`, the 46 queries of a
  statement in one callstack took the reason of the same query over all
  callstacks, `no-results`, instead of `no-callstack` (78 `no-results`
  instead of 32). The 30 exit queries are `missing`, 18 of which were
  `no-callstack`: the query module of the pilot left out the exit queries of
  a run without saved results, and its answer file does not list the reached
  exits. The current module writes them as unavailable (`no-results`).
- Every answer file was still complete under the stricter reader: one done
  line, last, with the count of the rows.
- `outcomes.tsv`, `times.tsv`, `alarms.tsv` and `functions.tsv` were
  unchanged. The runs of the outcome demonstration got the same classes
  under the rules of that revision: its `killed` run has no `oom_kill` rise.
- `tables.md` ended with the checks of `fixtures.txt` and
  `outcome-demo.txt`, which `campaign.py tables` adds itself.

## Results

The tables are in `tables/tables.md`; `fixtures.txt` and
`outcome-demo.txt` hold the checks of the constructed cases as the pilot
ran them.

- All 32 runs completed (8 cases; modes `nocache`, `cache`, `cache.2`,
  `reference`). No watchdog fired.
- Two runs of the same binary, `cache` and `cache.2`, have the same AST
  digest and align every record in every case, with equal state-query
  answers and equal alarms; their preprocessing is compared by the recorded
  commands only, so the alignment is not complete. `reference` against
  `cache` aligns every record, with equal answers and alarms, but the
  numbering of the reference runs is asserted, not checked by digest. In all
  38 alignments, both runs completed, neither was interrupted and both logs
  give the statement numbers; the numbering is `recorded command` in 21,
  `asserted` in 16 and `different` in 1, `same-line.c`
  (`alignment-summary.tsv` of each pair). The fixtures run apart with the
  current harness give the numbering `same` and complete alignments for two
  runs of the same binary (see below).
- Between `nocache` and `cache`, every record is aligned or nested under a
  hit (`accounted` is true), with no undecided group, no unmatched record
  and no inferred call. Alarms and property statuses are equal in every
  case; solitaire has 9 property keys that occur more than once, with the
  same statuses on both sides.
- Hits with memexec: none in `jsmn-example`, `libyaml/test-version` and
  `khash`; 10 to 264 in the other cases.
- Set A: the membership of each run agrees with the count of issue #28 for
  the eight targets in every mode. Applications of the allocation and
  release builtins in the mode `cache`: genann `malloc` 13, `free` 10;
  jsmn-main `malloc` 35, `free` 35; khash `malloc` 1, `calloc` 1,
  `realloc` 2, `free` 5; none in the other cases.
- State queries, `nocache` against `cache`: every query answered by both
  runs gets the same answer except in 2048 (25 narrower), jsmn-main (6
  narrower) and genann (34 wider, 4 incomparable, listed in
  `genann-query-differences.tsv`). These counts include the states at the
  exit of each function. That file is not written by `pilot.sh`: it is
  extracted from
  `comparisons/genann/genann.eva/default/nocache-vs-cache/queries-differences.tsv`
  of the raw logs with `awk -F'\t' 'NR==1 || $6 !~ /^unavailable/'`. The
  answers that only `nocache` gives are for callstacks that memexec does not
  analyse. Every answer file is complete. Top answers: 4 with caching
  disabled and 9 with memexec in genann, none elsewhere.
- Collector verdicts (`collector.tsv`): with memexec, `would-store` for
  0 (genann, khash, solitaire) to 188 (jsmn-main) bodies; the reasons of
  refusal are `sweep`, `builtin`, `contract`, `side-table`,
  `indirect-call` and `allocated-block`. The producer stored an entry for
  each `would-store` verdict and refused the others with the same reason.
- Fixtures: the second call to `outer` in `nested-hit.c` is reported as a
  hit with its two calls to `leaf` nested under it; the frame example of
  issue #3 gives `{3}` in both runs for the first call, `{5}` without
  caching and no answer with memexec for the second, and `{3; 5}` against
  `{3}` over all callstacks; a run with `-eva-no-results` answers no query;
  the two calls on one line of `same-line.c` are unmatched. All 22 checks
  of the pilot pass. Recomputed with the listing of format 2, the two
  archived runs of `same-line.c` have different digests and their calls are
  undecided. The fixtures of the current harness have 49 checks: they add
  the digests of the AST and of the preprocessing, `sites.c`, `branches.c`,
  `header.c`, an unused macro in `nested-hit.c`, a run with
  `-eva-no-results-domain cvalue`, and a `same-line.c` whose two runs differ
  by `-lib-entry`, which the archive does not have. Run apart from the pilot
  with the same binary (`campaign/fixtures/run-fixtures.sh`), all 49 pass.
- Outcome classes: the constructed runs are classified `timeout` (the
  watchdog sent SIGTERM; status 143), `oom` (Frama-C reports exhausted
  memory; status 6), `error` (status 1) and `killed` (SIGKILL that the
  watchdog did not send, with no evidence of the out-of-memory killer;
  status 137).

### Difference in genann

After `genann_free(second)` at `test.c:220`, caching disabled gives an
escaping address and memexec gives a valid pointer to the allocated block,
because the call is a memexec hit (entry stored at `genann.c:169`) and the
body's `free` is not applied again; `free` is applied 22 times against 10.
