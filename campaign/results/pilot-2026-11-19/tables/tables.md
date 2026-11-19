# Result tables

Produced by `campaign.py tables` from `campaign-pilot-2026-11-19`. A cell `-` is a value that was not measured.

## Outcomes, time and memory per invocation

`watchdog` is the last signal sent at the wall-time limit (`none` when it did not fire); `oom_evidence` the evidence that memory was exhausted.

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

## Cache activity and set A

Totals per case of the statistics file; memexec counts only in the modes that enable it. `allocation_and_release` sums the applications of the allocation and release builtins; a run is in set A when it is 0. `recorded_in_set_a` is the membership recorded by the earlier measurement.

| case | mode | hits | misses | stored | refused | refused_by_reason | allocation_and_release | in_set_a | recorded_in_set_a | agrees |
|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | 104 | 73 | 73 | 0 | none | 0 | True | True | yes |
| 2048/2048.eva/default | cache.2 | 104 | 73 | 73 | 0 | none | 0 | True | True | yes |
| 2048/2048.eva/default | nocache | - | - | - | - | - | 0 | True | True | yes |
| 2048/2048.eva/default | reference | 104 | 73 | 73 | 0 | none | 0 | True | True | yes |
| fixtures/frame.c/default | cache | 1 | 2 | 2 | 0 | none | 0 | True | - | - |
| fixtures/frame.c/default | cache.2 | 1 | 2 | 2 | 0 | none | 0 | True | - | - |
| fixtures/frame.c/default | nocache | - | - | - | - | - | 0 | True | - | - |
| fixtures/frame.c/default | noresults | - | - | - | - | - | 0 | True | - | - |
| fixtures/nested-hit.c/default | cache | 1 | 4 | 4 | 0 | none | 0 | True | - | - |
| fixtures/nested-hit.c/default | cache.2 | 1 | 4 | 4 | 0 | none | 0 | True | - | - |
| fixtures/nested-hit.c/default | nocache | - | - | - | - | - | 0 | True | - | - |
| fixtures/same-line.c/default | side0 | 0 | 2 | 2 | 0 | none | 0 | True | - | - |
| fixtures/same-line.c/default | side1 | 0 | 2 | 2 | 0 | none | 0 | True | - | - |
| genann/genann.eva/default | cache | 170 | 583 | 561 | 22 | not-cacheable=22 | 23 | False | False | yes |
| genann/genann.eva/default | cache.2 | 170 | 583 | 561 | 22 | not-cacheable=22 | 23 | False | False | yes |
| genann/genann.eva/default | nocache | - | - | - | - | - | 35 | False | False | yes |
| genann/genann.eva/default | reference | 170 | 583 | 561 | 22 | not-cacheable=22 | 23 | False | False | yes |
| jsmn/jsmn-example.eva/default | cache | 0 | 86 | 86 | 0 | none | 0 | True | True | yes |
| jsmn/jsmn-example.eva/default | cache.2 | 0 | 86 | 86 | 0 | none | 0 | True | True | yes |
| jsmn/jsmn-example.eva/default | nocache | - | - | - | - | - | 0 | True | True | yes |
| jsmn/jsmn-example.eva/default | reference | 0 | 86 | 86 | 0 | none | 0 | True | True | yes |
| jsmn/jsmn-main.eva/default | cache | 73 | 734 | 682 | 52 | not-cacheable=52 | 70 | False | False | yes |
| jsmn/jsmn-main.eva/default | cache.2 | 73 | 734 | 682 | 52 | not-cacheable=52 | 70 | False | False | yes |
| jsmn/jsmn-main.eva/default | nocache | - | - | - | - | - | 70 | False | False | yes |
| jsmn/jsmn-main.eva/default | reference | 73 | 734 | 682 | 52 | not-cacheable=52 | 70 | False | False | yes |
| kgflags/kgflags-simple.eva/default | cache | 10 | 99 | 99 | 0 | none | 0 | True | True | yes |
| kgflags/kgflags-simple.eva/default | cache.2 | 10 | 99 | 99 | 0 | none | 0 | True | True | yes |
| kgflags/kgflags-simple.eva/default | nocache | - | - | - | - | - | 0 | True | True | yes |
| kgflags/kgflags-simple.eva/default | reference | 10 | 99 | 99 | 0 | none | 0 | True | True | yes |
| khash/khash.eva/default | cache | 0 | 8 | 4 | 4 | not-cacheable=4 | 9 | False | False | yes |
| khash/khash.eva/default | cache.2 | 0 | 8 | 4 | 4 | not-cacheable=4 | 9 | False | False | yes |
| khash/khash.eva/default | nocache | - | - | - | - | - | 9 | False | False | yes |
| khash/khash.eva/default | reference | 0 | 8 | 4 | 4 | not-cacheable=4 | 9 | False | False | yes |
| libyaml/test-version.eva/default | cache | 0 | 3 | 3 | 0 | none | 0 | True | True | yes |
| libyaml/test-version.eva/default | cache.2 | 0 | 3 | 3 | 0 | none | 0 | True | True | yes |
| libyaml/test-version.eva/default | nocache | - | - | - | - | - | 0 | True | True | yes |
| libyaml/test-version.eva/default | reference | 0 | 3 | 3 | 0 | none | 0 | True | True | yes |
| solitaire/solitaire.eva/default | cache | 264 | 22 | 22 | 0 | none | 0 | True | True | yes |
| solitaire/solitaire.eva/default | cache.2 | 264 | 22 | 22 | 0 | none | 0 | True | True | yes |
| solitaire/solitaire.eva/default | nocache | - | - | - | - | - | 0 | True | True | yes |
| solitaire/solitaire.eva/default | reference | 264 | 22 | 22 | 0 | none | 0 | True | True | yes |

