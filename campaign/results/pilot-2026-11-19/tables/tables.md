# Result tables

Produced by `campaign.py tables` from `campaign-pilot-2026-11-19`. A cell `-` means that the source of its column does not give the value; it is never a zero. Each table names its source.

## Outcomes, time and memory per invocation

From the `run.tsv` of each run. `watchdog` is the last signal sent at the wall-time limit (`none` when it did not fire); `oom_evidence` the evidence that memory was exhausted.

| case | mode | outcome | exit | signal | watchdog | oom_evidence | elapsed_s | user_s | maxrss_kib | limit_s |
|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | completed | 0 | - | none | - | 0.70 | 0.65 | 205748 | 180 |
| 2048/2048.eva/default | cache.2 | completed | 0 | - | none | - | 0.70 | 0.65 | 205080 | 180 |
| 2048/2048.eva/default | nocache | completed | 0 | - | none | - | 1.95 | 1.87 | 241132 | 180 |
| 2048/2048.eva/default | reference | completed | 0 | - | none | - | 0.70 | 0.66 | 206360 | 180 |
| fixtures/frame.c/default | cache | completed | 0 | - | - | - | - | - | - | - |
| fixtures/frame.c/default | cache.2 | completed | 0 | - | - | - | - | - | - | - |
| fixtures/frame.c/default | nocache | completed | 0 | - | - | - | - | - | - | - |
| fixtures/frame.c/default | noresults | completed | 0 | - | - | - | - | - | - | - |
| fixtures/nested-hit.c/default | cache | completed | 0 | - | - | - | - | - | - | - |
| fixtures/nested-hit.c/default | cache.2 | completed | 0 | - | - | - | - | - | - | - |
| fixtures/nested-hit.c/default | nocache | completed | 0 | - | - | - | - | - | - | - |
| fixtures/same-line.c/default | side0 | completed | 0 | - | - | - | - | - | - | - |
| fixtures/same-line.c/default | side1 | completed | 0 | - | - | - | - | - | - | - |
| genann/genann.eva/default | cache | completed | 0 | - | none | - | 2.39 | 2.29 | 308328 | 180 |
| genann/genann.eva/default | cache.2 | completed | 0 | - | none | - | 2.37 | 2.25 | 308232 | 180 |
| genann/genann.eva/default | nocache | completed | 0 | - | none | - | 3.47 | 3.37 | 323980 | 180 |
| genann/genann.eva/default | reference | completed | 0 | - | none | - | 2.39 | 2.28 | 308804 | 180 |
| jsmn/jsmn-example.eva/default | cache | completed | 0 | - | none | - | 0.52 | 0.47 | 198084 | 180 |
| jsmn/jsmn-example.eva/default | cache.2 | completed | 0 | - | none | - | 0.52 | 0.47 | 197816 | 180 |
| jsmn/jsmn-example.eva/default | nocache | completed | 0 | - | none | - | 0.52 | 0.48 | 196580 | 180 |
| jsmn/jsmn-example.eva/default | reference | completed | 0 | - | none | - | 0.52 | 0.46 | 199164 | 180 |
| jsmn/jsmn-main.eva/default | cache | completed | 0 | - | none | - | 3.67 | 3.56 | 387276 | 180 |
| jsmn/jsmn-main.eva/default | cache.2 | completed | 0 | - | none | - | 3.63 | 3.52 | 387300 | 180 |
| jsmn/jsmn-main.eva/default | nocache | completed | 0 | - | none | - | 3.79 | 3.69 | 368680 | 180 |
| jsmn/jsmn-main.eva/default | reference | completed | 0 | - | none | - | 3.65 | 3.55 | 388044 | 180 |
| kgflags/kgflags-simple.eva/default | cache | completed | 0 | - | none | - | 0.56 | 0.50 | 203236 | 180 |
| kgflags/kgflags-simple.eva/default | cache.2 | completed | 0 | - | none | - | 0.58 | 0.52 | 202888 | 180 |
| kgflags/kgflags-simple.eva/default | nocache | completed | 0 | - | none | - | 0.56 | 0.52 | 201860 | 180 |
| kgflags/kgflags-simple.eva/default | reference | completed | 0 | - | none | - | 0.56 | 0.50 | 203660 | 180 |
| khash/khash.eva/default | cache | completed | 0 | - | none | - | 0.30 | 0.26 | 177896 | 180 |
| khash/khash.eva/default | cache.2 | completed | 0 | - | none | - | 0.32 | 0.27 | 177736 | 180 |
| khash/khash.eva/default | nocache | completed | 0 | - | none | - | 0.30 | 0.26 | 176712 | 180 |
| khash/khash.eva/default | reference | completed | 0 | - | none | - | 0.32 | 0.27 | 178856 | 180 |
| libyaml/test-version.eva/default | cache | completed | 0 | - | none | - | 1.95 | 1.82 | 366916 | 180 |
| libyaml/test-version.eva/default | cache.2 | completed | 0 | - | none | - | 1.95 | 1.84 | 367272 | 180 |
| libyaml/test-version.eva/default | nocache | completed | 0 | - | none | - | 1.95 | 1.83 | 365860 | 180 |
| libyaml/test-version.eva/default | reference | completed | 0 | - | none | - | 1.95 | 1.83 | 368248 | 180 |
| solitaire/solitaire.eva/default | cache | completed | 0 | - | none | - | 1.83 | 1.75 | 240340 | 180 |
| solitaire/solitaire.eva/default | cache.2 | completed | 0 | - | none | - | 2.35 | 2.26 | 239808 | 180 |
| solitaire/solitaire.eva/default | nocache | completed | 0 | - | none | - | 29.10 | 28.83 | 450456 | 180 |
| solitaire/solitaire.eva/default | reference | completed | 0 | - | none | - | 1.83 | 1.75 | 241544 | 180 |

## Counters of the statistics file: cache activity and set A

Source: the rows of `eva-stats.csv`, which holds the export of the last analysis of the invocation that ended. A number is the sum of the rows of its counter. `-` means that the file has no row of that counter, or is not a complete export (`export_rows`, the number of its rows, is then `-` too). The analyzer writes a row for a counter only once it has incremented it: a cell is 0 only when a row holds 0, and no value is taken from the options of the run, from its log or from another row. `hits`, `misses`, `stored` and `refused` are the `memexec-*` rows. `allocation_and_release` sums the rows of the allocation and release builtins, and `allocation_and_release_rows` counts them: its 0 means that there is no such row among the `export_rows` rows of this file. `in_set_a` is `False` when that sum is positive, `True` when rows give the sum 0, and `-` without such a row. `recorded_in_set_a` is the membership recorded by the earlier measurement; `agrees` compares the two when `in_set_a` is not `-`.

