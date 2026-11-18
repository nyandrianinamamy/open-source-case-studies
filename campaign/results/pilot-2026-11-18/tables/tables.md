# Result tables

Produced by `campaign.py tables` from `campaign-pilot-2026-11-18`.

## Outcomes, time and memory per invocation

| case | mode | outcome | exit | elapsed_s | user_s | maxrss_kib | limit_s |
|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | completed | 0 | 0.64 | 0.60 | 201692 | 180 |
| 2048/2048.eva/default | cache.2 | completed | 0 | 0.70 | 0.65 | 201144 | 180 |
| 2048/2048.eva/default | nocache | completed | 0 | 1.70 | 1.65 | 234348 | 180 |
| 2048/2048.eva/default | reference | completed | 0 | 0.64 | 0.59 | 202416 | 180 |
| fixtures/frame.c/default | cache | completed | 0 | - | - | - | - |
| fixtures/frame.c/default | cache.2 | completed | 0 | - | - | - | - |
| fixtures/frame.c/default | nocache | completed | 0 | - | - | - | - |
| fixtures/nested-hit.c/default | cache | completed | 0 | - | - | - | - |
| fixtures/nested-hit.c/default | cache.2 | completed | 0 | - | - | - | - |
| fixtures/nested-hit.c/default | nocache | completed | 0 | - | - | - | - |
| genann/genann.eva/default | cache | completed | 0 | 2.17 | 2.09 | 303720 | 180 |
| genann/genann.eva/default | cache.2 | completed | 0 | 2.19 | 2.10 | 303968 | 180 |
| genann/genann.eva/default | nocache | completed | 0 | 3.06 | 2.97 | 313344 | 180 |
| genann/genann.eva/default | reference | completed | 0 | 2.16 | 2.08 | 305164 | 180 |
| jsmn/jsmn-example.eva/default | cache | completed | 0 | 0.51 | 0.47 | 194312 | 180 |
| jsmn/jsmn-example.eva/default | cache.2 | completed | 0 | 0.50 | 0.45 | 194476 | 180 |
| jsmn/jsmn-example.eva/default | nocache | completed | 0 | 0.48 | 0.44 | 192904 | 180 |
| jsmn/jsmn-example.eva/default | reference | completed | 0 | 0.50 | 0.45 | 195492 | 180 |
| jsmn/jsmn-main.eva/default | cache | completed | 0 | 3.31 | 3.22 | 373964 | 180 |
| jsmn/jsmn-main.eva/default | cache.2 | completed | 0 | 3.33 | 3.23 | 374036 | 180 |
| jsmn/jsmn-main.eva/default | nocache | completed | 0 | 3.49 | 3.39 | 375244 | 180 |
| jsmn/jsmn-main.eva/default | reference | completed | 0 | 3.35 | 3.26 | 374292 | 180 |
| kgflags/kgflags-simple.eva/default | cache | completed | 0 | 0.53 | 0.48 | 200804 | 180 |
| kgflags/kgflags-simple.eva/default | cache.2 | completed | 0 | 0.54 | 0.50 | 200740 | 180 |
| kgflags/kgflags-simple.eva/default | nocache | completed | 0 | 0.54 | 0.50 | 199880 | 180 |
| kgflags/kgflags-simple.eva/default | reference | completed | 0 | 0.53 | 0.49 | 201420 | 180 |
| khash/khash.eva/default | cache | completed | 0 | 0.30 | 0.25 | 177788 | 180 |
| khash/khash.eva/default | cache.2 | completed | 0 | 0.29 | 0.26 | 177440 | 180 |
| khash/khash.eva/default | nocache | completed | 0 | 0.30 | 0.26 | 174136 | 180 |
| khash/khash.eva/default | reference | completed | 0 | 0.30 | 0.26 | 178368 | 180 |
| libyaml/test-version.eva/default | cache | completed | 0 | 1.91 | 1.81 | 365068 | 180 |
| libyaml/test-version.eva/default | cache.2 | completed | 0 | 1.92 | 1.82 | 365368 | 180 |
| libyaml/test-version.eva/default | nocache | completed | 0 | 2.14 | 2.01 | 361240 | 180 |
| libyaml/test-version.eva/default | reference | completed | 0 | 1.96 | 1.87 | 365916 | 180 |
| solitaire/solitaire.eva/default | cache | completed | 0 | 1.68 | 1.62 | 237056 | 180 |
| solitaire/solitaire.eva/default | cache.2 | completed | 0 | 1.69 | 1.63 | 237152 | 180 |
| solitaire/solitaire.eva/default | nocache | completed | 0 | 24.38 | 24.15 | 452424 | 180 |
| solitaire/solitaire.eva/default | reference | completed | 0 | 1.69 | 1.62 | 238096 | 180 |