## Collector verdicts, produced and supplied entries

Verdicts of the body access collector on the bodies analysed to completion, the entries the producer stored from them or refused (no lookup reads them), and the counters of entries supplied by a test module, which no campaign run supplies.

| case | mode | collector_would_store | collector_refused | collector_refused_by_reason | producer_stored | producer_refused | producer_refused_by_reason | supplied_hits | supplied_rejected | supplied_refused | supplied_rejected_by_reason | supplied_refused_by_reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | 0 | 0 | 0 | none | none |
| 2048/2048.eva/default | cache.2 | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | 0 | 0 | 0 | none | none |
| 2048/2048.eva/default | nocache | 38 | 378 | builtin=6,contract=133,side-table=185,sweep=54 | 38 | 378 | builtin=6,contract=133,side-table=185,sweep=54 | 0 | 0 | 0 | none | none |
| 2048/2048.eva/default | reference | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | 6 | 67 | builtin=3,contract=8,side-table=36,sweep=20 | 0 | 0 | 0 | none | none |
| fixtures/frame.c/default | cache | 1 | 1 | sweep=1 | 1 | 1 | sweep=1 | 0 | 0 | 0 | none | none |
| fixtures/frame.c/default | cache.2 | 1 | 1 | sweep=1 | 1 | 1 | sweep=1 | 0 | 0 | 0 | none | none |
| fixtures/frame.c/default | nocache | 1 | 2 | side-table=1,sweep=1 | 1 | 2 | side-table=1,sweep=1 | 0 | 0 | 0 | none | none |
| fixtures/frame.c/default | noresults | 1 | 2 | side-table=1,sweep=1 | 1 | 2 | side-table=1,sweep=1 | 0 | 0 | 0 | none | none |
| fixtures/nested-hit.c/default | cache | 2 | 2 | sweep=2 | 2 | 2 | sweep=2 | 0 | 0 | 0 | none | none |
| fixtures/nested-hit.c/default | cache.2 | 2 | 2 | sweep=2 | 2 | 2 | sweep=2 | 0 | 0 | 0 | none | none |
| fixtures/nested-hit.c/default | nocache | 4 | 3 | sweep=3 | 4 | 3 | sweep=3 | 0 | 0 | 0 | none | none |
| fixtures/same-line.c/default | side0 | 1 | 1 | sweep=1 | 1 | 1 | sweep=1 | 0 | 0 | 0 | none | none |
| fixtures/same-line.c/default | side1 | 1 | 1 | sweep=1 | 1 | 1 | sweep=1 | 0 | 0 | 0 | none | none |
| genann/genann.eva/default | cache | 0 | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | 0 | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | 0 | 0 | 0 | none | none |
| genann/genann.eva/default | cache.2 | 0 | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | 0 | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | 0 | 0 | 0 | none | none |
| genann/genann.eva/default | nocache | 0 | 1123 | builtin=404,contract=36,indirect-call=564,sweep=119 | 0 | 1123 | builtin=404,contract=36,indirect-call=564,sweep=119 | 0 | 0 | 0 | none | none |
| genann/genann.eva/default | reference | 0 | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | 0 | 583 | builtin=266,contract=36,indirect-call=197,sweep=84 | 0 | 0 | 0 | none | none |
| jsmn/jsmn-example.eva/default | cache | 37 | 49 | builtin=37,sweep=12 | 37 | 49 | builtin=37,sweep=12 | 0 | 0 | 0 | none | none |
| jsmn/jsmn-example.eva/default | cache.2 | 37 | 49 | builtin=37,sweep=12 | 37 | 49 | builtin=37,sweep=12 | 0 | 0 | 0 | none | none |
| jsmn/jsmn-example.eva/default | nocache | 37 | 49 | builtin=37,sweep=12 | 37 | 49 | builtin=37,sweep=12 | 0 | 0 | 0 | none | none |
| jsmn/jsmn-example.eva/default | reference | 37 | 49 | builtin=37,sweep=12 | 37 | 49 | builtin=37,sweep=12 | 0 | 0 | 0 | none | none |
| jsmn/jsmn-main.eva/default | cache | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | 0 | 0 | 0 | none | none |
| jsmn/jsmn-main.eva/default | cache.2 | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | 0 | 0 | 0 | none | none |
| jsmn/jsmn-main.eva/default | nocache | 268 | 568 | allocated-block=184,builtin=66,indirect-call=30,sweep=288 | 268 | 568 | allocated-block=184,builtin=66,indirect-call=30,sweep=288 | 0 | 0 | 0 | none | none |
| jsmn/jsmn-main.eva/default | reference | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | 188 | 546 | allocated-block=184,builtin=61,indirect-call=30,sweep=271 | 0 | 0 | 0 | none | none |
| kgflags/kgflags-simple.eva/default | cache | 53 | 46 | builtin=10,sweep=36 | 53 | 46 | builtin=10,sweep=36 | 0 | 0 | 0 | none | none |
| kgflags/kgflags-simple.eva/default | cache.2 | 53 | 46 | builtin=10,sweep=36 | 53 | 46 | builtin=10,sweep=36 | 0 | 0 | 0 | none | none |
| kgflags/kgflags-simple.eva/default | nocache | 54 | 55 | builtin=19,sweep=36 | 54 | 55 | builtin=19,sweep=36 | 0 | 0 | 0 | none | none |
| kgflags/kgflags-simple.eva/default | reference | 53 | 46 | builtin=10,sweep=36 | 53 | 46 | builtin=10,sweep=36 | 0 | 0 | 0 | none | none |
| khash/khash.eva/default | cache | 0 | 8 | allocated-block=1,builtin=3,sweep=4 | 0 | 8 | allocated-block=1,builtin=3,sweep=4 | 0 | 0 | 0 | none | none |
| khash/khash.eva/default | cache.2 | 0 | 8 | allocated-block=1,builtin=3,sweep=4 | 0 | 8 | allocated-block=1,builtin=3,sweep=4 | 0 | 0 | 0 | none | none |
| khash/khash.eva/default | nocache | 0 | 8 | allocated-block=1,builtin=3,sweep=4 | 0 | 8 | allocated-block=1,builtin=3,sweep=4 | 0 | 0 | 0 | none | none |
| khash/khash.eva/default | reference | 0 | 8 | allocated-block=1,builtin=3,sweep=4 | 0 | 8 | allocated-block=1,builtin=3,sweep=4 | 0 | 0 | 0 | none | none |
| libyaml/test-version.eva/default | cache | 2 | 1 | sweep=1 | 2 | 1 | sweep=1 | 0 | 0 | 0 | none | none |
| libyaml/test-version.eva/default | cache.2 | 2 | 1 | sweep=1 | 2 | 1 | sweep=1 | 0 | 0 | 0 | none | none |
| libyaml/test-version.eva/default | nocache | 2 | 1 | sweep=1 | 2 | 1 | sweep=1 | 0 | 0 | 0 | none | none |
| libyaml/test-version.eva/default | reference | 2 | 1 | sweep=1 | 2 | 1 | sweep=1 | 0 | 0 | 0 | none | none |
| solitaire/solitaire.eva/default | cache | 0 | 22 | contract=14,sweep=8 | 0 | 22 | contract=14,sweep=8 | 0 | 0 | 0 | none | none |
| solitaire/solitaire.eva/default | cache.2 | 0 | 22 | contract=14,sweep=8 | 0 | 22 | contract=14,sweep=8 | 0 | 0 | 0 | none | none |
| solitaire/solitaire.eva/default | nocache | 0 | 796 | contract=533,sweep=263 | 0 | 796 | contract=533,sweep=263 | 0 | 0 | 0 | none | none |
| solitaire/solitaire.eva/default | reference | 0 | 22 | contract=14,sweep=8 | 0 | 22 | contract=14,sweep=8 | 0 | 0 | 0 | none | none |