| case | mode | export_rows | hits | misses | stored | refused | refused_by_reason | allocation_and_release_rows | allocation_and_release | in_set_a | recorded_in_set_a | agrees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | 117 | 104 | 73 | 73 | - | - | 0 | - | - | True | - |
| 2048/2048.eva/default | cache.2 | 117 | 104 | 73 | 73 | - | - | 0 | - | - | True | - |
| 2048/2048.eva/default | nocache | 77 | - | - | - | - | - | 0 | - | - | True | - |
| 2048/2048.eva/default | reference | 117 | 104 | 73 | 73 | - | - | 0 | - | - | True | - |
| fixtures/frame.c/default | cache | 15 | 1 | 2 | 2 | - | - | 0 | - | - | - | - |
| fixtures/frame.c/default | cache.2 | 15 | 1 | 2 | 2 | - | - | 0 | - | - | - | - |
| fixtures/frame.c/default | nocache | 12 | - | - | - | - | - | 0 | - | - | - | - |
| fixtures/frame.c/default | noresults | 12 | - | - | - | - | - | 0 | - | - | - | - |
| fixtures/nested-hit.c/default | cache | 19 | 1 | 4 | 4 | - | - | 0 | - | - | - | - |
| fixtures/nested-hit.c/default | cache.2 | 19 | 1 | 4 | 4 | - | - | 0 | - | - | - | - |
| fixtures/nested-hit.c/default | nocache | 12 | - | - | - | - | - | 0 | - | - | - | - |
| fixtures/same-line.c/default | side0 | 14 | - | 2 | 2 | - | - | 0 | - | - | - | - |
| fixtures/same-line.c/default | side1 | 14 | - | 2 | 2 | - | - | 0 | - | - | - | - |
| genann/genann.eva/default | cache | 164 | 170 | 583 | 561 | 22 | not-cacheable=22 | 2 | 23 | False | False | yes |
| genann/genann.eva/default | cache.2 | 164 | 170 | 583 | 561 | 22 | not-cacheable=22 | 2 | 23 | False | False | yes |
| genann/genann.eva/default | nocache | 106 | - | - | - | - | - | 2 | 35 | False | False | yes |
| genann/genann.eva/default | reference | 164 | 170 | 583 | 561 | 22 | not-cacheable=22 | 2 | 23 | False | False | yes |
| jsmn/jsmn-example.eva/default | cache | 52 | - | 86 | 86 | - | - | 0 | - | - | True | - |
| jsmn/jsmn-example.eva/default | cache.2 | 52 | - | 86 | 86 | - | - | 0 | - | - | True | - |
| jsmn/jsmn-example.eva/default | nocache | 36 | - | - | - | - | - | 0 | - | - | True | - |
| jsmn/jsmn-example.eva/default | reference | 52 | - | 86 | 86 | - | - | 0 | - | - | True | - |
| jsmn/jsmn-main.eva/default | cache | 145 | 73 | 734 | 682 | 52 | not-cacheable=52 | 2 | 70 | False | False | yes |
| jsmn/jsmn-main.eva/default | cache.2 | 145 | 73 | 734 | 682 | 52 | not-cacheable=52 | 2 | 70 | False | False | yes |
| jsmn/jsmn-main.eva/default | nocache | 86 | - | - | - | - | - | 2 | 70 | False | False | yes |
| jsmn/jsmn-main.eva/default | reference | 145 | 73 | 734 | 682 | 52 | not-cacheable=52 | 2 | 70 | False | False | yes |
| kgflags/kgflags-simple.eva/default | cache | 85 | 10 | 99 | 99 | - | - | 0 | - | - | True | - |
| kgflags/kgflags-simple.eva/default | cache.2 | 85 | 10 | 99 | 99 | - | - | 0 | - | - | True | - |
| kgflags/kgflags-simple.eva/default | nocache | 53 | - | - | - | - | - | 0 | - | - | True | - |
| kgflags/kgflags-simple.eva/default | reference | 85 | 10 | 99 | 99 | - | - | 0 | - | - | True | - |
| khash/khash.eva/default | cache | 46 | - | 8 | 4 | 4 | not-cacheable=4 | 4 | 9 | False | False | yes |
| khash/khash.eva/default | cache.2 | 46 | - | 8 | 4 | 4 | not-cacheable=4 | 4 | 9 | False | False | yes |
| khash/khash.eva/default | nocache | 32 | - | - | - | - | - | 4 | 9 | False | False | yes |
| khash/khash.eva/default | reference | 46 | - | 8 | 4 | 4 | not-cacheable=4 | 4 | 9 | False | False | yes |
| libyaml/test-version.eva/default | cache | 18 | - | 3 | 3 | - | - | 0 | - | - | True | - |
| libyaml/test-version.eva/default | cache.2 | 18 | - | 3 | 3 | - | - | 0 | - | - | True | - |
| libyaml/test-version.eva/default | nocache | 12 | - | - | - | - | - | 0 | - | - | True | - |
| libyaml/test-version.eva/default | reference | 18 | - | 3 | 3 | - | - | 0 | - | - | True | - |
| solitaire/solitaire.eva/default | cache | 80 | 264 | 22 | 22 | - | - | 0 | - | - | True | - |
| solitaire/solitaire.eva/default | cache.2 | 80 | 264 | 22 | 22 | - | - | 0 | - | - | True | - |
| solitaire/solitaire.eva/default | nocache | 65 | - | - | - | - | - | 0 | - | - | True | - |
| solitaire/solitaire.eva/default | reference | 80 | 264 | 22 | 22 | - | - | 0 | - | - | True | - |

## Counters of the statistics file: collector, producer and supplied entries

Same source and same reading as the previous table: the rows `collector-*` (verdicts of the body access collector), `cache-produced` and `cache-production-refused-*` (the producer), and `cache-hits`, `cache-rejected-*` and `cache-refused-*` (entries supplied by a test module).