## Cache activity and set A

Totals per case of the statistics file. `allocation_and_release` sums the applications of the allocation and release builtins; a run is in set A when it is 0. `recorded_in_set_a` is the membership recorded by the earlier measurement.

| case | mode | hits | misses | stored | refused | refused_by_reason | allocation_and_release | in_set_a | recorded_in_set_a | agrees |
|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | 104 | 73 | 73 | 0 | - | 0 | True | True | yes |
| 2048/2048.eva/default | cache.2 | 104 | 73 | 73 | 0 | - | 0 | True | True | yes |
| 2048/2048.eva/default | nocache | 0 | 0 | 0 | 0 | - | 0 | True | True | yes |
| 2048/2048.eva/default | reference | 104 | 73 | 73 | 0 | - | 0 | True | True | yes |
| fixtures/frame.c/default | cache | 1 | 2 | 2 | 0 | - | 0 | True | n/a | n/a |
| fixtures/frame.c/default | cache.2 | 1 | 2 | 2 | 0 | - | 0 | True | n/a | n/a |
| fixtures/frame.c/default | nocache | 0 | 0 | 0 | 0 | - | 0 | True | n/a | n/a |
| fixtures/nested-hit.c/default | cache | 1 | 4 | 4 | 0 | - | 0 | True | n/a | n/a |
| fixtures/nested-hit.c/default | cache.2 | 1 | 4 | 4 | 0 | - | 0 | True | n/a | n/a |
| fixtures/nested-hit.c/default | nocache | 0 | 0 | 0 | 0 | - | 0 | True | n/a | n/a |
| genann/genann.eva/default | cache | 170 | 583 | 561 | 22 | not-cacheable=22 | 23 | False | False | yes |
| genann/genann.eva/default | cache.2 | 170 | 583 | 561 | 22 | not-cacheable=22 | 23 | False | False | yes |
| genann/genann.eva/default | nocache | 0 | 0 | 0 | 0 | - | 35 | False | False | yes |
| genann/genann.eva/default | reference | 170 | 583 | 561 | 22 | not-cacheable=22 | 23 | False | False | yes |
| jsmn/jsmn-example.eva/default | cache | 0 | 86 | 86 | 0 | - | 0 | True | True | yes |
| jsmn/jsmn-example.eva/default | cache.2 | 0 | 86 | 86 | 0 | - | 0 | True | True | yes |
| jsmn/jsmn-example.eva/default | nocache | 0 | 0 | 0 | 0 | - | 0 | True | True | yes |
| jsmn/jsmn-example.eva/default | reference | 0 | 86 | 86 | 0 | - | 0 | True | True | yes |
| jsmn/jsmn-main.eva/default | cache | 73 | 734 | 682 | 52 | not-cacheable=52 | 70 | False | False | yes |
| jsmn/jsmn-main.eva/default | cache.2 | 73 | 734 | 682 | 52 | not-cacheable=52 | 70 | False | False | yes |
| jsmn/jsmn-main.eva/default | nocache | 0 | 0 | 0 | 0 | - | 70 | False | False | yes |
| jsmn/jsmn-main.eva/default | reference | 73 | 734 | 682 | 52 | not-cacheable=52 | 70 | False | False | yes |
| kgflags/kgflags-simple.eva/default | cache | 10 | 99 | 99 | 0 | - | 0 | True | True | yes |
| kgflags/kgflags-simple.eva/default | cache.2 | 10 | 99 | 99 | 0 | - | 0 | True | True | yes |
| kgflags/kgflags-simple.eva/default | nocache | 0 | 0 | 0 | 0 | - | 0 | True | True | yes |
| kgflags/kgflags-simple.eva/default | reference | 10 | 99 | 99 | 0 | - | 0 | True | True | yes |
| khash/khash.eva/default | cache | 0 | 8 | 4 | 4 | not-cacheable=4 | 9 | False | False | yes |
| khash/khash.eva/default | cache.2 | 0 | 8 | 4 | 4 | not-cacheable=4 | 9 | False | False | yes |
| khash/khash.eva/default | nocache | 0 | 0 | 0 | 0 | - | 9 | False | False | yes |
| khash/khash.eva/default | reference | 0 | 8 | 4 | 4 | not-cacheable=4 | 9 | False | False | yes |
| libyaml/test-version.eva/default | cache | 0 | 3 | 3 | 0 | - | 0 | True | True | yes |
| libyaml/test-version.eva/default | cache.2 | 0 | 3 | 3 | 0 | - | 0 | True | True | yes |
| libyaml/test-version.eva/default | nocache | 0 | 0 | 0 | 0 | - | 0 | True | True | yes |
| libyaml/test-version.eva/default | reference | 0 | 3 | 3 | 0 | - | 0 | True | True | yes |
| solitaire/solitaire.eva/default | cache | 264 | 22 | 22 | 0 | - | 0 | True | True | yes |
| solitaire/solitaire.eva/default | cache.2 | 264 | 22 | 22 | 0 | - | 0 | True | True | yes |
| solitaire/solitaire.eva/default | nocache | 0 | 0 | 0 | 0 | - | 0 | True | True | yes |
| solitaire/solitaire.eva/default | reference | 264 | 22 | 22 | 0 | - | 0 | True | True | yes |

