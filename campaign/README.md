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
| `bin/watchdog.py` | runs Eva under the wall-time and memory limits and measures it |
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
  paths into the Frama-C build written `${FRAMAC_SHARE}` and `${FRAMAC_LIB}`,
  and the paths into the temporary snapshot (the `-ffile-prefix-map` option
  of `genann`) written `${SNAPSHOT}`;
- `configuration_sha256`: SHA-256 of the parse flags, Eva flags and sources.

Regenerate it with
`campaign/tools/make-manifest.sh FRAMA_C_CHECKOUT REVISION campaign/manifest.tsv`.
It runs `make -n`, which writes the commands without running an analysis, in
a fresh temporary snapshot; two runs give the same file. The runner does not
read the commands of the manifest: it runs the recipes of the makefiles.

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
there). In the binaries of the pilot, the body access collector and the
producer of cache entries are on by default in every mode: each analysed
call gets a collector verdict, and the producer stores entries that no
lookup reads. `--extra-eva-flags -eva-no-cache-collect` turns both off.

A checkout is either a git working tree with no local change, whose `HEAD`
is recorded, or a directory made by `tools/build-reference.sh`, which records
its revision in `CAMPAIGN_REVISION`:

```sh
campaign/tools/build-reference.sh [--no-build] FRAMA_C_REPOSITORY REVISION DESTINATION [SWITCH]
```

`CAMPAIGN_PATCH` names a patch to apply on top of the revision. The
directory then keeps the patch as `CAMPAIGN_PATCH.patch` and its SHA-256 in
`CAMPAIGN_PATCH_SHA256`. The runner records the revision and the SHA-256 in
two columns of `provenance/binaries.tsv`, and copies the patch to
`provenance/patches/ROLE.patch`; it stops when the patch no longer matches
its SHA-256. `--no-build` makes the directory without building Frama-C.

The counters that a binary can write are read from its `eva.cmxs`, in
families: `builtin` (`builtin-applied-*`), `memexec` (`memexec-*`),
`supplied` (`cache-hits`, `cache-rejected-*`, `cache-refused-*`),
`collector` (`collector-*`) and `producer` (`cache-produced`,
`cache-production-refused-*`). A run measures the families of its binary
that its options do not turn off: `-eva-no-memexec` turns off `memexec`,
`-eva-no-cache-collect` turns off `collector` and `producer`. The statistics
file has no row for a counter that stays at 0, so a counter of a measured
family with no row is a measured 0, and a counter of a family that is not
measured is written `-` in the tables.

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
   The wrapper runs the Eva invocation under `bin/watchdog.py`, in a
   session of its own, with an address-space limit when a memory limit is
   given. At the wall-time limit the watchdog sends SIGTERM to the session,
   and SIGKILL 60 s later. It writes the elapsed time, CPU times, peak
   resident memory, exit status or signal, whether it fired and when, and
   the evidence of the out-of-memory killer that it can read: the increase
   of `oom_kill` in the memory events of its cgroup, and, for a SIGKILL that
   it did not send, the kernel log (`unreadable` when `dmesg` is not
   allowed). Make itself is not measured;
4. builds the per-call records from the log and classifies the outcome;
5. when the run completed, loads the saved session and answers the state
   queries. This step is not timed.

## Output

```
OUTPUT/
  provenance/  command.txt machine.txt binaries.tsv campaign-revision.txt
               manifest.tsv manifest.sha256 cases.txt patches/
  tools/ROLE/  sites.env version plugins campaign_queries.cmxs checkout
  runs/CASE/MODE/
               run.tsv measure mode.mk parse-command eva-command
               eva.log.gz records.jsonl.gz queries.tsv.gz
               alarms.csv eva-stats.csv stats.txt metrics.log ...
  comparisons/CASE/A-vs-B/
               pair.tsv alignment-*.tsv queries-*.tsv alarms-*.tsv
  tables/      outcomes.tsv activity.tsv collector.tsv functions.tsv
               times.tsv alignment.tsv queries.tsv alarms.tsv tables.md
```