| case | mode | collector_would_store | collector_refused | collector_refused_by_reason | producer_stored | producer_refused | producer_refused_by_reason | supplied_hits | supplied_rejected | supplied_refused | supplied_rejected_by_reason | supplied_refused_by_reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | - | - | - | - | - |
| 2048/2048.eva/default | cache.2 | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | - | - | - | - | - |
| 2048/2048.eva/default | nocache | 38 | 378 | builtin=6,contract=133,side-table=185,sweep=54 | 38 | 378 | builtin=6,contract=133,side-table=185,sweep=54 | - | - | - | - | - |
| 2048/2048.eva/default | reference | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | - | - | - | - | - |
| fixtures/frame.c/default | cache | 1 | 1 | sweep=1 | 1 | 1 | sweep=1 | - | - | - | - | - |
| fixtures/frame.c/default | cache.2 | 1 | 1 | sweep=1 | 1 | 1 | sweep=1 | - | - | - | - | - |
| fixtures/frame.c/default | nocache | 1 | 2 | side-table=1,sweep=1 | 1 | 2 | side-table=1,sweep=1 | - | - | - | - | - |
| fixtures/frame.c/default | noresults | 1 | 2 | side-table=1,sweep=1 | 1 | 2 | side-table=1,sweep=1 | - | - | - | - | - |
| fixtures/nested-hit.c/default | cache | 2 | 2 | sweep=2 | 2 | 2 | sweep=2 | - | - | - | - | - |
| fixtures/nested-hit.c/default | cache.2 | 2 | 2 | sweep=2 | 2 | 2 | sweep=2 | - | - | - | - | - |
| fixtures/nested-hit.c/default | nocache | 4 | 3 | sweep=3 | 4 | 3 | sweep=3 | - | - | - | - | - |
| fixtures/same-line.c/default | side0 | 1 | 1 | sweep=1 | 1 | 1 | sweep=1 | - | - | - | - | - |
| fixtures/same-line.c/default | side1 | 1 | 1 | sweep=1 | 1 | 1 | sweep=1 | - | - | - | - | - |
| genann/genann.eva/default | cache | - | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | - | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | - | - | - | - | - |
| genann/genann.eva/default | cache.2 | - | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | - | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | - | - | - | - | - |
| genann/genann.eva/default | nocache | - | 1123 | builtin=404,contract=36,indirect-call=564,sweep=119 | - | 1123 | builtin=404,contract=36,indirect-call=564,sweep=119 | - | - | - | - | - |
| genann/genann.eva/default | reference | - | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | - | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | - | - | - | - | - |
| jsmn/jsmn-example.eva/default | cache | 37 | 49 | builtin=37,sweep=12 | 37 | 49 | builtin=37,sweep=12 | - | - | - | - | - |
| jsmn/jsmn-example.eva/default | cache.2 | 37 | 49 | builtin=37,sweep=12 | 37 | 49 | builtin=37,sweep=12 | - | - | - | - | - |
| jsmn/jsmn-example.eva/default | nocache | 37 | 49 | builtin=37,sweep=12 | 37 | 49 | builtin=37,sweep=12 | - | - | - | - | - |
| jsmn/jsmn-example.eva/default | reference | 37 | 49 | builtin=37,sweep=12 | 37 | 49 | builtin=37,sweep=12 | - | - | - | - | - |
| jsmn/jsmn-main.eva/default | cache | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | - | - | - | - | - |
| jsmn/jsmn-main.eva/default | cache.2 | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | - | - | - | - | - |
| jsmn/jsmn-main.eva/default | nocache | 268 | 568 | allocated-block=184,builtin=66,indirect-call=30,sweep=288 | 268 | 568 | allocated-block=184,builtin=66,indirect-call=30,sweep=288 | - | - | - | - | - |
| jsmn/jsmn-main.eva/default | reference | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | - | - | - | - | - |
| kgflags/kgflags-simple.eva/default | cache | 53 | 46 | builtin=10,sweep=36 | 53 | 46 | builtin=10,sweep=36 | - | - | - | - | - |
| kgflags/kgflags-simple.eva/default | cache.2 | 53 | 46 | builtin=10,sweep=36 | 53 | 46 | builtin=10,sweep=36 | - | - | - | - | - |
| kgflags/kgflags-simple.eva/default | nocache | 54 | 55 | builtin=19,sweep=36 | 54 | 55 | builtin=19,sweep=36 | - | - | - | - | - |
| kgflags/kgflags-simple.eva/default | reference | 53 | 46 | builtin=10,sweep=36 | 53 | 46 | builtin=10,sweep=36 | - | - | - | - | - |
| khash/khash.eva/default | cache | - | 8 | allocated-block=1,builtin=3,sweep=4 | - | 8 | allocated-block=1,builtin=3,sweep=4 | - | - | - | - | - |
| khash/khash.eva/default | cache.2 | - | 8 | allocated-block=1,builtin=3,sweep=4 | - | 8 | allocated-block=1,builtin=3,sweep=4 | - | - | - | - | - |
| khash/khash.eva/default | nocache | - | 8 | allocated-block=1,builtin=3,sweep=4 | - | 8 | allocated-block=1,builtin=3,sweep=4 | - | - | - | - | - |
| khash/khash.eva/default | reference | - | 8 | allocated-block=1,builtin=3,sweep=4 | - | 8 | allocated-block=1,builtin=3,sweep=4 | - | - | - | - | - |
| libyaml/test-version.eva/default | cache | 2 | 1 | sweep=1 | 2 | 1 | sweep=1 | - | - | - | - | - |
| libyaml/test-version.eva/default | cache.2 | 2 | 1 | sweep=1 | 2 | 1 | sweep=1 | - | - | - | - | - |
| libyaml/test-version.eva/default | nocache | 2 | 1 | sweep=1 | 2 | 1 | sweep=1 | - | - | - | - | - |
| libyaml/test-version.eva/default | reference | 2 | 1 | sweep=1 | 2 | 1 | sweep=1 | - | - | - | - | - |
| solitaire/solitaire.eva/default | cache | - | 22 | contract=14,sweep=8 | - | 22 | contract=14,sweep=8 | - | - | - | - | - |
| solitaire/solitaire.eva/default | cache.2 | - | 22 | contract=14,sweep=8 | - | 22 | contract=14,sweep=8 | - | - | - | - | - |
| solitaire/solitaire.eva/default | nocache | - | 796 | contract=533,sweep=263 | - | 796 | contract=533,sweep=263 | - | - | - | - | - |
| solitaire/solitaire.eva/default | reference | - | 22 | contract=14,sweep=8 | - | 22 | contract=14,sweep=8 | - | - | - | - | - |

The `memexec-*` and `collector-*` rows of each function are in `functions.tsv`, read in the same way: `-` where the function has no row of the counter.

## Dispositions counted in the Eva log (log-derived)