The hits, misses, stores and refusals per function are in `functions.tsv`.

## Elapsed time per mode

Elapsed time of the first run of each mode, or its outcome when it did not complete. A ratio is given only when both runs completed.

| case | nocache_s | cache_s | reference_s | cache_over_nocache | cache_over_reference |
|---|---|---|---|---|---|
| 2048/2048.eva/default | 1.70 | 0.64 | 0.64 | 0.376 | 1.000 |
| fixtures/frame.c/default | not measured | not measured | not run | n/a | n/a |
| fixtures/nested-hit.c/default | not measured | not measured | not run | n/a | n/a |
| genann/genann.eva/default | 3.06 | 2.17 | 2.16 | 0.709 | 1.005 |
| jsmn/jsmn-example.eva/default | 0.48 | 0.51 | 0.50 | 1.062 | 1.020 |
| jsmn/jsmn-main.eva/default | 3.49 | 3.31 | 3.35 | 0.948 | 0.988 |
| kgflags/kgflags-simple.eva/default | 0.54 | 0.53 | 0.53 | 0.981 | 1.000 |
| khash/khash.eva/default | 0.30 | 0.30 | 0.30 | 1.000 | 1.000 |
| libyaml/test-version.eva/default | 2.14 | 1.91 | 1.96 | 0.893 | 0.974 |
| solitaire/solitaire.eva/default | 24.38 | 1.68 | 1.69 | 0.069 | 0.994 |

## Alignment of the per-call records

Run A is the baseline, run B the candidate.