`provenance/` records the command, the machine (kernel, OS, CPU, memory,
toolchain, load at the start), for each binary its revision, the SHA-256 and
copy of its patch, the SHA-256 of the binary and of its `eva.cmxs` and its
counter families, the revision of this harness, and the manifest actually
used (`--manifest` may name another one than `manifest.tsv`) with its
SHA-256. Paths under the home directory are written from `~`.

`run.tsv` holds the case, mode, binary revision and patch SHA-256, counter
families, case-study revision, start time, outcome and its out-of-memory
evidence, exit status of each step, the measure, the limits and the extra
options.

### Outcomes

| Outcome | Meaning |
|---|---|
| `parse-error` | the parse recipe failed; Eva did not run |
| `harness-error` | the Eva invocation was not measured, or make failed after it |
| `timeout` | the watchdog fired at the wall-time limit |
| `oom` | Frama-C or the OCaml runtime reports exhausted memory, or the cgroup or the kernel log reports the out-of-memory killer |
| `killed` | killed by SIGKILL that the watchdog did not send, with no evidence of the out-of-memory killer: cause unknown |
| `error` | any other nonzero status: 1 invalid input, 3 unimplemented, 4 internal error, 125 unexpected exception, another signal, or 124 |
| `incomplete` | status 0, but the entry point has no analysed record |
| `completed` | status 0 and the entry point was analysed |

The classes are tried in the order of the table. A signal is recorded as
status 128 + N. A timeout is never inferred from the status or the elapsed
time: a program can exit with 124, and a SIGKILL near the limit can come
from elsewhere. The case-study options hide the `VALUES COMPUTED` banner, so
completion is read from the per-call record of the entry point.
`tools/outcome-demo.sh` constructs one run for `timeout`, `oom`, `error` and
`killed`.

### Per-call records

The seam prints one message per call that reaches it: a call analysed
through the body of the called function, or answered by a cache. A call
resolved by a builtin or by the specification of the called function
reaches no cache and prints no message; the statistic `builtin-applied-NAME`
counts the applications of each builtin, and no message or statistic counts
the calls resolved by a specification. The records below therefore cover the
calls that reach the seam, not every reached call.

```
[eva:cache] FILE:LINE:
  call to F: lookup: L; execution: E; storage: S; collector: C
  stack: F :: FILE:LINE (stmt N) <- CALLER :: FILE:LINE (stmt M) <- ... <- main
```

The lookup `L` is `no-candidate`, or the candidates rejected, oldest first,
then the entry used, as in `rejected (entry 1: key-differs), hit (entry 2)`.
The collector verdict `C` (`would-store` or `refused (REASON)`) follows an
analysed call when the collector is on. `N` is the number of the call
statement in the AST: two calls on one line differ. A long stack is broken
over several lines. The producer prints its own messages in the category
`cache-producer`, read in the same way. An analysed or interrupted call is
printed after the calls it contains; a hit is printed at its lookup.
`campaign.py records LOG` rebuilds the tree of calls from this order and the
callstacks, and writes one JSON object per call:

| Field | Content |
|---|---|
| `id` | invocation identity, see below |
| `parent`, `seq`, `children` | parent identity, order in the log, number of calls inside |
| `function`, `site`, `entry_point`, `callstack` | the call and its stack |
| `dispositions` | every `KEY: VALUE` part of the message, verbatim |
| `stmt` | the number of the call statement, or null in a log without it |
| `lookup` | `hit` when an entry was used, else `rejected` when a candidate was rejected, else `no-candidate`, or the disposition verbatim |
| `lookup_rejected`, `lookup_hit_entry`, `lookup_other` | each rejected candidate with its entry and reason, the entry used, and the parts of the lookup that are not understood, verbatim |
| `execution`, `storage`, `collector` | each disposition up to its first space or parenthesis: `analysed`, `not-analysed`, `interrupted`, `stored`, `none`, `refused`, `would-store`, or a kind added later |
| `hit_of` | for a hit on `entry N`, the identity of the call that stored entry N |
| `inferred` | true for a call with no message, rebuilt from the stacks of its callees |