Source: the `[eva:cache]` messages of `eva.log`, one disposition line per call, counted by the words of their fields. These are counts of lines of the log, not counters of the statistics file: the two sources are never added, and neither stands for the other. `analysis_starts` counts the lines `[eva] Analyzing ... application starting at ...`. A count of 0, or `none` in a list by reason, means that there is no such line among the `disposition_lines` disposition lines of this log. The counts by kind are `-` unless the log has exactly one analysis start, at least one disposition line, and no cache message of a form the tool does not know; `log_note` then says why. The columns of the collector and of the producer are `-` when no disposition line has that field: the analyzer prints the producer field only under the message category `cache-producer`, and the kinds of a field that the log does not print are not compared. `lookup_rejected` counts the rejected candidates, the other columns count lines. `sources` compares each kind that has a counter with the rows of the statistics file: `agree on N kind(s)` when N kinds have the same number in both, `disagree:` followed by each kind whose two numbers differ or that the log shows and no row counts.

| case | mode | analysis_starts | disposition_lines | lookup_hit | lookup_no_candidate | lookup_rejected | lookup_rejected_by_reason | storage_stored | storage_none | storage_refused | storage_refused_by_reason | collector_would_store | collector_refused | collector_refused_by_reason | producer_stored | producer_refused | producer_refused_by_reason | log_note | sources |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | 1 | 177 | 104 | 73 | 0 | none | 73 | 104 | 0 | none | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | - | - | - | - | agree on 7 kinds |
| 2048/2048.eva/default | cache.2 | 1 | 177 | 104 | 73 | 0 | none | 73 | 104 | 0 | none | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | - | - | - | - | agree on 7 kinds |
| 2048/2048.eva/default | nocache | 1 | 416 | 0 | 416 | 0 | none | 0 | 0 | 416 | disabled=416 | 38 | 378 | builtin=6,contract=133,side-table=185,sweep=54 | - | - | - | - | agree on 5 kinds |
| 2048/2048.eva/default | reference | 1 | 177 | 104 | 73 | 0 | none | 73 | 104 | 0 | none | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | - | - | - | - | agree on 7 kinds |
| fixtures/frame.c/default | cache | 1 | 3 | 1 | 2 | 0 | none | 2 | 1 | 0 | none | 1 | 1 | sweep=1 | - | - | - | - | agree on 4 kinds |
| fixtures/frame.c/default | cache.2 | 1 | 3 | 1 | 2 | 0 | none | 2 | 1 | 0 | none | 1 | 1 | sweep=1 | - | - | - | - | agree on 4 kinds |
| fixtures/frame.c/default | nocache | 1 | 3 | 0 | 3 | 0 | none | 0 | 0 | 3 | disabled=3 | 1 | 2 | side-table=1,sweep=1 | - | - | - | - | agree on 3 kinds |
| fixtures/frame.c/default | noresults | 1 | 3 | 0 | 3 | 0 | none | 0 | 0 | 3 | disabled=3 | 1 | 2 | side-table=1,sweep=1 | - | - | - | - | agree on 3 kinds |
| fixtures/nested-hit.c/default | cache | 1 | 5 | 1 | 4 | 0 | none | 4 | 1 | 0 | none | 2 | 2 | sweep=2 | - | - | - | - | agree on 4 kinds |
| fixtures/nested-hit.c/default | cache.2 | 1 | 5 | 1 | 4 | 0 | none | 4 | 1 | 0 | none | 2 | 2 | sweep=2 | - | - | - | - | agree on 4 kinds |
| fixtures/nested-hit.c/default | nocache | 1 | 7 | 0 | 7 | 0 | none | 0 | 0 | 7 | disabled=7 | 4 | 3 | sweep=3 | - | - | - | - | agree on 2 kinds |
| fixtures/same-line.c/default | side0 | 1 | 2 | 0 | 2 | 0 | none | 2 | 0 | 0 | none | 1 | 1 | sweep=1 | - | - | - | - | agree on 3 kinds |
| fixtures/same-line.c/default | side1 | 1 | 2 | 0 | 2 | 0 | none | 2 | 0 | 0 | none | 1 | 1 | sweep=1 | - | - | - | - | agree on 3 kinds |
| genann/genann.eva/default | cache | 1 | 753 | 170 | 583 | 0 | none | 561 | 170 | 22 | not-cacheable=22 | 0 | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | - | - | - | - | agree on 7 kinds |
| genann/genann.eva/default | cache.2 | 1 | 753 | 170 | 583 | 0 | none | 561 | 170 | 22 | not-cacheable=22 | 0 | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | - | - | - | - | agree on 7 kinds |
| genann/genann.eva/default | nocache | 1 | 1123 | 0 | 1123 | 0 | none | 0 | 0 | 1123 | disabled=1123 | 0 | 1123 | builtin=404,contract=36,indirect-call=564,sweep=119 | - | - | - | - | agree on 4 kinds |
| genann/genann.eva/default | reference | 1 | 753 | 170 | 583 | 0 | none | 561 | 170 | 22 | not-cacheable=22 | 0 | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | - | - | - | - | agree on 7 kinds |
| jsmn/jsmn-example.eva/default | cache | 1 | 86 | 0 | 86 | 0 | none | 86 | 0 | 0 | none | 37 | 49 | builtin=37,sweep=12 | - | - | - | - | agree on 4 kinds |
| jsmn/jsmn-example.eva/default | cache.2 | 1 | 86 | 0 | 86 | 0 | none | 86 | 0 | 0 | none | 37 | 49 | builtin=37,sweep=12 | - | - | - | - | agree on 4 kinds |
| jsmn/jsmn-example.eva/default | nocache | 1 | 86 | 0 | 86 | 0 | none | 0 | 0 | 86 | disabled=86 | 37 | 49 | builtin=37,sweep=12 | - | - | - | - | agree on 3 kinds |
| jsmn/jsmn-example.eva/default | reference | 1 | 86 | 0 | 86 | 0 | none | 86 | 0 | 0 | none | 37 | 49 | builtin=37,sweep=12 | - | - | - | - | agree on 4 kinds |
| jsmn/jsmn-main.eva/default | cache | 1 | 807 | 73 | 734 | 0 | none | 682 | 73 | 52 | not-cacheable=52 | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | - | - | - | - | agree on 8 kinds |
| jsmn/jsmn-main.eva/default | cache.2 | 1 | 807 | 73 | 734 | 0 | none | 682 | 73 | 52 | not-cacheable=52 | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | - | - | - | - | agree on 8 kinds |
| jsmn/jsmn-main.eva/default | nocache | 1 | 836 | 0 | 836 | 0 | none | 0 | 0 | 836 | disabled=836 | 268 | 568 | allocated-block=184,builtin=66,indirect-call=30,sweep=288 | - | - | - | - | agree on 5 kinds |
| jsmn/jsmn-main.eva/default | reference | 1 | 807 | 73 | 734 | 0 | none | 682 | 73 | 52 | not-cacheable=52 | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | - | - | - | - | agree on 8 kinds |
| kgflags/kgflags-simple.eva/default | cache | 1 | 109 | 10 | 99 | 0 | none | 99 | 10 | 0 | none | 53 | 46 | builtin=10,sweep=36 | - | - | - | - | agree on 5 kinds |
| kgflags/kgflags-simple.eva/default | cache.2 | 1 | 109 | 10 | 99 | 0 | none | 99 | 10 | 0 | none | 53 | 46 | builtin=10,sweep=36 | - | - | - | - | agree on 5 kinds |
| kgflags/kgflags-simple.eva/default | nocache | 1 | 109 | 0 | 109 | 0 | none | 0 | 0 | 109 | disabled=109 | 54 | 55 | builtin=19,sweep=36 | - | - | - | - | agree on 3 kinds |
| kgflags/kgflags-simple.eva/default | reference | 1 | 109 | 10 | 99 | 0 | none | 99 | 10 | 0 | none | 53 | 46 | builtin=10,sweep=36 | - | - | - | - | agree on 5 kinds |
| khash/khash.eva/default | cache | 1 | 8 | 0 | 8 | 0 | none | 4 | 0 | 4 | not-cacheable=4 | 0 | 8 | allocated-block=1,builtin=3,sweep=4 | - | - | - | - | agree on 5 kinds |
| khash/khash.eva/default | cache.2 | 1 | 8 | 0 | 8 | 0 | none | 4 | 0 | 4 | not-cacheable=4 | 0 | 8 | allocated-block=1,builtin=3,sweep=4 | - | - | - | - | agree on 5 kinds |
| khash/khash.eva/default | nocache | 1 | 8 | 0 | 8 | 0 | none | 0 | 0 | 8 | disabled=8 | 0 | 8 | allocated-block=1,builtin=3,sweep=4 | - | - | - | - | agree on 3 kinds |
| khash/khash.eva/default | reference | 1 | 8 | 0 | 8 | 0 | none | 4 | 0 | 4 | not-cacheable=4 | 0 | 8 | allocated-block=1,builtin=3,sweep=4 | - | - | - | - | agree on 5 kinds |
| libyaml/test-version.eva/default | cache | 1 | 3 | 0 | 3 | 0 | none | 3 | 0 | 0 | none | 2 | 1 | sweep=1 | - | - | - | - | agree on 3 kinds |
| libyaml/test-version.eva/default | cache.2 | 1 | 3 | 0 | 3 | 0 | none | 3 | 0 | 0 | none | 2 | 1 | sweep=1 | - | - | - | - | agree on 3 kinds |
| libyaml/test-version.eva/default | nocache | 1 | 3 | 0 | 3 | 0 | none | 0 | 0 | 3 | disabled=3 | 2 | 1 | sweep=1 | - | - | - | - | agree on 2 kinds |
| libyaml/test-version.eva/default | reference | 1 | 3 | 0 | 3 | 0 | none | 3 | 0 | 0 | none | 2 | 1 | sweep=1 | - | - | - | - | agree on 3 kinds |
| solitaire/solitaire.eva/default | cache | 1 | 286 | 264 | 22 | 0 | none | 22 | 264 | 0 | none | 0 | 22 | contract=14,sweep=8 | - | - | - | - | agree on 4 kinds |
| solitaire/solitaire.eva/default | cache.2 | 1 | 286 | 264 | 22 | 0 | none | 22 | 264 | 0 | none | 0 | 22 | contract=14,sweep=8 | - | - | - | - | agree on 4 kinds |
| solitaire/solitaire.eva/default | nocache | 1 | 796 | 0 | 796 | 0 | none | 0 | 0 | 796 | disabled=796 | 0 | 796 | contract=533,sweep=263 | - | - | - | - | agree on 2 kinds |
| solitaire/solitaire.eva/default | reference | 1 | 286 | 264 | 22 | 0 | none | 22 | 264 | 0 | none | 0 | 22 | contract=14,sweep=8 | - | - | - | - | agree on 4 kinds |