| case | A | B | records_a | records_b | aligned | aligned_other_dispositions | hit_a_analysed_b | analysed_a_hit_b | nested_under_hit_a | nested_under_hit_b | unmatched_a | unmatched_b | undecided_groups | accounted | complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | cache.2 | 177 | 177 | 177 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| 2048/2048.eva/default | nocache | cache | 416 | 177 | 177 | 177 | 0 | 104 | 0 | 239 | 0 | 0 | 0 | True | False |
| 2048/2048.eva/default | nocache | reference | 416 | 177 | 177 | 177 | 0 | 104 | 0 | 239 | 0 | 0 | 0 | True | False |
| 2048/2048.eva/default | reference | cache | 177 | 177 | 177 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| fixtures/frame.c/default | cache | cache.2 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| fixtures/frame.c/default | nocache | cache | 3 | 3 | 3 | 3 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | True | True |
| fixtures/nested-hit.c/default | cache | cache.2 | 5 | 5 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| fixtures/nested-hit.c/default | nocache | cache | 7 | 5 | 5 | 5 | 0 | 1 | 0 | 2 | 0 | 0 | 0 | True | False |
| genann/genann.eva/default | cache | cache.2 | 753 | 753 | 753 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| genann/genann.eva/default | nocache | cache | 1123 | 753 | 753 | 753 | 0 | 170 | 0 | 370 | 0 | 0 | 0 | True | False |
| genann/genann.eva/default | nocache | reference | 1123 | 753 | 753 | 753 | 0 | 170 | 0 | 370 | 0 | 0 | 0 | True | False |
| genann/genann.eva/default | reference | cache | 753 | 753 | 753 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| jsmn/jsmn-example.eva/default | cache | cache.2 | 86 | 86 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| jsmn/jsmn-example.eva/default | nocache | cache | 86 | 86 | 86 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| jsmn/jsmn-example.eva/default | nocache | reference | 86 | 86 | 86 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| jsmn/jsmn-example.eva/default | reference | cache | 86 | 86 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| jsmn/jsmn-main.eva/default | cache | cache.2 | 807 | 807 | 807 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| jsmn/jsmn-main.eva/default | nocache | cache | 836 | 807 | 807 | 807 | 0 | 73 | 0 | 29 | 0 | 0 | 0 | True | False |
| jsmn/jsmn-main.eva/default | nocache | reference | 836 | 807 | 807 | 807 | 0 | 73 | 0 | 29 | 0 | 0 | 0 | True | False |
| jsmn/jsmn-main.eva/default | reference | cache | 807 | 807 | 807 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| kgflags/kgflags-simple.eva/default | cache | cache.2 | 109 | 109 | 109 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| kgflags/kgflags-simple.eva/default | nocache | cache | 109 | 109 | 109 | 109 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | True | True |
| kgflags/kgflags-simple.eva/default | nocache | reference | 109 | 109 | 109 | 109 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | True | True |
| kgflags/kgflags-simple.eva/default | reference | cache | 109 | 109 | 109 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| khash/khash.eva/default | cache | cache.2 | 8 | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| khash/khash.eva/default | nocache | cache | 8 | 8 | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| khash/khash.eva/default | nocache | reference | 8 | 8 | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| khash/khash.eva/default | reference | cache | 8 | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| libyaml/test-version.eva/default | cache | cache.2 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| libyaml/test-version.eva/default | nocache | cache | 3 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| libyaml/test-version.eva/default | nocache | reference | 3 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| libyaml/test-version.eva/default | reference | cache | 3 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| solitaire/solitaire.eva/default | cache | cache.2 | 286 | 286 | 286 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |
| solitaire/solitaire.eva/default | nocache | cache | 796 | 286 | 286 | 286 | 0 | 264 | 0 | 510 | 0 | 0 | 0 | True | False |
| solitaire/solitaire.eva/default | nocache | reference | 796 | 286 | 286 | 286 | 0 | 264 | 0 | 510 | 0 | 0 | 0 | True | False |
| solitaire/solitaire.eva/default | reference | cache | 286 | 286 | 286 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | True | True |

## State queries

Run A is the baseline, run B the candidate.