The hits, misses, stores, refusals and collector verdicts per function are in `functions.tsv`.

## Elapsed time per mode

Elapsed time of the first run of each mode, or its outcome when it did not complete. A ratio is given only when both runs completed.

| case | nocache_s | cache_s | reference_s | cache_over_nocache | cache_over_reference |
|---|---|---|---|---|---|
| 2048/2048.eva/default | 1.95 | 0.70 | 0.70 | 0.359 | 1.000 |
| fixtures/frame.c/default | not measured | not measured | not run | n/a | n/a |
| fixtures/nested-hit.c/default | not measured | not measured | not run | n/a | n/a |
| genann/genann.eva/default | 3.47 | 2.39 | 2.39 | 0.689 | 1.000 |
| jsmn/jsmn-example.eva/default | 0.52 | 0.52 | 0.52 | 1.000 | 1.000 |
| jsmn/jsmn-main.eva/default | 3.79 | 3.67 | 3.65 | 0.968 | 1.005 |
| kgflags/kgflags-simple.eva/default | 0.56 | 0.56 | 0.56 | 1.000 | 1.000 |
| khash/khash.eva/default | 0.30 | 0.30 | 0.32 | 1.000 | 0.938 |
| libyaml/test-version.eva/default | 1.95 | 1.95 | 1.95 | 1.000 | 1.000 |
| solitaire/solitaire.eva/default | 29.10 | 1.83 | 1.83 | 0.063 | 1.000 |