## Elapsed time per mode

From the `run.tsv` of the first run of each mode: its elapsed time, or its outcome when it did not complete. `no run` means that the directory has no run of the mode, `no outcome` and `no time` that the run records none. A ratio is given only when both runs completed and have a time.

| case | nocache_s | cache_s | reference_s | cache_over_nocache | cache_over_reference |
|---|---|---|---|---|---|
| 2048/2048.eva/default | 1.95 | 0.70 | 0.70 | 0.359 | 1.000 |
| fixtures/frame.c/default | no time | no time | no run | n/a | n/a |
| fixtures/nested-hit.c/default | no time | no time | no run | n/a | n/a |
| genann/genann.eva/default | 3.47 | 2.39 | 2.39 | 0.689 | 1.000 |
| jsmn/jsmn-example.eva/default | 0.52 | 0.52 | 0.52 | 1.000 | 1.000 |
| jsmn/jsmn-main.eva/default | 3.79 | 3.67 | 3.65 | 0.968 | 1.005 |
| kgflags/kgflags-simple.eva/default | 0.56 | 0.56 | 0.56 | 1.000 | 1.000 |
| khash/khash.eva/default | 0.30 | 0.30 | 0.32 | 1.000 | 0.938 |
| libyaml/test-version.eva/default | 1.95 | 1.95 | 1.95 | 1.000 | 1.000 |
| solitaire/solitaire.eva/default | 29.10 | 1.83 | 1.83 | 0.063 | 1.000 |

## Alignment of the per-call records

Run A is the baseline, run B the candidate. Pairs: 38, with a valid summary: 38, of which both runs completed: 38. A pair without a valid summary has `-` in every column of the comparison; `both_completed` is `-` when the outcome of a run is not recorded.

