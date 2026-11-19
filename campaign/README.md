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
| `tools/export-ast.sh` | lists again the AST of runs recorded before its digest |
| `fixtures/` | constructed programs and the checks run on them |
| `reference/set-a-recorded.tsv` | set A membership recorded by issue #28 |
| `tests/test_campaign.py` | tests of `campaign.py` |
| `results/` | tables and provenance of campaigns that ran |

`campaign.py` uses the Python standard library only. Run it with
`python3 -I`, which its first line also does. Its tests:
`python3 -I -B -m unittest discover -s campaign/tests`. Every script with a
`#!` line is executable.

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
`cache-production-refused-*`). A family is measured by a run when the
invocation that wrote its statistics file gives evidence for it: a row of
the family in that file, or, for a family that the binary has, its
dispositions in the log: for `memexec` a storage `stored` or `refused` for
another reason than `disabled`, or a hit; for `collector` a `collector:`
field; for `producer` a `producer:` field. The dispositions count only when
the records form one tree: a log of two analyses would not say which one
wrote the statistics, which Eva writes at the end of each analysis.

When the command that ran Eva has one stage, its options also decide. The
options are those of that command (the file `command` written by the
makefiles, or `eva-command` of a fixture), in their order, so options added
by a makefile after those of the mode count: the last of `-eva-memexec` and
`-eva-no-memexec` decides `memexec` (off by default), and the last of
`-eva-cache-collect` and `-eva-no-cache-collect` decides `collector` and
`producer` (on by default). A run whose log prints `storage: refused
(disabled)` did not run memexec, whatever its options, so its options do not
make `memexec` measured. A command with `-then`, `-then-on`, `-then-last`,
`-then-replace` or `-commands-file` is resolved by the evidence alone: its
options do not say which of them the invocation that wrote the statistics
had. The stage that `analysis.mk` adds after Eva (`-then -report-csv ...
-metrics-eva-cover ... -nonterm`) is not part of the recorded command; it
sets no Eva option and does not run Eva again, so the recorded command
counts as one stage. The mode name is not used. The statistics file has no
row for a counter that stays at 0, so a counter of a measured family with no
row is a measured 0, and a counter of a family that is not measured is
written `-` in the tables.

## Running

```sh
campaign/run-campaign.sh [--cases FILE] [--modes nocache,cache,reference] \
  [--repeat MODE] [--timeout SECONDS] [--memory-limit BYTES] \
  [--extra-eva-flags FLAGS] [--dedicated-scope] --test-checkout DIR \
  [--reference-checkout DIR] [--switch DIR] OUTPUT
```

`run-campaign.sh --help` lists the options. The default wall-time limit of
each Eva invocation is 3,600 s. Runs are serial and are not retried; a
mode that fails does not stop the other modes.

The runner records the SHA-256 of the manifest and of the patch of each
binary on their bytes, and the archive keeps these bytes (see below). It
therefore stops before it writes anything when the manifest or a patch
contains the home directory: write the path as `~` or as a variable. The
home directory is looked for in each of its spellings: the value of `HOME`
without its trailing slashes and its physical path, when `HOME` is a
symbolic link, each followed by a separator, by a character that cannot
continue a file name, or by the end (`campaign.py home`). The provenance,
the redaction of the archive and its final check use the same spellings.

Each run:

1. extracts the case-study sources at `oscs_revision` with `git archive` into
   a fresh directory, and removes any saved parse or Eva result;
2. runs the parse recipe of the target (`make TARGET.parse`). For this step
   alone, `bin/frama-c-measure` adds `-keep-temp-files` and `-kernel-msg-key
   pp` and sets `TMPDIR` to a directory of the run: Frama-C prints each
   preprocessing command and keeps each preprocessed file there.
   `campaign.py preprocessing` records their digests in `run.tsv` (see
   Alignment of two runs) and the commands in `preprocessing.txt`, then the
   directory is removed. The Eva recipe loads the session of this parse and
   does not preprocess again;