## Alignment of the per-call records

Run A is the baseline, run B the candidate. Pairs: 38, compared: 38, with both runs completed: 38.

| case | A | B | both_completed | records_a | records_b | inferred_a | inferred_b | aligned | aligned_other_dispositions | hit_a_analysed_b | analysed_a_hit_b | nested_under_hit_a | nested_under_hit_b | unmatched_a | unmatched_b | undecided_groups | problems_a | problems_b | numbering | accounted | complete | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | cache.2 | True | 177 | 177 | 0 | 0 | 177 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| 2048/2048.eva/default | nocache | cache | True | 416 | 177 | 0 | 0 | 177 | 177 | 0 | 104 | 0 | 239 | 0 | 0 | 0 | 0 | 0 | same | True | False | incomplete: not every record aligned |
| 2048/2048.eva/default | nocache | reference | True | 416 | 177 | 0 | 0 | 177 | 177 | 0 | 104 | 0 | 239 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | incomplete: not every record aligned, numbering asserted, not checked by digest |
| 2048/2048.eva/default | reference | cache | True | 177 | 177 | 0 | 0 | 177 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal revision, patch, options and preprocessing, not checked by digest |
| fixtures/frame.c/default | cache | cache.2 | True | 3 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| fixtures/frame.c/default | nocache | cache | True | 3 | 3 | 0 | 0 | 3 | 3 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| fixtures/frame.c/default | nocache | noresults | True | 3 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| fixtures/nested-hit.c/default | cache | cache.2 | True | 5 | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| fixtures/nested-hit.c/default | nocache | cache | True | 7 | 5 | 0 | 0 | 5 | 5 | 0 | 1 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | same | True | False | incomplete: not every record aligned |
| fixtures/same-line.c/default | side0 | side1 | True | 2 | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | same | True | False | incomplete: not every record aligned |
| genann/genann.eva/default | cache | cache.2 | True | 753 | 753 | 0 | 0 | 753 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| genann/genann.eva/default | nocache | cache | True | 1123 | 753 | 0 | 0 | 753 | 753 | 0 | 170 | 0 | 370 | 0 | 0 | 0 | 0 | 0 | same | True | False | incomplete: not every record aligned |
| genann/genann.eva/default | nocache | reference | True | 1123 | 753 | 0 | 0 | 753 | 753 | 0 | 170 | 0 | 370 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | incomplete: not every record aligned, numbering asserted, not checked by digest |
| genann/genann.eva/default | reference | cache | True | 753 | 753 | 0 | 0 | 753 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal revision, patch, options and preprocessing, not checked by digest |
| jsmn/jsmn-example.eva/default | cache | cache.2 | True | 86 | 86 | 0 | 0 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| jsmn/jsmn-example.eva/default | nocache | cache | True | 86 | 86 | 0 | 0 | 86 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| jsmn/jsmn-example.eva/default | nocache | reference | True | 86 | 86 | 0 | 0 | 86 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal revision, patch, options and preprocessing, not checked by digest |
| jsmn/jsmn-example.eva/default | reference | cache | True | 86 | 86 | 0 | 0 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal revision, patch, options and preprocessing, not checked by digest |
| jsmn/jsmn-main.eva/default | cache | cache.2 | True | 807 | 807 | 0 | 0 | 807 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| jsmn/jsmn-main.eva/default | nocache | cache | True | 836 | 807 | 0 | 0 | 807 | 807 | 0 | 73 | 0 | 29 | 0 | 0 | 0 | 0 | 0 | same | True | False | incomplete: not every record aligned |
| jsmn/jsmn-main.eva/default | nocache | reference | True | 836 | 807 | 0 | 0 | 807 | 807 | 0 | 73 | 0 | 29 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | incomplete: not every record aligned, numbering asserted, not checked by digest |
| jsmn/jsmn-main.eva/default | reference | cache | True | 807 | 807 | 0 | 0 | 807 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal revision, patch, options and preprocessing, not checked by digest |
| kgflags/kgflags-simple.eva/default | cache | cache.2 | True | 109 | 109 | 0 | 0 | 109 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| kgflags/kgflags-simple.eva/default | nocache | cache | True | 109 | 109 | 0 | 0 | 109 | 109 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| kgflags/kgflags-simple.eva/default | nocache | reference | True | 109 | 109 | 0 | 0 | 109 | 109 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal revision, patch, options and preprocessing, not checked by digest |
| kgflags/kgflags-simple.eva/default | reference | cache | True | 109 | 109 | 0 | 0 | 109 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal revision, patch, options and preprocessing, not checked by digest |
| khash/khash.eva/default | cache | cache.2 | True | 8 | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| khash/khash.eva/default | nocache | cache | True | 8 | 8 | 0 | 0 | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| khash/khash.eva/default | nocache | reference | True | 8 | 8 | 0 | 0 | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal revision, patch, options and preprocessing, not checked by digest |
| khash/khash.eva/default | reference | cache | True | 8 | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal revision, patch, options and preprocessing, not checked by digest |
| libyaml/test-version.eva/default | cache | cache.2 | True | 3 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| libyaml/test-version.eva/default | nocache | cache | True | 3 | 3 | 0 | 0 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| libyaml/test-version.eva/default | nocache | reference | True | 3 | 3 | 0 | 0 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal revision, patch, options and preprocessing, not checked by digest |
| libyaml/test-version.eva/default | reference | cache | True | 3 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal revision, patch, options and preprocessing, not checked by digest |
| solitaire/solitaire.eva/default | cache | cache.2 | True | 286 | 286 | 0 | 0 | 286 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | same | True | True | complete |
| solitaire/solitaire.eva/default | nocache | cache | True | 796 | 286 | 0 | 0 | 286 | 286 | 0 | 264 | 0 | 510 | 0 | 0 | 0 | 0 | 0 | same | True | False | incomplete: not every record aligned |
| solitaire/solitaire.eva/default | nocache | reference | True | 796 | 286 | 0 | 0 | 286 | 286 | 0 | 264 | 0 | 510 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | incomplete: not every record aligned, numbering asserted, not checked by digest |
| solitaire/solitaire.eva/default | reference | cache | True | 286 | 286 | 0 | 0 | 286 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | asserted | True | False | numbering asserted from equal revision, patch, options and preprocessing, not checked by digest |