| case | A | B | both_completed | records_a | records_b | inferred_a | inferred_b | aligned | aligned_other_dispositions | hit_a_analysed_b | analysed_a_hit_b | nested_under_hit_a | nested_under_hit_b | unmatched_a | unmatched_b | undecided_groups | problems_a | problems_b | numbering | accounted | complete | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | cache.2 | True | 177 | 177 | 0 | 0 | 177 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | AST digests equal, preprocessing compared by the recorded command only |
| 2048/2048.eva/default | nocache | cache | True | 416 | 177 | 0 | 0 | 177 | 177 | 0 | 104 | 0 | 239 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | incomplete: not every record aligned, preprocessing compared by the recorded command only |
| 2048/2048.eva/default | nocache | reference | True | 416 | 177 | 0 | 0 | 177 | 177 | 0 | 104 | 0 | 239 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | incomplete: not every record aligned, numbering asserted, not checked by digest |
| 2048/2048.eva/default | reference | cache | True | 177 | 177 | 0 | 0 | 177 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal recorded revisions, patch and extra options, not checked by digest |
| fixtures/frame.c/default | cache | cache.2 | True | 3 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | incomplete: entry point not given, preprocessing compared by the recorded command only |
| fixtures/frame.c/default | nocache | cache | True | 3 | 3 | 0 | 0 | 3 | 3 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | incomplete: entry point not given, preprocessing compared by the recorded command only |
| fixtures/frame.c/default | nocache | noresults | True | 3 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | incomplete: entry point not given, preprocessing compared by the recorded command only |
| fixtures/nested-hit.c/default | cache | cache.2 | True | 5 | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | incomplete: entry point not given, preprocessing compared by the recorded command only |
| fixtures/nested-hit.c/default | nocache | cache | True | 7 | 5 | 0 | 0 | 5 | 5 | 0 | 1 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | incomplete: entry point not given, not every record aligned, preprocessing compared by the recorded command only |
| fixtures/same-line.c/default | side0 | side1 | True | 2 | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | different | True | False | incomplete: entry point not given, AST digests differ, not every record aligned |
| genann/genann.eva/default | cache | cache.2 | True | 753 | 753 | 0 | 0 | 753 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | AST digests equal, preprocessing compared by the recorded command only |
| genann/genann.eva/default | nocache | cache | True | 1123 | 753 | 0 | 0 | 753 | 753 | 0 | 170 | 0 | 370 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | incomplete: not every record aligned, preprocessing compared by the recorded command only |
| genann/genann.eva/default | nocache | reference | True | 1123 | 753 | 0 | 0 | 753 | 753 | 0 | 170 | 0 | 370 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | incomplete: not every record aligned, numbering asserted, not checked by digest |
| genann/genann.eva/default | reference | cache | True | 753 | 753 | 0 | 0 | 753 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal recorded revisions, patch and extra options, not checked by digest |
| jsmn/jsmn-example.eva/default | cache | cache.2 | True | 86 | 86 | 0 | 0 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | AST digests equal, preprocessing compared by the recorded command only |
| jsmn/jsmn-example.eva/default | nocache | cache | True | 86 | 86 | 0 | 0 | 86 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | AST digests equal, preprocessing compared by the recorded command only |
| jsmn/jsmn-example.eva/default | nocache | reference | True | 86 | 86 | 0 | 0 | 86 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal recorded revisions, patch and extra options, not checked by digest |
| jsmn/jsmn-example.eva/default | reference | cache | True | 86 | 86 | 0 | 0 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal recorded revisions, patch and extra options, not checked by digest |
| jsmn/jsmn-main.eva/default | cache | cache.2 | True | 807 | 807 | 0 | 0 | 807 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | AST digests equal, preprocessing compared by the recorded command only |
| jsmn/jsmn-main.eva/default | nocache | cache | True | 836 | 807 | 0 | 0 | 807 | 807 | 0 | 73 | 0 | 29 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | incomplete: not every record aligned, preprocessing compared by the recorded command only |
| jsmn/jsmn-main.eva/default | nocache | reference | True | 836 | 807 | 0 | 0 | 807 | 807 | 0 | 73 | 0 | 29 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | incomplete: not every record aligned, numbering asserted, not checked by digest |
| jsmn/jsmn-main.eva/default | reference | cache | True | 807 | 807 | 0 | 0 | 807 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal recorded revisions, patch and extra options, not checked by digest |
| kgflags/kgflags-simple.eva/default | cache | cache.2 | True | 109 | 109 | 0 | 0 | 109 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | AST digests equal, preprocessing compared by the recorded command only |
| kgflags/kgflags-simple.eva/default | nocache | cache | True | 109 | 109 | 0 | 0 | 109 | 109 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | AST digests equal, preprocessing compared by the recorded command only |
| kgflags/kgflags-simple.eva/default | nocache | reference | True | 109 | 109 | 0 | 0 | 109 | 109 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal recorded revisions, patch and extra options, not checked by digest |
| kgflags/kgflags-simple.eva/default | reference | cache | True | 109 | 109 | 0 | 0 | 109 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal recorded revisions, patch and extra options, not checked by digest |
| khash/khash.eva/default | cache | cache.2 | True | 8 | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | AST digests equal, preprocessing compared by the recorded command only |
| khash/khash.eva/default | nocache | cache | True | 8 | 8 | 0 | 0 | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | AST digests equal, preprocessing compared by the recorded command only |
| khash/khash.eva/default | nocache | reference | True | 8 | 8 | 0 | 0 | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal recorded revisions, patch and extra options, not checked by digest |
| khash/khash.eva/default | reference | cache | True | 8 | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal recorded revisions, patch and extra options, not checked by digest |
| libyaml/test-version.eva/default | cache | cache.2 | True | 3 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | AST digests equal, preprocessing compared by the recorded command only |
| libyaml/test-version.eva/default | nocache | cache | True | 3 | 3 | 0 | 0 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | AST digests equal, preprocessing compared by the recorded command only |
| libyaml/test-version.eva/default | nocache | reference | True | 3 | 3 | 0 | 0 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal recorded revisions, patch and extra options, not checked by digest |
| libyaml/test-version.eva/default | reference | cache | True | 3 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal recorded revisions, patch and extra options, not checked by digest |
| solitaire/solitaire.eva/default | cache | cache.2 | True | 286 | 286 | 0 | 0 | 286 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | AST digests equal, preprocessing compared by the recorded command only |
| solitaire/solitaire.eva/default | nocache | cache | True | 796 | 286 | 0 | 0 | 286 | 286 | 0 | 264 | 0 | 510 | 0 | 0 | 0 | 0 | 0 | recorded command | True | False | incomplete: not every record aligned, preprocessing compared by the recorded command only |
| solitaire/solitaire.eva/default | nocache | reference | True | 796 | 286 | 0 | 0 | 286 | 286 | 0 | 264 | 0 | 510 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | incomplete: not every record aligned, numbering asserted, not checked by digest |
| solitaire/solitaire.eva/default | reference | cache | True | 286 | 286 | 0 | 0 | 286 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal recorded revisions, patch and extra options, not checked by digest |

