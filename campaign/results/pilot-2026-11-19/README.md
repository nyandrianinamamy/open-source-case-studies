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
  logs with the tools at `0803efe8`; see "Recomputed tables" below.
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

The second review of issue #54 found cases where the tools reported a
result they had not established. The tables were recomputed from the
archive of the raw logs, without running the pilot again:

```sh
campaign/tools/export-ast.sh OUTPUT test ~/.t3/worktrees/frama-c/t3-7ff6e3ed-f506bb46ca39d7d6 ~/Project/frama-c \
  > SCRATCH/ast-digests.tsv
diff SCRATCH/ast-digests.tsv campaign/results/pilot-2026-11-19/ast-digests.tsv
python3 -I campaign/tools/campaign.py recompute OUTPUT \
  --ast-digests campaign/results/pilot-2026-11-19/ast-digests.tsv \
  --recorded-set-a campaign/reference/set-a-recorded.tsv
```

where `OUTPUT` is the directory extracted from the archive, whose SHA-256
was checked against `raw-logs.sha256`, and `SCRATCH` a directory outside
the working tree: the listing is written there and compared with the
committed one, which the replay does not overwrite. The tables of
`OUTPUT/tables/` are those committed here.

- The runs of the pilot have no digest of their AST: the runner did not
  list it yet. `export-ast.sh` listed it again for each run of the binary
  under test, fixtures included, by re-running only the parsing step with
  that binary, whose SHA-256 it checked against `binaries.tsv`
  (`ast-digests.tsv`; it took 28 s). The three or four runs of each case
  have one digest. The reference binary is no longer on the machine, so the
  runs of the mode `reference` have no digest: the 16 pairs that involve one
  have the numbering `asserted` (same case, revision, patch, case-study
  revision and options), not checked by digest. The 22 other pairs have
  the numbering `same`.
- `alignment.tsv` gains the column `numbering`. The 12 pairs with a
  reference run that were `complete` now have the verdict `numbering
  asserted from equal revision, patch, options and preprocessing, not
  checked by digest`, and `complete` False; the 4 others (`nocache` against
  `reference` where hits nest calls) add this reason. No other cell of the
  alignment changes: every log has a record of the entry point, no stack is
  malformed, and every run completed.
- `activity.tsv`: `refused_by_reason` is `none` instead of `-` in the 21
  runs where memexec was measured and refused nothing; `-` now means only
  that the family was not measured. The measured families are now read
  from the Eva command of each run; they are the same as before.
- `collector.tsv` gains `supplied_refused_by_reason`, `none` in every run;
  `supplied_rejected_by_reason` is `none` instead of `-` for the same
  reason as above.
- `queries.tsv` gains a column per side for each reason of an unanswered
  query; all are 0 but one. In the comparison of `frame.c` without caching
  against the run with `-eva-no-results`, the 46 queries of a statement in
  one callstack now take the reason of the same query over all callstacks,
  `no-results`, instead of `no-callstack` (78 `no-results` instead of 32).
  The 30 exit queries are `missing`, 18 of which were `no-callstack`: the
  query module of the pilot left out the exit queries of a run without
  saved results, and its answer file does not list the reached exits. The
  current module writes them as unavailable (`no-results`).
- Every answer file is still complete under the stricter reader: one done
  line, last, with the count of the rows.
- `outcomes.tsv`, `times.tsv`, `alarms.tsv` and `functions.tsv` are
  unchanged. The runs of the outcome demonstration get the same classes
  under the current rules: its `killed` run has no `oom_kill` rise.
- `tables.md` now ends with the checks of `fixtures.txt` and
  `outcome-demo.txt`, which `campaign.py tables` adds itself; the text is
  the same as before.

## Results

The tables are in `tables/tables.md`; `fixtures.txt` and
`outcome-demo.txt` hold the checks of the constructed cases as the pilot
ran them.

- All 32 runs completed (8 cases; modes `nocache`, `cache`, `cache.2`,
  `reference`). No watchdog fired.
- Two runs of the same binary, `cache` and `cache.2`, have the same AST
  digest and align completely in every case, with equal state-query
  answers and equal alarms. `reference` against `cache` aligns every
  record, with equal answers and alarms, but the numbering of the reference
  runs is asserted, not checked by digest. In all 38 alignments, both runs
  completed, neither was interrupted and both logs give the statement
  numbers; the numbering is `same` in 22 and `asserted` in 16
  (`alignment-summary.tsv` of each pair).
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
  of the pilot pass. The fixtures of the current harness have 35 checks:
  they add the AST digests, `sites.c` and a run with
  `-eva-no-results-domain cvalue`, which the archive does not have. Run
  apart from the pilot with the same binary
  (`campaign/fixtures/run-fixtures.sh`), all 35 pass.
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
