# Pilot of 2026-11-18

Memexec against caching disabled on eight case-study targets, with the
constructed cases of `campaign/fixtures/` and the outcome demonstration.

## How it ran

```sh
campaign/pilot.sh ~/.t3/worktrees/campaign-pilot-2026-11-18 \
  ~/.t3/worktrees/frama-c/t3-7ff6e3ed-f506bb46ca39d7d6 \
  ~/.t3/worktrees/campaign-ref-5bf903b27a ~/Project/frama-c
```

- Limits: 180 s of wall time and 8,000,000,000 bytes of address space per
  Eva invocation (the defaults of `pilot.sh`; the runner's default limit is
  3,600 s). The whole command took 138 s.
- Harness: revision `d51d7172` of this repository
  (`provenance/campaign-revision.txt`); the command it ran is
  `provenance/command.txt`.
- Case studies: revision `168321b6306abdacee95b22c9c94996f1174ab2c`, the
  manifest `campaign/manifest.tsv` at the harness revision.
- Binaries (`provenance/binaries.tsv`): both at revision
  `5bf903b27a432f6998ed1b9c9c812b0abd49d371` of `nyandrianinamamy/frama-c`.
  The test binary is a git worktree at that revision; the reference binary
  was built from the same revision by `tools/build-reference.sh`. Their
  `eva.cmxs` are identical; the `frama-c` executables differ by the paths
  of their builds. The mode `reference` is therefore a second build of the
  binary under test, not an earlier memexec.
- Machine (`provenance/machine.txt`): Intel Core i5-14600KF, 20 hardware
  threads, 31 GB, Ubuntu 24.04, OCaml 5.2.1, Dune 3.21.1. The machine was
  shared with other jobs while the runs were serial, so the times are not a
  timing series.
- Raw logs: `campaign-pilot-2026-11-18.tar.gz`, outside this repository,
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

## Results

The tables are in `tables/tables.md`; `fixtures.txt` and
`outcome-demo.txt` hold the checks of the constructed cases.

- All 32 runs completed (8 cases; modes `nocache`, `cache`, `cache.2`,
  `reference`).
- Two runs of the same binary (`cache` and `cache.2`) align completely in
  every case, with equal state-query answers and alarms.
- Between `nocache` and `cache`, every record is aligned or nested under a
  hit (`accounted` is true), with no undecided group and no unmatched
  record. Alarms and property statuses are equal in every case.
- Hits with memexec: none in `jsmn-example`, `libyaml/test-version` and
  `khash`; 10 to 264 in the other cases.
- Set A: the membership of each run agrees with the count of issue #28 for
  the eight targets in every mode. In the mode `cache`, the counts of each
  builtin equal the recorded ones (genann: `malloc` 13, `free` 10; jsmn-main:
  35 and 35; khash: `malloc` 1, `calloc` 1, `realloc` 2, `free` 5). With
  caching disabled, genann applies `free` 22 times: memexec skips 12 calls
  to `genann_free`, which are hits.
- State queries, `nocache` against `cache`: the answers given by both runs
  are equal except in 2048 (20 narrower), jsmn-main (6 narrower) and genann
  (17 wider, 2 incomparable, listed in `genann-query-differences.tsv`). The
  answers that only `nocache` gives are for callstacks that memexec does not
  analyse.
- Fixtures: the second call to `outer` in `nested-hit.c` is reported as a
  hit with its two calls to `leaf` nested under it; the frame example of
  issue #3 gives `{3}` with memexec against `{3; 5}` before `r = 0;` over
  all callstacks, and no answer for the callstack of the second call. All
  checks pass.
- Outcome classes: the constructed runs are classified `timeout` (exit 124),
  `oom` (134), `error` (1) and `killed` (137).

### Differences in genann

These are findings of the pilot. They are not explained here.

- After `genann_free(second);` (test.c:220), `second` is a dangling address
  with caching disabled, and still points to `__malloc_genann_init_l123_6`
  with memexec, over all callstacks and in the callstack
  `main|persist@main:269:5`. With memexec, that call is a hit on the entry
  stored by the call to `genann_free` in `genann_read` (genann.c:169), so
  `free` is not applied again.
- The 17 wider answers are all over all callstacks, in `genann_init`,
  `genann_randomize` and `genann_train`; at these statements the answers of
  the callstacks present in both runs are equal. For example, before line 126,
  `ret->inputs` has no value in each callstack (it is not yet written), and
  `{1000}` over all callstacks with caching disabled against
  `[1..2147483646]` with memexec.
