# Campaign of reuse within one Eva analysis

This directory runs the Eva targets of the case studies in several modes of
caching and compares the runs. It implements the benchmark protocol of
[issue #21](https://github.com/nyandrianinamamy/frama-c/issues/21) of
`nyandrianinamamy/frama-c`; the harness and its pilot are
[issue #54](https://github.com/nyandrianinamamy/frama-c/issues/54).

| Path | Content |
|---|---|
| `manifest.tsv` | the cases: one Eva target in one fixed configuration |
| `run-campaign.sh` | the runner: runs cases in modes, compares, writes tables |
| `pilot.sh`, `pilot-cases.txt` | the pilot: one command for all its tables |
| `bin/frama-c-measure` | stands for `frama-c` in the recipes and measures Eva |
| `queries/campaign_queries.ml` | Frama-C module that answers the state queries |
| `tools/campaign.py` | records, alignment, query and alarm comparison, tables |
| `tools/build-reference.sh` | builds a Frama-C binary pinned by revision |
| `tools/make-manifest.sh` | regenerates the manifest |
| `tools/outcome-demo.sh` | constructed runs for each outcome class |
| `tools/archive-logs.sh` | packs the raw logs of a campaign, with their SHA-256 |
| `fixtures/` | constructed programs and the checks run on them |
| `reference/set-a-recorded.tsv` | set A membership recorded by issue #28 |
| `tests/test_campaign.py` | tests of `campaign.py` |
| `results/` | tables and provenance of campaigns that ran |

`campaign.py` uses the Python standard library only. Run it with
`python3 -I`. Its tests: `python3 -I -B -m unittest discover -s campaign/tests`.

## Cases

A case is one Eva target of the case studies with one fixed configuration.
Its identifier is `DIRECTORY/TARGET.eva/CONFIGURATION`, for instance
`jsmn/jsmn-main.eva/default`. The configuration `default` is the one of the
makefiles at the pinned revision; a changed precision configuration gets a
row of its own with another name.

`manifest.tsv` lists every Eva target at revision
`168321b6306abdacee95b22c9c94996f1174ab2c` (1,256 cases). Columns:

- `case`, `target`, `directory`, `configuration`;
- `oscs_revision`: the case-study revision that pins the inputs;
  `directory_tree`: the git tree of the directory at that revision;
- `entry_point`, `domains`, `precision` (the precision options of the Eva
  command), `harness` (sources inside the directory), `sources`, `machdep`;
- `parse_flags`, `eva_flags`: the commands written by the makefiles, with the
  paths into the Frama-C build written `${FRAMAC_SHARE}` and `${FRAMAC_LIB}`;
- `configuration_sha256`: SHA-256 of the parse flags, Eva flags and sources.

Regenerate it with
`campaign/tools/make-manifest.sh FRAMA_C_CHECKOUT REVISION campaign/manifest.tsv`.
It runs `make -n`, which writes the commands without running an analysis.

## Modes

| Mode | Binary | Eva option |
|---|---|---|
| `nocache` | under test | `-eva-no-memexec` |
| `cache` | under test | `-eva-memexec` |
| `reference` | reference, pinned by revision | `-eva-memexec` |

`cache` against `nocache` checks correctness: same binary, caching on and
off. `cache` against `reference` compares hits, misses and time with an
earlier binary. `--repeat MODE` runs a mode a second time as `MODE.2`; the two
runs of the same binary on the same case must align completely. Each mode
also gets `-eva-msg-key=+cache,+callstacks`, and the options of
`--extra-eva-flags` when given. The options of a mode are set in `run_one` of
`run-campaign.sh`.

The binaries must print the `[eva:cache]` message of each call and the
`builtin-applied-NAME` statistics. Both come from the call-cache seam of
`nyandrianinamamy/frama-c` (`docs/eva/reuse-correspondence/call-cache-seam.md`
there). A checkout is either a git working tree with no local change, whose
`HEAD` is recorded, or a directory made by `tools/build-reference.sh`, which
records its revision in `CAMPAIGN_REVISION`:

```sh
campaign/tools/build-reference.sh FRAMA_C_REPOSITORY REVISION DESTINATION [SWITCH]
```

`CAMPAIGN_PATCH` names a patch to apply on top of the revision; its SHA-256
is then recorded with the revision.

## Running

```sh
campaign/run-campaign.sh [--cases FILE] [--modes nocache,cache,reference] \
  [--repeat MODE] [--timeout SECONDS] [--memory-limit BYTES] \
  [--extra-eva-flags FLAGS] --test-checkout DIR [--reference-checkout DIR] \
  [--switch DIR] OUTPUT
```

`run-campaign.sh --help` lists the options. The default wall-time limit of
each Eva invocation is 3,600 s. Runs are serial and are not retried; a
mode that fails does not stop the other modes. Each run:

1. extracts the case-study sources at `oscs_revision` with `git archive` into
   a fresh directory, and removes any saved parse or Eva result;
2. runs the parse recipe of the target (`make TARGET.parse`);
3. runs the Eva recipe (`make TARGET.eva`) with `FRAMAC=bin/frama-c-measure`.
   The wrapper runs the Eva invocation under `timeout` (SIGTERM at the limit,
   SIGKILL 60 s later), under `prlimit --as` when a memory limit is given,
   and under GNU `time`, which writes the elapsed time, CPU times, peak
   resident memory and exit status. Make itself is not measured;
4. builds the per-call records from the log and classifies the outcome;
5. when the run completed, loads the saved session and answers the state
   queries. This step is not timed.

## Output

```
OUTPUT/
  provenance/  command.txt machine.txt binaries.tsv campaign-revision.txt
               manifest.tsv cases.txt
  tools/ROLE/  sites.env version plugins campaign_queries.cmxs checkout
  runs/CASE/MODE/
               run.tsv measure mode.mk parse-command eva-command
               eva.log.gz records.jsonl.gz queries.tsv.gz
               alarms.csv eva-stats.csv stats.txt metrics.log ...
  comparisons/CASE/A-vs-B/
               pair.tsv alignment-*.tsv queries-*.tsv alarms-*.tsv
  tables/      outcomes.tsv activity.tsv functions.tsv times.tsv
               alignment.tsv queries.tsv alarms.tsv tables.md
```

`provenance/` records the command, the machine (kernel, OS, CPU, memory,
toolchain, load at the start), the revision and SHA-256 of each binary and of
its `eva.cmxs`, and the revision of this harness. Paths under the home
directory are written from `~`.

`run.tsv` holds the case, mode, binary revision, case-study revision, start
time, outcome, exit status of each step, the measure, the limits and the
extra options.

### Outcomes

| Outcome | Meaning |
|---|---|
| `parse-error` | the parse recipe failed; Eva did not run |
| `harness-error` | the Eva invocation was not measured, or make failed after it |
| `oom` | Frama-C or the OCaml runtime reports exhausted memory |
| `timeout` | exit status 124, or 137 at or after the limit |
| `killed` | SIGKILL before the limit, as by the out-of-memory killer |
| `error` | any other nonzero status: 1 invalid input, 3 unimplemented, 4 internal error, 125 unexpected exception, or a signal |
| `incomplete` | status 0, but the entry point has no analysed record |
| `completed` | status 0 and the entry point was analysed |

A signal is recorded as status 128 + N. The case-study options hide the
`VALUES COMPUTED` banner, so completion is read from the per-call record of
the entry point. `tools/outcome-demo.sh` constructs one run for `timeout`,
`oom`, `error` and `killed`.

### Per-call records

The seam prints one message per call:

```
[eva:cache] FILE:LINE:
  call to F: lookup: L; execution: E; storage: S
  stack: F :: FILE:LINE <- CALLER :: FILE:LINE <- ... <- main
```

An analysed or interrupted call is printed after the calls it contains; a
hit is printed at its lookup. `campaign.py records LOG` rebuilds the tree of
calls from this order and the callstacks, and writes one JSON object per
call:

| Field | Content |
|---|---|
| `id` | invocation identity, see below |
| `parent`, `seq`, `children` | parent identity, order in the log, number of calls inside |
| `function`, `site`, `entry_point`, `callstack` | the call and its stack |
| `dispositions` | every `KEY: VALUE` part of the message, verbatim |
| `lookup`, `execution`, `storage` | each disposition up to its first space or parenthesis: `no-candidate`, `hit`, `analysed`, `not-analysed`, `interrupted`, `stored`, `none`, `refused`, or a kind added later |
| `hit_of` | for a hit on `entry N`, the identity of the call that stored entry N |

The identity of a call is the identity of its parent, then
`FUNCTION@SITE#K` where K counts the earlier calls to the same function from
the same site in the same parent; the entry point is `main#0`. For example
`main#0 > outer@nested-hit.c:14#0 > leaf@nested-hit.c:9#1`. Unknown
dispositions, reasons and fields are kept verbatim. A log cut by a timeout
or a kill leaves calls with no message; their parents are rebuilt from the
callstacks of their children, and the problems are written to
`records-problems.log`.

### Alignment of two runs

`campaign.py align A B PREFIX` aligns the records of two runs from the entry
point down. Two calls align when their parents align and they have the same
function and call site, and either the sequence of (function, site) of the
siblings is the same in both runs (aligned by position), or the pair
(function, site) occurs once among the siblings of each run. Otherwise:

- calls inside a call that is a hit in one run and analysed in the other are
  *nested under a hit*, not aligned;
- a group of siblings with the same (function, site) that occurs several
  times on a side and does not align by position is *undecided*: it is
  reported with its sizes, not guessed;
- a call present in one run only is *unmatched*, with its descendants.

`alignment-summary.tsv` counts the records of each run, the aligned pairs and
those whose dispositions differ, the hits of one run analysed in the other
(`hit_a_analysed_b`, `analysed_a_hit_b`), the records of A nested under a hit
of B (`nested_under_hit_b`) and the converse (`nested_under_hit_a`), the
unmatched records and the undecided groups. `accounted` is true when every
record is in exactly one of these classes; `complete` when every record of
both runs is aligned. The individual records are in `alignment-differences`,
`-under-hit`, `-unmatched` and `-undecided.tsv`.

### State queries

`queries/campaign_queries.ml` is loaded with `-load framac.sav -load-module
campaign_queries.cmxs` and writes to the file named by `CAMPAIGN_QUERIES_OUT`.
It uses the public `Eva.Results` API. A query is a statement, a point
(`before` or `after`), a callstack or all callstacks (`*`), and a scalar
lvalue. The enumerated queries are, for each reached statement, the scalar
lvalues of the statement itself. `CAMPAIGN_QUERIES_NAMED` adds named queries
(`FUNCTION LINE POINT VARIABLE`). Keys do not depend on the numbering of the
AST: a statement is `FUNCTION:LINE:K`, a callstack is
`main|CALLEE@CALLER:LINE:K|...`.

Values: `T` (top), `G` and the bases of a garbled mix, or `M` and
`BASE=OFFSETS` for each base, where `NULL` holds the integers. Offsets:
`S1,2,3` (small set), `IMIN..MAX%R/M` (empty bound: unbounded), `FMIN..MAX`
in hexadecimal with `;nan` when NaN is possible, `Fnan`, `B` (bottom). Base
names never contain `;` or `=`, so the suffix `;nan` is told apart from the
separator of the bases.

`campaign.py queries A B PREFIX` compares the answer of B with that of A:
`equal`, `wider`, `narrower`, `incomparable`, or `undecided` when the written
forms do not decide inclusion. Two identical written answers are `equal`. An
answer that may be uninitialized or an escaping address is included only in
another that may be too. The answer over all callstacks is an evaluation in
the state joined over the callstacks, which can differ from the join of the
answers of each callstack. It counts top answers on each side, and the
queries without an answer on a side by reason: `unreached`, `no-callstack`
(the statement is reached but not under that callstack), `error`, `missing`.
Every query that is not `equal` is listed in `queries-differences.tsv`. The
summary also gives the statements reached in one run only.

### Alarms

`campaign.py alarms A B` compares the `alarms.csv` files of the two runs,
keyed by file, line, function, property kind and property: same status,
other status, present in one run only. The differences are listed.

### Tables

`campaign.py tables OUTPUT --recorded-set-a reference/set-a-recorded.tsv`
writes `tables/`, which `run-campaign.sh` does at the end:

- `outcomes.tsv`: outcome, exit status, elapsed and user time, peak resident
  memory and limit of each invocation;
- `activity.tsv`: hits, misses, stores and refusals per run, the
  applications of the allocation and release builtins (`malloc`, `calloc`,
  `realloc`, `reallocarray`, `alloca`, the VLA allocator, `free`, the VLA
  release, under their libc or `Frama_C_` names), set A membership (no such
  application) and its agreement with the recorded count;
- `functions.tsv`: hits, misses, stores and refusals per function;
- `times.tsv`: elapsed time per mode and the ratios cache/nocache and
  cache/reference when both runs completed;
- `alignment.tsv`, `queries.tsv`, `alarms.tsv`: the comparison summaries;
- `tables.md`: all of the above but `functions.tsv`, as Markdown.

## Pilot

```sh
campaign/pilot.sh OUTPUT TEST_CHECKOUT REFERENCE_CHECKOUT [SWITCH]
```

runs the cases of `pilot-cases.txt` in the modes `nocache`, `cache`,
`cache.2` and `reference`, with a limit of `PILOT_TIMEOUT` seconds (180 by
default) and an address-space limit of `PILOT_MEMORY_LIMIT` bytes (8 GB by
default). It then runs the fixtures and the outcome demonstration, and
appends their checks to `tables/tables.md`. It exits with 1 when a check
fails.

The fixtures (`fixtures/run-fixtures.sh`) run Frama-C directly on two
programs, outside the manifest:

- `nested-hit.c`: the second call to `outer` is analysed with caching off and
  a hit with memexec; the two calls to `leaf` inside it must be reported as
  nested under the hit, and two runs with memexec must align completely;
- `frame.c`: the program of the example run of issue #3. Before `r = 0;` in
  `get`, over all callstacks, `r` is `{3; 5}` with caching off and `{3}`
  with memexec, which must be reported as narrower; the callstack of the
  second call to `get` has no answer with memexec.

`stage1-pilot.sh` at the root of the case studies runs the two jsmn targets
in the modes `nocache` and `cache` through the same runner.

## Results and raw logs

`results/NAME/` keeps the tables, provenance and checks of a campaign that
ran. The raw logs (`runs/`, `comparisons/`, the outcome demonstration) are
not committed: they go to an archive, whose SHA-256 is recorded in
`results/NAME/raw-logs.sha256`:

```sh
campaign/tools/archive-logs.sh OUTPUT /outside/the/tree/NAME.tar.gz
```

The archive writes the paths under the home directory from `~` and leaves
out the compiled query modules; the same output gives the same archive. The protocol attaches this archive to the tag
of the campaign on GitHub, which is made when the branch is published. To
check a copy of the archive, run `sha256sum -c raw-logs.sha256` in its
directory.

To replay a campaign, build the binaries at the revisions of
`provenance/binaries.tsv` with `tools/build-reference.sh`, check out this
repository at the revision of `provenance/campaign-revision.txt`, and run the
command of `provenance/command.txt`. Timings depend on the machine and its
load, which `provenance/machine.txt` records.