The identity of a call is the identity of its parent, then
`FUNCTION@SITE/sN#K` where `N` is the number of the call statement and K
counts the earlier calls to the same function from the same statement in the
same parent; the entry point is `main#0`. For example
`main#0 > outer@nested.c:13/s12#0 > leaf@nested.c:9/s5#1`. Without
statement numbers the site is `FUNCTION@FILE:LINE`. Unknown dispositions,
reasons and fields are kept verbatim.

A log cut by a timeout or a kill leaves calls with no message. Their
messages would come after those of their callees, so the calls still open
are rebuilt from the stacks of the callees: one open call per entry point
and full stack, shared by all the callees printed under it. These calls are
marked `inferred` and their execution is `open (no message)`. The problems
found (an interrupted log, a message whose stack does not fit the calls
still open) are written as `{"problem": ...}` lines of `records.jsonl` and
to `records-problems.log`.

### Alignment of two runs

`campaign.py align A B PREFIX` aligns the records of two runs from the entry
point down. The call site includes the statement number, so two calls on one
line are told apart; statement numbers are compared only when both runs
number the statements alike, which the runner asserts with
`--same-numbering` when the two binaries have the same revision and patch.
Two calls align when their parents align and they have the same function and
call site, and either the sequence of (function, site) of the siblings is the
same in both runs (aligned by position), or the pair (function, site) occurs
once among the siblings of each run. Otherwise:

- calls inside a call that is a hit in one run and analysed in the other are
  *nested under a hit*, not aligned;
- a group of siblings with the same (function, site) that occurs several
  times on a side and does not align by position is *undecided*: it is
  reported with its sizes, not guessed;
- in a log without statement numbers, every call below the entry point is
  undecided (`no statement number`): two calls on one line cannot be told
  apart, so none is aligned;
- a call present in one run only is *unmatched*, with its descendants.

`alignment-summary.tsv` counts the records of each run (`records_*`, from
messages) apart from the inferred calls (`inferred_*`), the aligned pairs of
records and those whose dispositions differ, the pairs that involve an
inferred call (`aligned_with_inferred`), the hits of one run analysed in the
other (`hit_a_analysed_b`, `analysed_a_hit_b`), the records of A nested under
a hit of B (`nested_under_hit_b`) and the converse (`nested_under_hit_a`),
the unmatched records and the undecided groups. It also says whether each
run was interrupted, how many structural problems each log has, whether the
logs give the statement numbers (`all`, `none` or `some`) and whether the
numbering is the same. `accounted` is true when every record is in exactly
one of these classes. `complete` is true when every record of both runs is
aligned, no call is inferred or interrupted, no problem was found, both
logs give the statement numbers and the numbering is the same; `verdict`
lists the reasons when it is false. The individual records are in
`alignment-differences`, `-under-hit`, `-unmatched` and `-undecided.tsv`,
and the problems in `alignment-problems.tsv`.

### State queries

`queries/campaign_queries.ml` is loaded with `-load framac.sav -load-module
campaign_queries.cmxs` and writes to the file named by `CAMPAIGN_QUERIES_OUT`.
It uses the public `Eva.Results` API. A query is a statement, a point
(`before` or `after`), a callstack or all callstacks (`*`), and a scalar
lvalue. The enumerated queries are, for each reached statement, the scalar
lvalues of the statement itself, and, for each function analysed, the
scalar lvalues of its body at its exit (`FUNCTION:exit`, point `exit`).
`CAMPAIGN_QUERIES_NAMED` adds named queries (`FUNCTION LINE POINT
VARIABLE`). Keys do not depend on the numbering of the AST: a statement is
`FUNCTION:LINE:K`, a callstack is `main|CALLEE@CALLER:LINE:K|...`.

Before it evaluates a query, the module checks that the state is available.
When it is not, it writes an `unavailable` line with the reason instead of
an answer: `no-results` (the results of the function were not saved, as
with `-eva-no-results`), `top-state` or `disabled-domain`. The file ends with
`done COUNT`, where COUNT is the number of answer, unavailable and error
lines; a file without this line, or with another count, is incomplete.

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
another that may be too. Numbers follow the inclusion of Eva between its
forms: a float interval is included in the integers only when these are
unbounded, and a set of integers in a float interval only when it is `{0}`
and the interval contains +0. The answer over all callstacks is an
evaluation in the state joined over the callstacks, which can differ from
the join of the answers of each callstack.