## State queries

Run A is the baseline, run B the candidate. Pairs: 38, compared: 38, with both runs completed: 38.

| case | A | B | both_completed | queries | answered_both | equal | wider | narrower | incomparable | undecided | top_a | top_b | unavailable_a_unreached | unavailable_b_unreached | unavailable_a_no-callstack | unavailable_b_no-callstack | unavailable_a_no-results | unavailable_b_no-results | unavailable_a_top-state | unavailable_b_top-state | unavailable_a_disabled-domain | unavailable_b_disabled-domain | unavailable_a_error | unavailable_b_error | unavailable_a_missing | unavailable_b_missing | unavailable_a_other | unavailable_b_other | reached_a_only | reached_b_only | complete_a | complete_b | comparison |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | cache.2 | True | 2078 | 2078 | 2078 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| 2048/2048.eva/default | nocache | cache | True | 4948 | 2078 | 2053 | 0 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2870 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| 2048/2048.eva/default | nocache | reference | True | 4948 | 2078 | 2053 | 0 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2870 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| 2048/2048.eva/default | reference | cache | True | 2078 | 2078 | 2078 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| fixtures/frame.c/default | cache | cache.2 | True | 88 | 88 | 88 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| fixtures/frame.c/default | nocache | cache | True | 108 | 88 | 87 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| fixtures/frame.c/default | nocache | noresults | True | 108 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 78 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 0 | 0 | 0 | complete | complete | complete |
| fixtures/nested-hit.c/default | cache | cache.2 | True | 86 | 86 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| fixtures/nested-hit.c/default | nocache | cache | True | 122 | 86 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 36 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| fixtures/same-line.c/default | side0 | side1 | True | 34 | 22 | 13 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | complete | complete | complete |
| genann/genann.eva/default | cache | cache.2 | True | 17178 | 17178 | 17178 | 0 | 0 | 0 | 0 | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| genann/genann.eva/default | nocache | cache | True | 18387 | 17178 | 17140 | 34 | 0 | 4 | 0 | 4 | 9 | 0 | 0 | 0 | 1209 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| genann/genann.eva/default | nocache | reference | True | 18387 | 17178 | 17140 | 34 | 0 | 4 | 0 | 4 | 9 | 0 | 0 | 0 | 1209 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| genann/genann.eva/default | reference | cache | True | 17178 | 17178 | 17178 | 0 | 0 | 0 | 0 | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| jsmn/jsmn-example.eva/default | cache | cache.2 | True | 1875 | 1875 | 1875 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| jsmn/jsmn-example.eva/default | nocache | cache | True | 1875 | 1875 | 1875 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| jsmn/jsmn-example.eva/default | nocache | reference | True | 1875 | 1875 | 1875 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| jsmn/jsmn-example.eva/default | reference | cache | True | 1875 | 1875 | 1875 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| jsmn/jsmn-main.eva/default | cache | cache.2 | True | 35235 | 35235 | 35235 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| jsmn/jsmn-main.eva/default | nocache | cache | True | 35923 | 35235 | 35229 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 688 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| jsmn/jsmn-main.eva/default | nocache | reference | True | 35923 | 35235 | 35229 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 688 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| jsmn/jsmn-main.eva/default | reference | cache | True | 35235 | 35235 | 35235 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| kgflags/kgflags-simple.eva/default | cache | cache.2 | True | 1466 | 1466 | 1466 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| kgflags/kgflags-simple.eva/default | nocache | cache | True | 1504 | 1466 | 1466 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 38 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| kgflags/kgflags-simple.eva/default | nocache | reference | True | 1504 | 1466 | 1466 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 38 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| kgflags/kgflags-simple.eva/default | reference | cache | True | 1466 | 1466 | 1466 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| khash/khash.eva/default | cache | cache.2 | True | 1034 | 1034 | 1034 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| khash/khash.eva/default | nocache | cache | True | 1034 | 1034 | 1034 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| khash/khash.eva/default | nocache | reference | True | 1034 | 1034 | 1034 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| khash/khash.eva/default | reference | cache | True | 1034 | 1034 | 1034 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| libyaml/test-version.eva/default | cache | cache.2 | True | 106 | 106 | 106 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| libyaml/test-version.eva/default | nocache | cache | True | 106 | 106 | 106 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| libyaml/test-version.eva/default | nocache | reference | True | 106 | 106 | 106 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| libyaml/test-version.eva/default | reference | cache | True | 106 | 106 | 106 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| solitaire/solitaire.eva/default | cache | cache.2 | True | 4451 | 4451 | 4451 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| solitaire/solitaire.eva/default | nocache | cache | True | 6355 | 4451 | 4451 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1904 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| solitaire/solitaire.eva/default | nocache | reference | True | 6355 | 4451 | 4451 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1904 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |
| solitaire/solitaire.eva/default | reference | cache | True | 4451 | 4451 | 4451 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | complete | complete | complete |

## Alarms and property statuses

Run A is the baseline, run B the candidate. Pairs: 38, compared: 32, with both runs completed: 32.

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

Constructed runs of tools/outcome-demo.sh, caching disabled.

```
PASS	expected timeout	observed timeout	exit 143	signal 15	watchdog term	oom_evidence -	elapsed_s 1.02
PASS	expected oom	observed oom	exit 6	signal -	watchdog none	oom_evidence log	elapsed_s 1.49
PASS	expected error	observed error	exit 1	signal -	watchdog none	oom_evidence -	elapsed_s 0.32
PASS	expected killed	observed killed	exit 137	signal 9	watchdog none	oom_evidence -	elapsed_s 1.63
```