## State queries

Run A is the baseline, run B the candidate. Pairs: 38, with a valid summary: 38, of which both runs completed: 38. A pair without a valid summary has `-` in every column of the comparison; `both_completed` is `-` when the outcome of a run is not recorded.

| case | A | B | both_completed | queries | numbering | unpaired | answered_both | equal | wider | narrower | incomparable | undecided | top_a | top_b | unavailable_a_unreached | unavailable_b_unreached | unavailable_a_no-callstack | unavailable_b_no-callstack | unavailable_a_no-results | unavailable_b_no-results | unavailable_a_top-state | unavailable_b_top-state | unavailable_a_disabled-domain | unavailable_b_disabled-domain | unavailable_a_error | unavailable_b_error | unavailable_a_missing | unavailable_b_missing | unavailable_a_other | unavailable_b_other | reached_a_only | reached_b_only | complete_a | complete_b | comparison |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | cache.2 | True | 2078 | recorded command | 0 | 2078 | 2078 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| 2048/2048.eva/default | nocache | cache | True | 4948 | recorded command | 0 | 2078 | 2053 | 0 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2870 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| 2048/2048.eva/default | nocache | reference | True | 4948 | asserted | 0 | 2078 | 2053 | 0 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2870 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| 2048/2048.eva/default | reference | cache | True | 2078 | asserted | 0 | 2078 | 2078 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| fixtures/frame.c/default | cache | cache.2 | True | 88 | recorded command | 0 | 88 | 88 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| fixtures/frame.c/default | nocache | cache | True | 108 | recorded command | 0 | 88 | 87 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| fixtures/frame.c/default | nocache | noresults | True | 108 | recorded command | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 78 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| fixtures/nested-hit.c/default | cache | cache.2 | True | 86 | recorded command | 0 | 86 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| fixtures/nested-hit.c/default | nocache | cache | True | 122 | recorded command | 0 | 86 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 36 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| fixtures/same-line.c/default | side0 | side1 | True | 34 | different | 28 | 6 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | complete | complete | incomplete: AST digests differ |
| genann/genann.eva/default | cache | cache.2 | True | 17178 | recorded command | 0 | 17178 | 17178 | 0 | 0 | 0 | 0 | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| genann/genann.eva/default | nocache | cache | True | 18387 | recorded command | 0 | 17178 | 17140 | 34 | 0 | 4 | 0 | 4 | 9 | 0 | 0 | 0 | 1209 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| genann/genann.eva/default | nocache | reference | True | 18387 | asserted | 0 | 17178 | 17140 | 34 | 0 | 4 | 0 | 4 | 9 | 0 | 0 | 0 | 1209 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| genann/genann.eva/default | reference | cache | True | 17178 | asserted | 0 | 17178 | 17178 | 0 | 0 | 0 | 0 | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| jsmn/jsmn-example.eva/default | cache | cache.2 | True | 1875 | recorded command | 0 | 1875 | 1875 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| jsmn/jsmn-example.eva/default | nocache | cache | True | 1875 | recorded command | 0 | 1875 | 1875 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| jsmn/jsmn-example.eva/default | nocache | reference | True | 1875 | asserted | 0 | 1875 | 1875 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| jsmn/jsmn-example.eva/default | reference | cache | True | 1875 | asserted | 0 | 1875 | 1875 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| jsmn/jsmn-main.eva/default | cache | cache.2 | True | 35235 | recorded command | 0 | 35235 | 35235 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| jsmn/jsmn-main.eva/default | nocache | cache | True | 35923 | recorded command | 0 | 35235 | 35229 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 688 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| jsmn/jsmn-main.eva/default | nocache | reference | True | 35923 | asserted | 0 | 35235 | 35229 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 688 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| jsmn/jsmn-main.eva/default | reference | cache | True | 35235 | asserted | 0 | 35235 | 35235 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| kgflags/kgflags-simple.eva/default | cache | cache.2 | True | 1466 | recorded command | 0 | 1466 | 1466 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| kgflags/kgflags-simple.eva/default | nocache | cache | True | 1504 | recorded command | 0 | 1466 | 1466 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 38 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| kgflags/kgflags-simple.eva/default | nocache | reference | True | 1504 | asserted | 0 | 1466 | 1466 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 38 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| kgflags/kgflags-simple.eva/default | reference | cache | True | 1466 | asserted | 0 | 1466 | 1466 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| khash/khash.eva/default | cache | cache.2 | True | 1034 | recorded command | 0 | 1034 | 1034 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| khash/khash.eva/default | nocache | cache | True | 1034 | recorded command | 0 | 1034 | 1034 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| khash/khash.eva/default | nocache | reference | True | 1034 | asserted | 0 | 1034 | 1034 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| khash/khash.eva/default | reference | cache | True | 1034 | asserted | 0 | 1034 | 1034 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| libyaml/test-version.eva/default | cache | cache.2 | True | 106 | recorded command | 0 | 106 | 106 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| libyaml/test-version.eva/default | nocache | cache | True | 106 | recorded command | 0 | 106 | 106 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| libyaml/test-version.eva/default | nocache | reference | True | 106 | asserted | 0 | 106 | 106 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| libyaml/test-version.eva/default | reference | cache | True | 106 | asserted | 0 | 106 | 106 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| solitaire/solitaire.eva/default | cache | cache.2 | True | 4451 | recorded command | 0 | 4451 | 4451 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| solitaire/solitaire.eva/default | nocache | cache | True | 6355 | recorded command | 0 | 4451 | 4451 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1904 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: preprocessing compared by the recorded command only |
| solitaire/solitaire.eva/default | nocache | reference | True | 6355 | asserted | 0 | 4451 | 4451 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1904 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |
| solitaire/solitaire.eva/default | reference | cache | True | 4451 | asserted | 0 | 4451 | 4451 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | incomplete: numbering asserted, not checked by digest |

## Alarms and property statuses

Run A is the baseline, run B the candidate. Pairs: 38, with a valid summary: 32, of which both runs completed: 32. A pair without a valid summary has `-` in every column of the comparison; `both_completed` is `-` when the outcome of a run is not recorded.