3. runs the Eva recipe (`make TARGET.eva`) with `FRAMAC=bin/frama-c-measure`.
   The wrapper runs the Eva invocation under `bin/watchdog.py`, in a
   session of its own, with an address-space limit when a memory limit is
   given. At the wall-time limit the watchdog sends SIGTERM to the session,
   and SIGKILL 60 s later. It writes the elapsed time, CPU times, peak
   resident memory, exit status or signal, whether it fired and when, and
   the evidence of the out-of-memory killer that it can read: the increase
   of `oom_kill` in the memory events of its cgroup, whether that cgroup
   held other processes (`cgroup_exclusive`, see Outcomes), and, for a
   SIGKILL that it did not send, the kernel log (`unreadable` when `dmesg`
   is not allowed). Make itself is not measured;
4. builds the per-call records from the log and classifies the outcome;
5. loads the session saved by the parse recipe, which the Eva recipe loads,
   and lists its AST (see Alignment of two runs); `run.tsv` records the
   format of the listing (`ast_format`), its SHA-256 (`ast_sha256`, `-` when
   it could not be written) and its number of statements. This step is not
   timed;
6. when the run completed, loads the session saved by Eva and answers the
   state queries. This step is not timed.

## Output

```
OUTPUT/
  provenance/  command.txt machine.txt binaries.tsv campaign-revision.txt
               manifest.tsv manifest.sha256 cases.txt patches/
  tools/ROLE/  sites.env version plugins campaign_queries.cmxs checkout
  runs/CASE/MODE/
               run.tsv measure mode.mk parse-command eva-command
               eva.log.gz records.jsonl.gz queries.tsv.gz ast.tsv.gz
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
families, case-study revision, entry point, start time, outcome and its
out-of-memory evidence, whether the runner states a dedicated scope
(`dedicated_scope`), exit status of each step, the measure, the limits, the
extra options, and the SHA-256 and size of the AST listing.

### Outcomes

| Outcome | Meaning |
|---|---|
| `parse-error` | the parse recipe failed; Eva did not run |
| `harness-error` | the Eva invocation was not measured, or make failed after it |
| `timeout` | the watchdog fired at the wall-time limit |
| `oom` | Frama-C or the OCaml runtime reports exhausted memory; or a SIGKILL that the watchdog did not send, and the kernel log names the process, or `oom_kill` rose in a scope that the runner states it created for the measured invocation (`--dedicated-scope`) |
| `killed` | killed by SIGKILL that the watchdog did not send, with no evidence that the out-of-memory killer chose this process: cause unknown |
| `error` | any other nonzero status: 1 invalid input, 3 unimplemented, 4 internal error, 125 unexpected exception, another signal, or 124 |
| `incomplete` | status 0, but the records are not one tree whose root is the analysed call of the entry point |
| `completed` | status 0 and the entry point was analysed |

The classes are tried in the order of the table. The entry point is the one
configured for the target (the column `entry_point` of the manifest,
recorded in `run.tsv`; `main` for the fixtures): the records of a completed
run have one root, the analysed call of that function, and every callstack
ends in it. A log whose stacks end in another function, or that holds a
second tree after that of the entry point, is `incomplete`. A signal is
recorded as status 128 + N. A timeout is never inferred from the status or
the elapsed time: a program can exit with 124, and a SIGKILL near the limit
can come from elsewhere. The case-study options hide the `VALUES COMPUTED`
banner, so completion is read from the per-call record of the entry point.
`tools/outcome-demo.sh` constructs one run for `timeout`, `oom`, `error` and
`killed`.

The counter `oom_kill` belongs to the cgroup of the watchdog, which is
usually shared with the shell, the runner and anything else started in the
same session. A rise of it then says that the killer chose some process of
the cgroup, not this one. The watchdog also samples the processes of its
cgroup at the start and every half second, and writes `cgroup_exclusive
yes` when every sample lists only itself and the session of the measured
command. Neither decides the class: a sample does not show that the command
was in the cgroup, nor that no other process ran in it between two
samples. Without other evidence the run is `killed`, and the rise and the
samples are kept in `oom_evidence` (`cgroup oom_kill +N, samples exclusive
yes, no dedicated scope`).

The runner does not create cgroups. A rise of the counter is the cause only
when the watchdog runs in a scope created for the measured invocation, and
the runner says so with `--dedicated-scope`, which `run.tsv` records as
`dedicated_scope yes`. To provide it, start the watchdog in a transient
scope: in `bin/frama-c-measure`, replace `exec python3 -I` by
`exec systemd-run --user --scope --quiet -p MemoryMax=BYTES python3 -I`, and
pass `--dedicated-scope` to the runner. The scope then holds the watchdog and
the session of the command; the watchdog survives a kill, since it writes
the measure, so the process that the killer chose is the measured command.
The runner checks neither the scope nor the statement. Without it, `oom`
after a SIGKILL needs the kernel log, which `dmesg` may not let a user read.

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
over several lines. When the category `cache-producer` is enabled, the
message of a call whose body produced an entry or a refusal is printed in
that category instead, with the verdict of the producer as its last field
(`producer: stored (entry N)` or `producer: refused (REASON)`); `records`
reads both categories. The runner does not enable it. An analysed or
interrupted call is printed after the calls it contains; a hit is printed at
its lookup. `campaign.py records LOG` rebuilds the tree of calls from this
order and the callstacks, and writes one JSON object per call:

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

A log can also be cut inside a message. Each stack is checked: its last
frame is the name of the entry point, which is the called function of a
message without location; every other frame has a function name and a call
site `FILE:LINE`, with `(stmt N)` when the log numbers the statements; the
first frame is the called function. A message that is not a call
disposition, has no stack, or whose stack fails these checks gives a
structural problem instead of a record; `records` never stops on it.

### Alignment of two runs

`campaign.py align A B PREFIX` aligns the records of two runs from the entry
point down. The call site includes the statement number, so two calls on one
line are told apart. Statement numbers are compared only when both runs
number the statements alike, which is established from the program, not
from the binary: two runs of one binary whose preprocessing differs (a
macro in a condition, say) can give one statement number to different calls.

The query module lists the AST when `CAMPAIGN_AST_OUT` names a file. The
listing starts with the line `format 2`. Then, for each global in order, a
line `global KIND NAME RANGE TEXT`, where `TEXT` is the printed declaration
with its initial value (for a function, its prototype and locals, without
body or contract), followed for a function by a line `stmt FUNCTION SID
RANGE TEXT` for each of its statements, where `TEXT` is the printed
statement with its sub-statements named by their numbers. It ends with `done
COUNT`, the number of these lines. `RANGE` is `FILE:LINE@L1:C1-L2:C2`: the
file and line where the element starts, relative to the directory of the
analysis, then the line and column of its start and of its end in the text
that Frama-C parsed. Two calls of one text on one line, such as the branches
of `if (c) f(1); else f(1);`, have different ranges. Paths of the libc of
Frama-C are written from `FRAMAC_SHARE`, so two snapshots and two builds
give the same listing. `campaign.py ast LISTING` prints its format
(`ast_format`) and its SHA-256 (`ast_sha256`) over every line but the last,
or `-` when the listing is missing, cut or of another format. The format 1
of the previous revisions listed the statements alone, without their
columns; its digests establish nothing.

The parse step of each run also records the evidence of its preprocessing
(`campaign.py preprocessing LOG TMPDIR`): one command per file parsed, read
from the messages `preprocessing with "..."`, and the preprocessed file that
each wrote, kept in `TMPDIR`. In both, the temporary directory is written
`${TMP}`, the directory of the sources of the run `${SRC}`, the share
directory of the binary `${FRAMAC_SHARE}`, and the random part of the
temporary names is removed. `run.tsv` records the number of files
(`pp_files`), the SHA-256 of the commands (`pp_command_sha256`) and of the
digests of the preprocessed texts (`pp_text_sha256`). The preprocessed text
keeps the macro definitions (`-dD`), so a macro that no statement uses still
changes it. When a file is parsed without preprocessing, a command or a
preprocessed file is missing, the digests are `-` and `pp_problem` says why.
The numbering of two runs is:

| Numbering | When |
|---|---|
| `same` | the AST digests are equal, and so are the preprocessing digests |
| `preprocessing differs` | the AST digests are equal, the preprocessing digests differ |
| `different` | the AST digests differ |
| `recorded command` | runs of an archive whose AST was listed again afterwards, see Results: equal AST digests and equal recorded preprocessing |
| `not established` | anything else: a digest missing, a listing of another format |
| `asserted` | runs recorded before the digest existed, see Results |

`align` takes the digests (`--ast-a`, `--ast-b`, and `--pp-a`, `--pp-b` for
the preprocessing, as `PP_COMMAND_SHA256:PP_TEXT_SHA256`), the outcomes of
the runs (`--outcome-a`, `--outcome-b`) and the entry point configured for
the target (`--entry-point`); `campaign.py compare OUTPUT CASE A B` reads
them from the `run.tsv` of two runs and writes all the comparisons of the
pair, as the runner does. A run recorded before `run.tsv` held the entry
point takes the one of its case in `provenance/manifest.tsv`, else the last
`-main` of its Eva command, else `main`. Each log must be one tree of that
entry point: one root, its call, and every callstack ending in it. A second
root, a root of another function or a stack that ends elsewhere is a
structural problem of that log, and the alignment is not complete without
the entry point.
Unless the numbering is `same`, `recorded command` or `asserted`, every
group of calls below the entry point is undecided, with the reason `AST
digests differ`, `preprocessing differs` or `numbering not established`, and
none is aligned. Only `same` lets an alignment be complete.
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
numbering is the same (`numbering`), the entry point (`entry_point`),
whether each log has the record of the entry point as its only root
(`entry_point_a`, `entry_point_b`) and the outcome of each run. `accounted`
is true when every record is in exactly one of these classes. `complete` is
true when both runs completed, both logs have that record, every record of
both runs is aligned, no call is inferred or interrupted, no problem was
found, both logs give the statement numbers and the numbering is `same`;
`verdict` is then `complete`. When the only reason against it is an
`asserted` numbering, `verdict` is `numbering asserted from equal revision,
patch, options and preprocessing, not checked by digest`; when it is a
`recorded command` numbering, `AST digests equal, preprocessing compared by
the recorded command only`; otherwise it lists the reasons. The individual
records are in `alignment-differences`, `-under-hit`, `-unmatched` and
`-undecided.tsv`, and the problems in `alignment-problems.tsv`.

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
with `-eva-no-results`), `disabled-domain` (the states of the cvalue domain
were not saved, as with `-eva-no-results-domain cvalue`; Eva would answer
top everywhere) or `top-state`. The queries of a function whose state was
not saved are written over all callstacks only. The exit queries go through
the same check. The file starts with `format 2` and lists the reached
statements (`reach`), the exit of each function whose return statement is
reached included (`FUNCTION:exit`). It ends with `done COUNT`, where COUNT is
the number of answer, unavailable and error lines. A file is complete only
when every line is well formed and the done line is the last line, given
once, with that count; otherwise the comparison is incomplete and gives the
first reason found. The version of `format` and the count of `done` are
ASCII decimals of at most 18 digits: another digit, such as `²`, or a longer
number makes the line malformed. The same holds for the count of an AST
listing, the statuses of a measure and the numbers of a log.

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
`no-results`, `top-state`, `disabled-domain`, `error`, `missing`. A query
in one callstack of a function whose state was not saved takes the reason
of the same query over all callstacks. An exit query is `unreached` when its
exit is not listed as reached. A file without `format 2` lists no exit; its
module wrote the exit queries of a function only when its results were
saved and its exit reached. An exit query that such a file does not answer
is `no-callstack` when the file has the same query over all callstacks, and
`missing` otherwise. It says
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
  the producer, and the counters of supplied entries, with the rejections
  and refusals of supplied entries by reason, per run;
- `functions.tsv`: memexec activity and collector verdicts per function;
- `times.tsv`: elapsed time per mode and the ratios cache/nocache and
  cache/reference when both runs completed;
- `alignment.tsv`, `queries.tsv`, `alarms.tsv`: the comparison summaries,
  with `both_completed` for each pair, and for each comparison the number of
  pairs, of pairs compared, and of pairs whose two runs completed;
  `queries.tsv` has a column per side for each reason of an unanswered
  query;
- `tables.md`: all of the above but `functions.tsv`, as Markdown, followed
  by the checks of `fixtures.txt` and `outcome-demo.txt` when the output
  directory holds them, as the pilot's does.

A cell `-` is a value that was not measured, such as a memexec counter in
the mode `nocache`. A list of counts by reason is `none` when the family is
measured and no count is positive.

## Pilot

```sh
campaign/pilot.sh OUTPUT TEST_CHECKOUT REFERENCE_CHECKOUT [SWITCH]
```

runs the cases of `pilot-cases.txt` in the modes `nocache`, `cache`,
`cache.2` and `reference`, with a limit of `PILOT_TIMEOUT` seconds (180 by
default) and an address-space limit of `PILOT_MEMORY_LIMIT` bytes (8 GB by
default). It then runs the fixtures and the outcome demonstration, whose
checks go to `fixtures.txt` and `outcome-demo.txt`, and writes the tables
again, which adds these checks to `tables/tables.md`. It exits with 1 when
a check fails.

The fixtures (`fixtures/run-fixtures.sh`) run Frama-C directly on six
programs, outside the manifest. Each run lists its AST from a parse alone,
run as the runner runs the parse step, and from the session saved by Eva;
the two listings must have the same digest, and the comparisons take the
first, with the digests of the preprocessing of that parse, as the evidence
of numbering:

- `nested-hit.c`: the second call to `outer` is analysed with caching off
  and a hit with memexec; the two calls to `leaf` inside it must be reported
  as nested under the hit, and two runs with memexec must have the numbering
  `same` and align completely. Two runs with the unused macro `UNUSED` set
  to 0 and to 1 must have equal AST digests, the numbering `preprocessing
  differs`, and their calls must be undecided;
- `frame.c`: the program of the example run of issue #3. Before `r = 0;` in
  `get`, `r` is `{3}` in both runs under the callstack of the first call,
  `{5}` with caching off and no answer with memexec under the callstack of
  the second call, and over all callstacks `{3; 5}` with caching off against
  `{3}` with memexec, which must be reported as narrower. At the exit of
  `get`, `r` is `{0}`. A run with `-eva-no-results` and one with
  `-eva-no-results-domain cvalue` must answer no query, write each one, the
  exit queries included, as unavailable for that reason (`no-results`,
  `disabled-domain`), and end with a done line that counts these lines;
- `same-line.c`: two calls to `f` on one line, one on each branch of an `if`
  whose condition is a global. Analysed as it is, the analysis reaches
  `f(2)` only; with `-lib-entry`, `f(1)` too. The two runs parse the same
  program and must have the numbering `same`; the calls `f(2)` must align,
  and `f(1)` must be unmatched, not aligned with `f(2)`;
- `sites.c`: the same calls, with the macro `SIDE` as the condition itself;
  the runs with `SIDE` 0 and 1 give one call site and statement number to
  different calls. Their digests must differ, the calls must be undecided,
  not aligned, and the alignment must not be complete;
- `branches.c`: `if (SIDE) f(1); else f(1);` on one line, with `SIDE` 0 and
  1. The statement lines of the two listings must have the same numbers,
  lines and texts, and differ in their columns only; the digests must differ
  and the calls must not be aligned;
- `header.c`: `SIDE` sets the initial value of a global of the included
  `header.h`. The statement lines must be the same and the global lines
  differ in that global; the digests must differ and the calls must not be
  aligned.

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

The archive writes the paths under the home directory from `~`, in any
of its spellings, keeping the separator that follows (`HOME/file` becomes
`~/file`), and leaves out the compiled query modules; the same output gives
the same archive. The
files whose SHA-256 the provenance records (the manifest and the patches)
are archived as they were hashed: the script checks them against their
digests and stops when one of them holds the home directory. The protocol attaches this archive to the tag
of the campaign on GitHub, which is made when the branch is published. To
check a copy of the archive, run `sha256sum -c raw-logs.sha256` in its
directory.

`campaign.py recompute OUTPUT --recorded-set-a reference/set-a-recorded.tsv`
derives again, from the raw logs of an output directory or of its archive,
the records of each run, the outcome of each measured run, the comparisons
of each pair and the tables, with the tools of the current revision. Runs
recorded before the runner listed the AST have no `ast_sha256`. Their
digests can be listed again by re-running only the parsing step of each
run, which runs no analysis:

```sh
campaign/tools/export-ast.sh OUTPUT ROLE CHECKOUT [SWITCH] > DIGESTS
campaign.py recompute OUTPUT --ast-digests DIGESTS --recorded-set-a ...
```

`export-ast.sh` checks that the binary has the SHA-256 recorded for the
role, and prints the format of each listing. The digests so imported are
marked `ast_source imported` in `run.tsv`. The preprocessing of an archived
run is not listed again: the parse that `export-ast.sh` runs is not the one
of the run. Two imported runs without preprocessing digests are compared by
the preprocessing that their commands record instead: the revision and patch
of the binary and the `Command:` lines of `parse.log`, with the directory of
the source snapshot written `${SRC}`; for a fixture, which has no parse log,
the SHA-256 of the copy of the fixture kept in the run and the options
`-cpp*` of its extra options. Equal AST digests and equal recorded
preprocessing give the numbering `recorded command`: the calls are paired,
the preprocessed text was not compared, and the alignment is not complete.
Equal AST digests with different or missing recorded preprocessing give `not
established`. An imported run is never compared by its commands with a run
that has preprocessing digests.

`recompute` checks every row of the file of digests before it updates any
run. A row is valid when it has every column (`case`, `mode`, `ast_format`,
`ast_sha256`, `ast_statements`, `parse_exit`), the listing format 2, a
SHA-256 of 64 hexadecimal digits, a statement count that is a decimal, the
parse exit 0, ends with a newline, and is the only row of its run. A run
with an invalid row gets the digest `-`, so its numbering is `not
established`, and the reason in `ast_import_problem`; the reason is also
printed on the standard error. A run that recorded its digest itself keeps
it, whatever the file holds. Running `recompute` again with the same file
gives the same result.

When `export-ast.sh` cannot be run (the binary is gone), a pair of runs of
which one or both have no digest, and whose case, analyzer revision and
patch, case-study revision and extra options are equal, has the numbering
`asserted`: the same program parsed alike is expected to be numbered alike,
but no digest checks it. Such a pair is otherwise `not established`.

To replay a campaign, build the binaries at the revisions of
`provenance/binaries.tsv` with `tools/build-reference.sh`, check out this
repository at the revision of `provenance/campaign-revision.txt`, and run the
command of `provenance/command.txt`. Timings depend on the machine and its
load, which `provenance/machine.txt` records.