| case | A | B | queries | answered_both | equal | wider | narrower | incomparable | undecided | top_a | top_b | unavailable_a_no-callstack | unavailable_b_no-callstack | unavailable_a_unreached | unavailable_b_unreached | reached_a_only | reached_b_only |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | cache.2 | 1794 | 1794 | 1794 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2048/2048.eva/default | nocache | cache | 4278 | 1794 | 1774 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 2484 | 0 | 0 | 0 | 0 |
| 2048/2048.eva/default | nocache | reference | 4278 | 1794 | 1774 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 2484 | 0 | 0 | 0 | 0 |
| 2048/2048.eva/default | reference | cache | 1794 | 1794 | 1794 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| fixtures/frame.c/default | cache | cache.2 | 64 | 64 | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| fixtures/frame.c/default | nocache | cache | 78 | 64 | 63 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 14 | 0 | 0 | 0 | 0 |
| fixtures/nested-hit.c/default | cache | cache.2 | 66 | 66 | 66 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| fixtures/nested-hit.c/default | nocache | cache | 94 | 66 | 66 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 28 | 0 | 0 | 0 | 0 |
| genann/genann.eva/default | cache | cache.2 | 13190 | 13190 | 13190 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| genann/genann.eva/default | nocache | cache | 14110 | 13190 | 13171 | 17 | 0 | 2 | 0 | 0 | 0 | 0 | 920 | 0 | 0 | 0 | 0 |
| genann/genann.eva/default | nocache | reference | 14110 | 13190 | 13171 | 17 | 0 | 2 | 0 | 0 | 0 | 0 | 920 | 0 | 0 | 0 | 0 |
| genann/genann.eva/default | reference | cache | 13190 | 13190 | 13190 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-example.eva/default | cache | cache.2 | 1622 | 1622 | 1622 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-example.eva/default | nocache | cache | 1622 | 1622 | 1622 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-example.eva/default | nocache | reference | 1622 | 1622 | 1622 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-example.eva/default | reference | cache | 1622 | 1622 | 1622 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-main.eva/default | cache | cache.2 | 29790 | 29790 | 29790 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-main.eva/default | nocache | cache | 30306 | 29790 | 29784 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 516 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-main.eva/default | nocache | reference | 30306 | 29790 | 29784 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 516 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-main.eva/default | reference | cache | 29790 | 29790 | 29790 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| kgflags/kgflags-simple.eva/default | cache | cache.2 | 1046 | 1046 | 1046 | 0 | 0 | 0 | 0 | 44 | 44 | 0 | 0 | 0 | 0 | 0 | 0 |
| kgflags/kgflags-simple.eva/default | nocache | cache | 1078 | 1046 | 1046 | 0 | 0 | 0 | 0 | 44 | 44 | 0 | 32 | 0 | 0 | 0 | 0 |
| kgflags/kgflags-simple.eva/default | nocache | reference | 1078 | 1046 | 1046 | 0 | 0 | 0 | 0 | 44 | 44 | 0 | 32 | 0 | 0 | 0 | 0 |
| kgflags/kgflags-simple.eva/default | reference | cache | 1046 | 1046 | 1046 | 0 | 0 | 0 | 0 | 44 | 44 | 0 | 0 | 0 | 0 | 0 | 0 |
| khash/khash.eva/default | cache | cache.2 | 842 | 842 | 842 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| khash/khash.eva/default | nocache | cache | 842 | 842 | 842 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| khash/khash.eva/default | nocache | reference | 842 | 842 | 842 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| khash/khash.eva/default | reference | cache | 842 | 842 | 842 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| libyaml/test-version.eva/default | cache | cache.2 | 80 | 80 | 80 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| libyaml/test-version.eva/default | nocache | cache | 80 | 80 | 80 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| libyaml/test-version.eva/default | nocache | reference | 80 | 80 | 80 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| libyaml/test-version.eva/default | reference | cache | 80 | 80 | 80 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| solitaire/solitaire.eva/default | cache | cache.2 | 3962 | 3962 | 3962 | 0 | 0 | 0 | 0 | 3130 | 3130 | 0 | 0 | 0 | 0 | 0 | 0 |
| solitaire/solitaire.eva/default | nocache | cache | 5674 | 3962 | 3962 | 0 | 0 | 0 | 0 | 3130 | 3130 | 0 | 1712 | 0 | 0 | 0 | 0 |
| solitaire/solitaire.eva/default | nocache | reference | 5674 | 3962 | 3962 | 0 | 0 | 0 | 0 | 3130 | 3130 | 0 | 1712 | 0 | 0 | 0 | 0 |
| solitaire/solitaire.eva/default | reference | cache | 3962 | 3962 | 3962 | 0 | 0 | 0 | 0 | 3130 | 3130 | 0 | 0 | 0 | 0 | 0 | 0 |

## Alarms and property statuses

Run A is the baseline, run B the candidate.