An answer is top when it is `T`, or when it has no address and its numbers
are all the integers (`MNULL=I..%0/1`) or all the floats and NaN. A garbled
mix, or an address with an unbounded offset (`Mx=I..%0/1`), is not top: it
keeps its bases. Top answers are counted on each side over all the answers
of that side, whatever the other run answers.

The summary counts the queries answered in both runs and on each side, and
the queries without an answer on a side by reason: `unreached`,
`no-callstack` (the statement is reached but not under that callstack),
`no-results`, `top-state`, `disabled-domain`, `error`, `missing`. It says
whether each file is complete (`complete_a`, `complete_b`) and whether the
comparison is (`comparison`). Every query that is not `equal` is listed in
`queries-differences.tsv`, and the statements reached in one run only in
`queries-reached-in-one-run.tsv`.

### Alarms

`campaign.py alarms A B --root-a DIR --root-b DIR` compares the
`alarms.csv` files of the two runs, keyed by directory, file, line,
function, property kind and property: same status, other status, present in
one run only. Each run has its own source snapshot, so a directory under the
given root is written from `${SRC}`. A key that occurs several times in a
file is counted (`duplicate_keys_*`) and its statuses are compared as a
multiset, so a change of one of them is not lost. The differences are
listed.

### Tables

`campaign.py tables OUTPUT --recorded-set-a reference/set-a-recorded.tsv`
writes `tables/`, which `run-campaign.sh` does at the end:

- `outcomes.tsv`: outcome, exit status, signal, whether the watchdog fired,
  the out-of-memory evidence, elapsed and user time, peak resident memory
  and limit of each invocation;
- `activity.tsv`: memexec hits, misses, stores and refusals per run, the
  applications of the allocation and release builtins (`malloc`, `calloc`,
  `realloc`, `reallocarray`, `alloca`, the VLA allocator, `free`, the VLA
  release, under their libc or `Frama_C_` names), set A membership (no such
  application) and its agreement with the recorded count;
- `collector.tsv`: the collector verdicts, the entries stored or refused by
  the producer, and the counters of supplied entries, per run;
- `functions.tsv`: memexec activity and collector verdicts per function;
- `times.tsv`: elapsed time per mode and the ratios cache/nocache and
  cache/reference when both runs completed;
- `alignment.tsv`, `queries.tsv`, `alarms.tsv`: the comparison summaries,
  with `both_completed` for each pair, and for each comparison the number of
  pairs, of pairs compared, and of pairs whose two runs completed;
- `tables.md`: all of the above but `functions.tsv`, as Markdown.

A cell `-` is a value that was not measured, such as a memexec counter in
the mode `nocache`.

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

The fixtures (`fixtures/run-fixtures.sh`) run Frama-C directly on three
programs, outside the manifest:

- `nested-hit.c`: the second call to `outer` is analysed with caching off and
  a hit with memexec; the two calls to `leaf` inside it must be reported as
  nested under the hit, and two runs with memexec must align completely;
- `frame.c`: the program of the example run of issue #3. Before `r = 0;` in
  `get`, `r` is `{3}` in both runs under the callstack of the first call,
  `{5}` with caching off and no answer with memexec under the callstack of
  the second call, and over all callstacks `{3; 5}` with caching off against
  `{3}` with memexec, which must be reported as narrower;
- `same-line.c`: two calls to `f` on one line, one on each branch of an `if`
  whose condition is a global set by `-DSIDE`; the runs with `SIDE` 0 and 1
  analyse the same AST and take opposite branches. Their calls to `f` must
  be unmatched, not aligned, and the alignment must not be complete.

`stage1-pilot.sh` at the root of the case studies runs the two jsmn targets
in the modes `nocache` and `cache` through the same runner, and exits with 1
unless the four runs completed.

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