| case | A | B | both_completed | properties_a | properties_b | duplicate_keys_a | duplicate_keys_b | same_status | other_status | a_only | b_only |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | cache.2 | True | 17 | 17 | 0 | 0 | 17 | 0 | 0 | 0 |
| 2048/2048.eva/default | nocache | cache | True | 17 | 17 | 0 | 0 | 17 | 0 | 0 | 0 |
| 2048/2048.eva/default | nocache | reference | True | 17 | 17 | 0 | 0 | 17 | 0 | 0 | 0 |
| 2048/2048.eva/default | reference | cache | True | 17 | 17 | 0 | 0 | 17 | 0 | 0 | 0 |
| fixtures/frame.c/default | cache | cache.2 | True | - | - | - | - | - | - | - | - |
| fixtures/frame.c/default | nocache | cache | True | - | - | - | - | - | - | - | - |
| fixtures/frame.c/default | nocache | noresults | True | - | - | - | - | - | - | - | - |
| fixtures/nested-hit.c/default | cache | cache.2 | True | - | - | - | - | - | - | - | - |
| fixtures/nested-hit.c/default | nocache | cache | True | - | - | - | - | - | - | - | - |
| fixtures/same-line.c/default | side0 | side1 | True | - | - | - | - | - | - | - | - |
| genann/genann.eva/default | cache | cache.2 | True | 75 | 75 | 0 | 0 | 75 | 0 | 0 | 0 |
| genann/genann.eva/default | nocache | cache | True | 75 | 75 | 0 | 0 | 75 | 0 | 0 | 0 |
| genann/genann.eva/default | nocache | reference | True | 75 | 75 | 0 | 0 | 75 | 0 | 0 | 0 |
| genann/genann.eva/default | reference | cache | True | 75 | 75 | 0 | 0 | 75 | 0 | 0 | 0 |
| jsmn/jsmn-example.eva/default | cache | cache.2 | True | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| jsmn/jsmn-example.eva/default | nocache | cache | True | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| jsmn/jsmn-example.eva/default | nocache | reference | True | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| jsmn/jsmn-example.eva/default | reference | cache | True | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| jsmn/jsmn-main.eva/default | cache | cache.2 | True | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-main.eva/default | nocache | cache | True | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-main.eva/default | nocache | reference | True | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-main.eva/default | reference | cache | True | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| kgflags/kgflags-simple.eva/default | cache | cache.2 | True | 35 | 35 | 0 | 0 | 35 | 0 | 0 | 0 |
| kgflags/kgflags-simple.eva/default | nocache | cache | True | 35 | 35 | 0 | 0 | 35 | 0 | 0 | 0 |
| kgflags/kgflags-simple.eva/default | nocache | reference | True | 35 | 35 | 0 | 0 | 35 | 0 | 0 | 0 |
| kgflags/kgflags-simple.eva/default | reference | cache | True | 35 | 35 | 0 | 0 | 35 | 0 | 0 | 0 |
| khash/khash.eva/default | cache | cache.2 | True | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| khash/khash.eva/default | nocache | cache | True | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| khash/khash.eva/default | nocache | reference | True | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| khash/khash.eva/default | reference | cache | True | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| libyaml/test-version.eva/default | cache | cache.2 | True | 4 | 4 | 0 | 0 | 4 | 0 | 0 | 0 |
| libyaml/test-version.eva/default | nocache | cache | True | 4 | 4 | 0 | 0 | 4 | 0 | 0 | 0 |
| libyaml/test-version.eva/default | nocache | reference | True | 4 | 4 | 0 | 0 | 4 | 0 | 0 | 0 |
| libyaml/test-version.eva/default | reference | cache | True | 4 | 4 | 0 | 0 | 4 | 0 | 0 | 0 |
| solitaire/solitaire.eva/default | cache | cache.2 | True | 286 | 286 | 9 | 9 | 274 | 0 | 0 | 0 |
| solitaire/solitaire.eva/default | nocache | cache | True | 286 | 286 | 9 | 9 | 274 | 0 | 0 | 0 |
| solitaire/solitaire.eva/default | nocache | reference | True | 286 | 286 | 9 | 9 | 274 | 0 | 0 | 0 |
| solitaire/solitaire.eva/default | reference | cache | True | 286 | 286 | 9 | 9 | 274 | 0 | 0 | 0 |

## Checks on the constructed cases

Checks of `fixtures/run-fixtures.sh` as recorded when the campaign ran (harness revision `12644c58d8e915849602116a8a242384de5d7348`). `tables` copies these lines and does not check them again.

The alignment result of the recorded check is superseded. Current result: 0 of 38 alignments with a valid summary are complete. The alignment of the two memexec runs of `nested-hit.c` in this directory has numbering `recorded command`, `complete=False` and the verdict `incomplete: entry point not given, preprocessing compared by the recorded command only`.

```
PASS nested-hit: two runs of the same binary align completely
PASS nested-hit: one call analysed without caching is a hit with memexec
PASS nested-hit: the two nested calls are reported under the hit
PASS nested-hit: no alignment is undecided or unmatched
PASS nested-hit: every record is aligned or nested under the hit
PASS nested-hit: the nested records are the calls to leaf under the second call to outer
PASS frame: first call, raw answer {3} without caching
PASS frame: first call, raw answer {3} with memexec
PASS frame: second call, raw answer {5} without caching
PASS frame: second call, no raw answer with memexec
PASS frame: all callstacks, raw answer {3; 5} without caching
PASS frame: all callstacks, raw answer {3} with memexec
PASS frame: before r = 0, all callstacks, memexec answer {3} is narrower than {3; 5}
PASS frame: the callstack of the second call has no answer with memexec
PASS frame: the callstack of the first call answers {3} in both runs
PASS frame: at the exit of get, r is {0} without caching
PASS frame: with -eva-no-results, no query is answered
PASS frame: with -eva-no-results, the queries are unavailable for lack of results
PASS frame: with -eva-no-results, the done line counts the unavailable lines
PASS frame: the comparison with the run without results answers nothing in it
PASS same-line: the two calls of line 10 are unmatched, not aligned
PASS same-line: the alignment is not complete
```

## Outcome classes of the runner

Constructed runs of `tools/outcome-demo.sh`, caching disabled, as recorded when the campaign ran (harness revision `12644c58d8e915849602116a8a242384de5d7348`). `tables` copies these lines and does not check them again.

```
PASS	expected timeout	observed timeout	exit 143	signal 15	watchdog term	oom_evidence -	elapsed_s 1.02
PASS	expected oom	observed oom	exit 6	signal -	watchdog none	oom_evidence log	elapsed_s 1.49
PASS	expected error	observed error	exit 1	signal -	watchdog none	oom_evidence -	elapsed_s 0.32
PASS	expected killed	observed killed	exit 137	signal 9	watchdog none	oom_evidence -	elapsed_s 1.63
```