| case | A | B | properties_a | properties_b | same_status | other_status | a_only | b_only |
|---|---|---|---|---|---|---|---|---|
| 2048/2048.eva/default | cache | cache.2 | 17 | 17 | 17 | 0 | 0 | 0 |
| 2048/2048.eva/default | nocache | cache | 17 | 17 | 17 | 0 | 0 | 0 |
| 2048/2048.eva/default | nocache | reference | 17 | 17 | 17 | 0 | 0 | 0 |
| 2048/2048.eva/default | reference | cache | 17 | 17 | 17 | 0 | 0 | 0 |
| fixtures/frame.c/default | cache | cache.2 | n/a | n/a | n/a | n/a | n/a | n/a |
| fixtures/frame.c/default | nocache | cache | n/a | n/a | n/a | n/a | n/a | n/a |
| fixtures/nested-hit.c/default | cache | cache.2 | n/a | n/a | n/a | n/a | n/a | n/a |
| fixtures/nested-hit.c/default | nocache | cache | n/a | n/a | n/a | n/a | n/a | n/a |
| genann/genann.eva/default | cache | cache.2 | 75 | 75 | 75 | 0 | 0 | 0 |
| genann/genann.eva/default | nocache | cache | 75 | 75 | 75 | 0 | 0 | 0 |
| genann/genann.eva/default | nocache | reference | 75 | 75 | 75 | 0 | 0 | 0 |
| genann/genann.eva/default | reference | cache | 75 | 75 | 75 | 0 | 0 | 0 |
| jsmn/jsmn-example.eva/default | cache | cache.2 | 1 | 1 | 1 | 0 | 0 | 0 |
| jsmn/jsmn-example.eva/default | nocache | cache | 1 | 1 | 1 | 0 | 0 | 0 |
| jsmn/jsmn-example.eva/default | nocache | reference | 1 | 1 | 1 | 0 | 0 | 0 |
| jsmn/jsmn-example.eva/default | reference | cache | 1 | 1 | 1 | 0 | 0 | 0 |
| jsmn/jsmn-main.eva/default | cache | cache.2 | 0 | 0 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-main.eva/default | nocache | cache | 0 | 0 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-main.eva/default | nocache | reference | 0 | 0 | 0 | 0 | 0 | 0 |
| jsmn/jsmn-main.eva/default | reference | cache | 0 | 0 | 0 | 0 | 0 | 0 |
| kgflags/kgflags-simple.eva/default | cache | cache.2 | 35 | 35 | 35 | 0 | 0 | 0 |
| kgflags/kgflags-simple.eva/default | nocache | cache | 35 | 35 | 35 | 0 | 0 | 0 |
| kgflags/kgflags-simple.eva/default | nocache | reference | 35 | 35 | 35 | 0 | 0 | 0 |
| kgflags/kgflags-simple.eva/default | reference | cache | 35 | 35 | 35 | 0 | 0 | 0 |
| khash/khash.eva/default | cache | cache.2 | 0 | 0 | 0 | 0 | 0 | 0 |
| khash/khash.eva/default | nocache | cache | 0 | 0 | 0 | 0 | 0 | 0 |
| khash/khash.eva/default | nocache | reference | 0 | 0 | 0 | 0 | 0 | 0 |
| khash/khash.eva/default | reference | cache | 0 | 0 | 0 | 0 | 0 | 0 |
| libyaml/test-version.eva/default | cache | cache.2 | 4 | 4 | 4 | 0 | 0 | 0 |
| libyaml/test-version.eva/default | nocache | cache | 4 | 4 | 4 | 0 | 0 | 0 |
| libyaml/test-version.eva/default | nocache | reference | 4 | 4 | 4 | 0 | 0 | 0 |
| libyaml/test-version.eva/default | reference | cache | 4 | 4 | 4 | 0 | 0 | 0 |
| solitaire/solitaire.eva/default | cache | cache.2 | 274 | 274 | 274 | 0 | 0 | 0 |
| solitaire/solitaire.eva/default | nocache | cache | 274 | 274 | 274 | 0 | 0 | 0 |
| solitaire/solitaire.eva/default | nocache | reference | 274 | 274 | 274 | 0 | 0 | 0 |
| solitaire/solitaire.eva/default | reference | cache | 274 | 274 | 274 | 0 | 0 | 0 |

## Checks on the constructed cases

```
PASS nested-hit: two runs of the same binary align completely
PASS nested-hit: one call analysed without caching is a hit with memexec
PASS nested-hit: the two nested calls are reported under the hit
PASS nested-hit: no alignment is undecided or unmatched
PASS nested-hit: every record is aligned or nested under the hit
PASS nested-hit: the nested records are the calls to leaf under the second call to outer
PASS frame: before r = 0, all callstacks, memexec answer {3} is narrower than {3; 5}
PASS frame: the callstack of the second call has no answer with memexec
PASS frame: the callstack of the first call answers {3} in both runs
```

## Outcome classes of the runner

Constructed runs of tools/outcome-demo.sh, caching disabled.

```
PASS	expected timeout	observed timeout	exit 124	elapsed_s 1.00
PASS	expected oom	observed oom	exit 134	elapsed_s 2.47
PASS	expected error	observed error	exit 1	elapsed_s 0.30
PASS	expected killed	observed killed	exit 137	elapsed_s 1.59
```
