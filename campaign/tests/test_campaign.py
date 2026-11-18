"""Unit tests of campaign/tools/campaign.py.

Run from the root of the repository:
  python3 -I -m unittest discover -s campaign/tests -v
"""

import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location(
    "campaign", os.path.join(HERE, "..", "tools", "campaign.py"))
campaign = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(campaign)


def log(text):
    return text.strip("\n").split("\n")


# Messages in the forms Eva prints them: header and body on two lines or on
# one, the entry point without a location, a callstack broken over several
# lines, and other messages in between.
NESTED_LOG = """
[kernel] Parsing nested.c (with preprocessing)
[eva:cache] nested.c:9:
  call to leaf: lookup: no-candidate; execution: analysed; storage: stored (entry 1)
  stack: leaf :: nested.c:9 (stmt 5) <- outer :: nested.c:13 (stmt 12) <- main
[eva:alarm] nested.c:9: Warning:
  signed overflow. assert x + 1 <= 2147483647;
  stack: leaf :: nested.c:9 (stmt 5) <- outer :: nested.c:13 (stmt 12) <- main
[eva:cache] nested.c:9: call to leaf: lookup: hit (entry 1); execution: not-analysed; storage: none
  stack: leaf :: nested.c:9 (stmt 5) <-
         outer :: nested.c:13 (stmt 12) <-
         main
[eva:cache] nested.c:13:
  call to outer: lookup: no-candidate; execution: analysed; storage: stored (entry 2)
  stack: outer :: nested.c:13 (stmt 12) <- main
[eva:cache] nested.c:14:
  call to outer: lookup: hit (entry 2); execution: not-analysed; storage: none
  stack: outer :: nested.c:14 (stmt 13) <- main
[eva:cache]
  call to main: lookup: no-candidate; execution: analysed; storage: refused (not-cacheable)
  stack: main
[eva] done
"""

# The same program with caching disabled: the second call to outer is
# analysed and makes two nested calls.
NESTED_LOG_OFF = """
[eva:cache] nested.c:9:
  call to leaf: lookup: no-candidate; execution: analysed; storage: refused (disabled)
  stack: leaf :: nested.c:9 (stmt 5) <- outer :: nested.c:13 (stmt 12) <- main
[eva:cache] nested.c:9:
  call to leaf: lookup: no-candidate; execution: analysed; storage: refused (disabled)
  stack: leaf :: nested.c:9 (stmt 5) <- outer :: nested.c:13 (stmt 12) <- main
[eva:cache] nested.c:13:
  call to outer: lookup: no-candidate; execution: analysed; storage: refused (disabled)
  stack: outer :: nested.c:13 (stmt 12) <- main
[eva:cache] nested.c:9:
  call to leaf: lookup: no-candidate; execution: analysed; storage: refused (disabled)
  stack: leaf :: nested.c:9 (stmt 5) <- outer :: nested.c:14 (stmt 13) <- main
[eva:cache] nested.c:9:
  call to leaf: lookup: no-candidate; execution: analysed; storage: refused (disabled)
  stack: leaf :: nested.c:9 (stmt 5) <- outer :: nested.c:14 (stmt 13) <- main
[eva:cache] nested.c:14:
  call to outer: lookup: no-candidate; execution: analysed; storage: refused (disabled)
  stack: outer :: nested.c:14 (stmt 13) <- main
[eva:cache]
  call to main: lookup: no-candidate; execution: analysed; storage: refused (disabled)
  stack: main
"""


def records_of(text):
    """The rows written by the records subcommand for a log."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "eva.log")
        out = os.path.join(tmp, "records.jsonl")
        with open(path, "w") as f:
            f.write(text)
        campaign.main(["records", path, out])
        return campaign.load_records(out)


class Parser(unittest.TestCase):

    def test_forms_of_messages(self):
        records = campaign.cache_records(log(NESTED_LOG))
        self.assertEqual(len(records), 5)
        first, hit, _, _, main = records
        self.assertEqual(first["site"], "nested.c:9")
        self.assertEqual(first["function"], "leaf")
        self.assertEqual(first["dispositions"]["storage"], "stored (entry 1)")
        self.assertEqual(first["frames"],
                         [("outer", "nested.c:13", 12),
                          ("leaf", "nested.c:9", 5)])
        self.assertEqual(first["stmt"], 5)
        self.assertEqual(hit["dispositions"]["lookup"], "hit (entry 1)")
        self.assertEqual(hit["frames"], first["frames"])
        self.assertEqual(main["site"], "")
        self.assertEqual(main["frames"], [])
        self.assertEqual(main["entry_point"], "main")

    def test_unknown_fields_and_reasons_are_kept(self):
        # A lookup disposition with a reason of its own, as issue #45 adds,
        # and a storage disposition followed by a collector verdict and a
        # field of its own, as issue #41 adds: kept verbatim.
        text = ("nested.c:9: \ncall to leaf: lookup: rejected (entry 3: "
                "hint-generation); execution: analysed; storage: refused "
                "(not-cacheable) [collector: refused (nested-call; "
                "sweep)]; collector: would-store (x)\n"
                "stack: leaf :: nested.c:9 <- main")
        record = campaign.parse_cache_message(text)
        d = record["dispositions"]
        self.assertEqual(list(d), ["lookup", "execution", "storage",
                                   "collector"])
        self.assertEqual(d["lookup"], "rejected (entry 3: hint-generation)")
        self.assertEqual(
            d["storage"],
            "refused (not-cacheable) [collector: refused (nested-call; "
            "sweep)]")
        self.assertEqual(d["collector"], "would-store (x)")
        self.assertEqual(campaign.kinds(record),
                         ("rejected", "analysed", "refused"))

    def test_producers_with_later_forms(self):
        # The producer of a hit is found when the storage disposition has a
        # collector verdict after it; a rejected lookup names an entry but
        # is not a hit.
        text = """
[eva:cache] nested.c:9:
  call to leaf: lookup: no-candidate; execution: analysed; storage: stored (entry 1) [collector: kept]
  stack: leaf :: nested.c:9 <- main
[eva:cache] nested.c:10:
  call to leaf: lookup: hit (entry 1); execution: not-analysed; storage: none
  stack: leaf :: nested.c:10 <- main
[eva:cache] nested.c:11:
  call to leaf: lookup: rejected (entry 1: hint-generation); execution: analysed; storage: none; collector: swept (2)
  stack: leaf :: nested.c:11 <- main
[eva:cache]
  call to main: lookup: no-candidate; execution: analysed; storage: refused (not-cacheable)
  stack: main
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "eva.log")
            with open(path, "w") as f:
                f.write(text)
            out = os.path.join(tmp, "records.jsonl")
            with contextlib.redirect_stderr(io.StringIO()):
                campaign.main(["records", path, out])
            rows = {r["site"]: r for r in campaign.load_records(out)}
        self.assertEqual(rows["nested.c:9"]["storage"], "stored")
        self.assertEqual(rows["nested.c:10"]["hit_of"],
                         "main#0 > leaf@nested.c:9#0")
        self.assertEqual(rows["nested.c:10"]["lookup_hit_entry"], 1)
        self.assertEqual(rows["nested.c:11"]["lookup"], "rejected")
        self.assertIsNone(rows["nested.c:11"]["hit_of"])
        self.assertEqual(rows["nested.c:11"]["dispositions"]["collector"],
                         "swept (2)")

    def test_other_messages_are_ignored(self):
        lines = log("[eva:cache] not a call\n[eva] call to x: y")
        self.assertEqual(campaign.cache_records(lines), [])

    def test_callstack_hash(self):
        entry, frames = campaign.parse_stack("<Ab12> f :: a.c:1 <- main")
        self.assertEqual((entry, frames), ("main", [("f", "a.c:1", None)]))
        entry, frames = campaign.parse_stack(
            "<Ab12> f :: a.c:1 (stmt 7) <- main")
        self.assertEqual((entry, frames), ("main", [("f", "a.c:1", 7)]))


class Tree(unittest.TestCase):

    def test_identities_and_hits(self):
        rows = records_of(NESTED_LOG)
        ids = [r["id"] for r in rows]
        self.assertEqual(ids, [
            "main#0",
            "main#0 > outer@nested.c:13/s12#0",
            "main#0 > outer@nested.c:13/s12#0 > leaf@nested.c:9/s5#0",
            "main#0 > outer@nested.c:13/s12#0 > leaf@nested.c:9/s5#1",
            "main#0 > outer@nested.c:14/s13#0",
        ])
        by_id = {r["id"]: r for r in rows}
        self.assertEqual(
            by_id["main#0 > outer@nested.c:14/s13#0"]["hit_of"],
            "main#0 > outer@nested.c:13/s12#0")
        self.assertEqual(
            by_id["main#0 > outer@nested.c:13/s12#0 > leaf@nested.c:9/s5#1"]
            ["hit_of"],
            "main#0 > outer@nested.c:13/s12#0 > leaf@nested.c:9/s5#0")

    def test_killed_run_gets_open_parents(self):
        # The run stopped inside the second call to outer: its nested call
        # and main never printed their message.
        text = "\n".join(NESTED_LOG_OFF.strip("\n").split("\n")[:12])
        with contextlib.redirect_stderr(io.StringIO()):
            rows = records_of(text)
        by_id = {r["id"]: r for r in rows}
        self.assertIn("main#0", by_id)
        self.assertEqual(by_id["main#0"]["execution"], "open")
        self.assertTrue(by_id["main#0"]["inferred"])
        self.assertIn(
            "main#0 > outer@nested.c:14/s13#0 > leaf@nested.c:9/s5#0", by_id)
        self.assertEqual(
            by_id["main#0 > outer@nested.c:14/s13#0"]["execution"], "open")

    def test_missing_callstack_is_an_error(self):
        records = campaign.cache_records(log(
            "[eva:cache] a.c:1: \n  call to f: lookup: no-candidate; "
            "execution: analysed; storage: none"))
        with self.assertRaises(ValueError):
            campaign.build_tree(records)


class Alignment(unittest.TestCase):

    def test_same_run_aligns_completely(self):
        rows = records_of(NESTED_LOG)
        summary = campaign.summarize_alignment(
            rows, rows, campaign.align(rows, rows))
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["aligned"], 5)

    def test_hit_against_nested_lookups(self):
        off, on = records_of(NESTED_LOG_OFF), records_of(NESTED_LOG)
        result = campaign.align(off, on)
        summary = campaign.summarize_alignment(off, on, result)
        self.assertEqual(summary["aligned"], 5)
        self.assertEqual(summary["analysed_a_hit_b"], 2)
        self.assertEqual(summary["nested_under_hit_b"], 2)
        self.assertEqual(summary["undecided_groups"], 0)
        self.assertFalse(summary["complete"])
        self.assertTrue(summary["accounted"])
        self.assertEqual(
            sorted(i for _, i, _ in result["under_hit"]),
            ["main#0 > outer@nested.c:14/s13#0 > leaf@nested.c:9/s5#0",
             "main#0 > outer@nested.c:14/s13#0 > leaf@nested.c:9/s5#1"])

    @staticmethod
    def row(id_, parent, seq, function, site, lookup="no-candidate",
            stmt="line"):
        # By default, the statement number is the line of the call site.
        if stmt == "line":
            stmt = int(site.rsplit(":", 1)[1]) if site else None
        return {"id": id_, "parent": parent, "seq": seq,
                "function": function, "site": site, "stmt": stmt,
                "lookup": lookup, "execution": "analysed", "storage": "none",
                "dispositions": {"lookup": lookup}}

    def test_ambiguous_siblings_are_undecided(self):
        # Under main, a loop reaches f twice at one site in run A and three
        # times in run B: no alignment of these calls is guessed.
        r = self.row
        a = [r("m", None, 9, "main", ""),
             r("m > f@a.c:3#0", "m", 0, "f", "a.c:3"),
             r("m > f@a.c:3#1", "m", 1, "f", "a.c:3"),
             r("m > g@a.c:4#0", "m", 2, "g", "a.c:4")]
        b = [r("m", None, 9, "main", ""),
             r("m > f@a.c:3#0", "m", 0, "f", "a.c:3"),
             r("m > f@a.c:3#1", "m", 1, "f", "a.c:3"),
             r("m > f@a.c:3#2", "m", 2, "f", "a.c:3"),
             r("m > g@a.c:4#0", "m", 3, "g", "a.c:4")]
        result = campaign.align(a, b)
        summary = campaign.summarize_alignment(a, b, result)
        self.assertEqual(result["undecided"],
                         [("m", "m", "f@a.c:3/s3", 2, 3, 2, 3,
                           "repeated calls in another order")])
        self.assertEqual(summary["aligned"], 2)  # main and g
        self.assertTrue(summary["accounted"])
        self.assertFalse(summary["complete"])

    def test_reordered_siblings_are_undecided(self):
        r = self.row
        a = [r("m", None, 9, "main", ""),
             r("m > f@a.c:3#0", "m", 0, "f", "a.c:3"),
             r("m > g@a.c:4#0", "m", 1, "g", "a.c:4"),
             r("m > f@a.c:3#1", "m", 2, "f", "a.c:3")]
        b = [r("m", None, 9, "main", ""),
             r("m > f@a.c:3#0", "m", 0, "f", "a.c:3"),
             r("m > f@a.c:3#1", "m", 1, "f", "a.c:3"),
             r("m > g@a.c:4#0", "m", 2, "g", "a.c:4")]
        result = campaign.align(a, b)
        self.assertEqual(len(result["undecided"]), 1)
        self.assertEqual([x["id"] for x, _ in result["pairs"]],
                         ["m", "m > g@a.c:4#0"])

    def test_call_in_one_run_only_is_unmatched(self):
        r = self.row
        a = [r("m", None, 9, "main", ""),
             r("m > f@a.c:3#0", "m", 0, "f", "a.c:3")]
        b = [r("m", None, 9, "main", "")]
        result = campaign.align(a, b)
        self.assertEqual(result["unmatched"],
                         [("A", "m > f@a.c:3#0", "no call at this site in B")])


class Values(unittest.TestCase):

    def inc(self, a, b):
        return campaign.ival_included(campaign.parse_ival(a),
                                      campaign.parse_ival(b))

    def test_integers(self):
        self.assertTrue(self.inc("S3", "S3,5"))
        self.assertFalse(self.inc("S3,5", "S3"))
        self.assertTrue(self.inc("S2,4", "I0..10%0/2"))
        self.assertFalse(self.inc("S3", "I0..10%0/2"))
        self.assertTrue(self.inc("I0..10%0/2", "I..%0/1"))
        self.assertTrue(self.inc("I0..12%0/4", "I0..20%0/2"))
        self.assertFalse(self.inc("I0..12%0/2", "I0..20%0/4"))
        self.assertFalse(self.inc("I..10%0/1", "I0..10%0/1"))
        self.assertTrue(self.inc("I0..4%0/2", "S0,2,4"))
        self.assertFalse(self.inc("I0..6%0/2", "S0,2,4"))
        self.assertTrue(self.inc("B", "S1"))

    def test_floats(self):
        self.assertTrue(self.inc("F0x1p+0..0x1p+1", "F0x0p+0..0x1p+2"))
        self.assertFalse(self.inc("F-0x0p+0..0x1p+0", "F0x0p+0..0x1p+0"))
        self.assertTrue(self.inc("F0x0p+0..0x0p+0", "F-0x0p+0..0x0p+0"))
        self.assertFalse(self.inc("F0x1p+0..0x1p+0;nan", "F0x1p+0..0x1p+0"))
        self.assertTrue(self.inc("Fnan", "F0x1p+0..0x1p+0;nan"))
        self.assertFalse(self.inc("S1", "F0x1p+0..0x1p+0"))

    def test_nan_suffix_in_a_map(self):
        value = campaign.parse_value("MNULL=F-infinity..infinity;nan;x=S1")
        self.assertEqual(value[1]["NULL"],
                         ("float", float("-inf"), float("inf"), True))
        self.assertEqual(value[1]["x"], ("set", frozenset([1])))
        self.assertEqual(
            campaign.classify((1, 0, "MNULL=F-infinity..infinity;nan"),
                              (1, 0, "MNULL=F-infinity..infinity;nan")),
            "equal")
        self.assertEqual(
            campaign.classify((1, 0, "MNULL=F0x0p+0..0x1p+0"),
                              (1, 0, "MNULL=F-infinity..infinity;nan")),
            "wider")

    def test_same_written_answers_are_equal(self):
        self.assertEqual(campaign.classify((1, 0, "Mx=Iunparsed"),
                                           (1, 0, "Mx=Iunparsed")), "equal")

    def test_classify(self):
        c = campaign.classify
        self.assertEqual(c((1, 0, "MNULL=S3,5"), (1, 0, "MNULL=S3")),
                         "narrower")
        self.assertEqual(c((1, 0, "MNULL=S3"), (1, 0, "MNULL=S3,5")),
                         "wider")
        self.assertEqual(c((1, 0, "MNULL=S3"), (1, 0, "MNULL=S3")), "equal")
        self.assertEqual(c((1, 0, "MNULL=S3"), (1, 0, "MNULL=S4")),
                         "incomparable")
        self.assertEqual(c((1, 0, "MNULL=S3"), (0, 0, "MNULL=S3")), "wider")
        self.assertEqual(c((1, 0, "Mx=S0"), (1, 0, "Gx;y")), "wider")
        self.assertEqual(c((1, 0, "MNULL=S0;x=S0"), (1, 0, "Gx")),
                         "incomparable")
        self.assertEqual(c((1, 0, "Gx"), (1, 0, "T")), "wider")
        self.assertEqual(c((1, 0, "MNULL=S1"), (1, 0, "Z?")), "undecided")

    def test_top_answers(self):
        self.assertTrue(campaign.is_top_answer("T"))
        self.assertTrue(campaign.is_top_answer("MNULL=I..%0/1"))
        self.assertTrue(campaign.is_top_answer(
            "MNULL=F-infinity..infinity;nan"))
        self.assertFalse(campaign.is_top_answer("MNULL=I0..%0/1"))
        self.assertFalse(campaign.is_top_answer(
            "MNULL=F-infinity..infinity"))
        # A garbled mix keeps its bases: counted apart, not as top.
        self.assertFalse(campaign.is_top_answer("Gx"))
        self.assertTrue(campaign.is_garbled_answer("Gx"))


class Queries(unittest.TestCase):

    def test_example_run(self):
        # The answers of the example run of issue #3, written by the query
        # module: with memexec the second callstack does not exist.
        nocache = (
            "reach\tget\tget:8:0\n"
            "answer\tget\tget:8:0\tbefore\t*\tr\t1\t0\tMNULL=S3,5\n"
            "answer\tget\tget:8:0\tbefore\tmain|get@main:16:1\tr\t1\t0\t"
            "MNULL=S3\n"
            "answer\tget\tget:8:0\tbefore\tmain|get@main:18:1\tr\t1\t0\t"
            "MNULL=S5\n"
            "done\t3\n")
        cache = (
            "reach\tget\tget:8:0\n"
            "answer\tget\tget:8:0\tbefore\t*\tr\t1\t0\tMNULL=S3\n"
            "answer\tget\tget:8:0\tbefore\tmain|get@main:16:1\tr\t1\t0\t"
            "MNULL=S3\n"
            "done\t2\n")
        with tempfile.TemporaryDirectory() as tmp:
            a, b = os.path.join(tmp, "a"), os.path.join(tmp, "b")
            with open(a, "w") as f:
                f.write(nocache)
            with open(b, "w") as f:
                f.write(cache)
            summary, details, _ = campaign.compare_queries(a, b)
        self.assertEqual(summary["queries"], 3)
        self.assertEqual(summary["answered_both"], 2)
        self.assertEqual(summary["equal"], 1)
        self.assertEqual(summary["narrower"], 1)
        self.assertEqual(summary["unavailable_b_no-callstack"], 1)


class Outcomes(unittest.TestCase):

    def outcome(self, status, elapsed=1.0, log="", entry=True, make=0,
                parse=0, measured=True, watchdog="none", signal=None):
        measure = None
        if measured:
            if signal is None and status > 128:
                signal = status - 128
            measure = {"status": str(status), "elapsed_s": str(elapsed),
                       "watchdog": watchdog,
                       "signal": "-" if signal is None else str(signal)}
        return campaign.classify_outcome(parse, make, measure, log, entry,
                                         60.0)

    def test_classes(self):
        self.assertEqual(self.outcome(0), "completed")
        self.assertEqual(self.outcome(0, entry=False), "incomplete")
        self.assertEqual(self.outcome(143, 60.0, watchdog="term"), "timeout")
        self.assertEqual(self.outcome(137, 120.0, watchdog="kill"),
                         "timeout")
        self.assertEqual(self.outcome(137, 10.0), "killed")
        self.assertEqual(self.outcome(1), "error")
        self.assertEqual(self.outcome(4), "error")
        self.assertEqual(self.outcome(139), "error")
        # Exit status 124 of the analyzer itself, and SIGKILL near the
        # deadline, are not timeouts when the watchdog did not fire.
        self.assertEqual(self.outcome(124, 60.0, signal=None), "error")
        self.assertEqual(self.outcome(137, 59.9), "killed")
        self.assertEqual(
            self.outcome(125, log="[kernel] Unexpected error (Out of memory)."),
            "oom")
        self.assertEqual(
            self.outcome(134, log="Fatal error: Not enough heap memory to "
                         "reserve minor heaps"), "oom")
        self.assertEqual(self.outcome(2, log="Fatal error: out of memory"),
                         "oom")
        self.assertEqual(
            self.outcome(2, log="x\nFatal error: exception Out of memory\n"),
            "oom")
        self.assertEqual(
            self.outcome(134, log="Fatal error: allocation failure during "
                         "minor GC"), "oom")
        self.assertEqual(self.outcome(0, parse=2), "parse-error")
        self.assertEqual(self.outcome(0, measured=False), "harness-error")
        self.assertEqual(self.outcome(0, make=2), "harness-error")


class Measure(unittest.TestCase):

    def test_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "measure")
            with open(path, "w") as f:
                f.write("Command terminated by signal 9\nelapsed_s\t2.5\n"
                        "maxrss_kib\t100\nstatus\t0\n")
            measure = campaign.read_measure(path)
        self.assertEqual(measure["status"], "137")
        self.assertEqual(measure["signal"], "9")
        self.assertEqual(
            campaign.classify_outcome(0, 2, measure, "", False, 60.0),
            "killed")


class Counts(unittest.TestCase):

    def test_builtins_and_cache(self):
        stats = ("builtin-applied-malloc\tmalloc\t\t2\n"
                 "builtin-applied-Frama_C_free\tmy_free\t\t1\n"
                 "builtin-applied-strlen\tstrlen\t\t5\n"
                 "memexec-hits\tf\t\t3\n"
                 "memexec-refused-not-cacheable\tg\t\t1\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stats.csv")
            with open(path, "w") as f:
                f.write(stats)
            counts = campaign.run_counts(path)
        self.assertEqual(counts["malloc"], 2)
        self.assertEqual(counts["free"], 1)
        self.assertEqual(counts["allocation_and_release"], 3)
        self.assertFalse(counts["in_set_a"])
        self.assertEqual(counts["hits"], 3)
        self.assertEqual(counts["refused"], 1)

    def test_unknown_cache_counters_are_ignored(self):
        stats = ("memexec-hits\tf\t\t3\n"
                 "memexec-collector-swept\tf\t\t7\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stats.csv")
            with open(path, "w") as f:
                f.write(stats)
            counts = campaign.run_counts(path)
            rows = campaign.function_counts(path)
        self.assertEqual((counts["hits"], counts["misses"]), (3, 0))
        self.assertEqual(rows, [["f", 3, 0, 0, 0, 0, 0]])


class Tables(unittest.TestCase):

    def test_cache_activity_per_function(self):
        stats = ("memexec-hits\tf\t\t3\n"
                 "memexec-misses\tf\t\t1\n"
                 "memexec-misses\tg\t\t2\n"
                 "memexec-refused-not-cacheable\tg\t\t1\n"
                 "builtin-applied-strlen\tstrlen\t\t5\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stats.csv")
            with open(path, "w") as f:
                f.write(stats)
            rows = campaign.function_counts(path)
        self.assertEqual(rows, [["f", 3, 1, 0, 0, 0, 0],
                                ["g", 0, 2, 0, 1, 0, 0]])

    def test_unmeasured_runs_leave_no_empty_cell(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = os.path.join(tmp, "runs", "fixtures", "f.c", "default",
                               "cache")
            os.makedirs(run)
            with open(os.path.join(run, "run.tsv"), "w") as f:
                f.write("case\tfixtures/f.c/default\nmode\tcache\n"
                        "outcome\tcompleted\nexit\t0\n")
            with contextlib.redirect_stdout(io.StringIO()):
                campaign.main(["tables", tmp])
            for name in os.listdir(os.path.join(tmp, "tables")):
                with open(os.path.join(tmp, "tables", name)) as f:
                    for line in f:
                        self.assertEqual(line.rstrip("\n"), line.rstrip(),
                                         name)

    def test_times_and_ratios(self):
        runs = [
            {"case": "c", "mode": "nocache", "outcome": "completed",
             "elapsed_s": "2.00"},
            {"case": "c", "mode": "cache", "outcome": "completed",
             "elapsed_s": "0.50"},
            {"case": "c", "mode": "cache.2", "outcome": "completed",
             "elapsed_s": "0.40"},
            {"case": "c", "mode": "reference", "outcome": "timeout",
             "elapsed_s": "180.00"},
            {"case": "d", "mode": "nocache", "outcome": "completed",
             "elapsed_s": "1.00"},
            {"case": "e", "mode": "nocache", "outcome": "completed"},
            {"case": "e", "mode": "cache", "outcome": "completed"},
        ]
        self.assertEqual(campaign.time_rows(runs), [
            ["c", "2.00", "0.50", "timeout", "0.250", "n/a"],
            ["d", "1.00", "not run", "not run", "n/a", "n/a"],
            ["e", "not measured", "not measured", "not run", "n/a", "n/a"],
        ])



def write(path, text):
    with open(path, "w") as f:
        f.write(text)


# The reviewer's same-line input (issue #54): "if (SIDE) f(1); else f(2);"
# on line 4, two runs taking opposite branches, logged by a binary that does
# not print statement numbers.
SITES_LEGACY_0 = """
[eva:cache] sites.c:4:
  call to f: lookup: no-candidate; execution: analysed; storage: stored (entry 1)
  stack: f :: sites.c:4 <- main
[eva:cache]
  call to main: lookup: no-candidate; execution: analysed; storage: stored (entry 2)
  stack: main
"""

# fixtures/same-line.c analysed by the analyzer of issue #54 with SIDE 0
# and SIDE 1, under -eva-msg-key cache,callstacks: the two runs reach the
# calls f(2) and f(1), statements 7 and 6 of line 10. The messages of the
# logs, without the blank that ends their headers.
SAME_LINE_SIDE0 = """
[eva:cache] same-line.c:10:
  call to f: lookup: no-candidate; execution: analysed; storage: stored (entry 1); collector: would-store
  stack: f :: same-line.c:10 (stmt 7) <-
         main
[eva:cache]
  call to main: lookup: no-candidate; execution: analysed; storage: stored (entry 2); collector: refused (sweep)
  stack: main
"""
SAME_LINE_SIDE1 = SAME_LINE_SIDE0.replace("(stmt 7)", "(stmt 6)")


class SameLineCalls(unittest.TestCase):
    """H1: the call-site key holds the statement number."""

    def test_two_statements_of_one_line_are_unmatched(self):
        a, b = records_of(SAME_LINE_SIDE0), records_of(SAME_LINE_SIDE1)
        result = campaign.align(a, b)
        summary = campaign.summarize_alignment(a, b, result)
        self.assertEqual(summary["aligned"], 1)  # main only
        self.assertEqual((summary["unmatched_a"], summary["unmatched_b"]),
                         (1, 1))
        self.assertFalse(summary["complete"])

    def test_without_statement_numbers_nothing_below_main_aligns(self):
        a, b = records_of(SITES_LEGACY_0), records_of(SITES_LEGACY_0)
        result = campaign.align(a, b)
        summary = campaign.summarize_alignment(a, b, result)
        self.assertEqual(summary["aligned"], 1)
        self.assertEqual(result["undecided"],
                         [("main#0", "main#0", "f@sites.c:4", 1, 1, 1, 1,
                           "no statement number")])
        self.assertFalse(summary["complete"])
        self.assertIn("statement numbers missing", summary["verdict"])

    def test_same_run_with_numbers_aligns_completely(self):
        rows = records_of(SAME_LINE_SIDE0)
        summary = campaign.summarize_alignment(
            rows, rows, campaign.align(rows, rows))
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["verdict"], "complete")

    def test_numbering_not_established(self):
        rows = records_of(SAME_LINE_SIDE0)
        summary = campaign.summarize_alignment(
            rows, rows, campaign.align(rows, rows),
            numbering="not established")
        self.assertFalse(summary["complete"])


# Lookup dispositions printed by the analyzer of issue #54 for the test
# plugins/eva/tests/value/cache_supplied.c of the analyzer, run under
# -eva-msg-key cache,callstacks: messages of the run with the domains cvalue
# and sign, in which every candidate is rejected, and of the default run.
SUPPLIED_LOG_PRODUCT = """
[eva:cache] cache_supplied.c:120:
  call to step: lookup: rejected (entry 1: product); execution: analysed; storage: refused (supplied-only); collector: refused (builtin)
  stack: step :: cache_supplied.c:120 (stmt 49) <- main
[eva:cache] cache_supplied.c:135:
  call to precise_first: lookup: rejected (entry 3: product), rejected (entry 4: product); execution: analysed; storage: refused (supplied-only); collector: refused (builtin)
  stack: precise_first :: cache_supplied.c:135 (stmt 64) <- main
[eva:cache]
  call to main: lookup: no-candidate; execution: analysed; storage: refused (supplied-only); collector: refused (builtin)
  stack: main
"""
SUPPLIED_LOG_DEFAULT = """
[eva:cache] cache_supplied.c:127:
  call to step: lookup: rejected (entry 1: key-differs); execution: analysed; storage: refused (supplied-only); collector: refused (builtin)
  stack: step :: cache_supplied.c:127 (stmt 56) <- main
[eva:cache] cache_supplied.c:138:
  call to wide_first: lookup: hit (entry 5); execution: not-analysed; storage: none
  stack: wide_first :: cache_supplied.c:138 (stmt 67) <- main
[eva:cache]
  call to main: lookup: no-candidate; execution: analysed; storage: refused (supplied-only); collector: refused (builtin)
  stack: main
"""
# No test of the analyzer rejects a candidate and then uses another one.
# Call_cache.pretty_lookup prints the rejections, then ", ", then the hit.
SUPPLIED_LOG_BOTH = SUPPLIED_LOG_DEFAULT.replace(
    "lookup: hit (entry 5)", "lookup: rejected (entry 4: key-differs), "
    "hit (entry 5)")


class LookupCandidates(unittest.TestCase):
    """H2: the lookup disposition is a sequence of candidates."""

    def test_parse_lookup(self):
        p = campaign.parse_lookup
        self.assertEqual(
            p("rejected (entry 1: key-differs), hit (entry 2)"),
            {"kind": "hit", "rejected": [[1, "key-differs"]], "hit": 2,
             "other": []})
        self.assertEqual(
            p("rejected (entry 3: product), rejected (entry 4: product)"),
            {"kind": "rejected", "rejected": [[3, "product"], [4, "product"]],
             "hit": None, "other": []})
        self.assertEqual(p("no-candidate")["kind"], "no-candidate")
        unknown = p("deferred (entry 5: later), hit (entry 6)")
        self.assertEqual(unknown["kind"], "hit")
        self.assertEqual(unknown["other"], ["deferred (entry 5: later)"])

    def test_records_keep_each_candidate(self):
        rows = {r["function"]: r for r in records_of(SUPPLIED_LOG_PRODUCT)}
        self.assertEqual(rows["precise_first"]["lookup"], "rejected")
        self.assertEqual(rows["precise_first"].get("lookup_rejected"),
                         [[3, "product"], [4, "product"]])
        self.assertIsNone(rows["precise_first"].get("lookup_hit_entry"))
        self.assertEqual(rows["step"].get("collector"), "refused")
        self.assertEqual(
            rows["step"]["dispositions"]["collector"], "refused (builtin)")
        rows = {r["function"]: r for r in records_of(SUPPLIED_LOG_DEFAULT)}
        self.assertEqual(rows["step"].get("lookup_rejected"),
                         [[1, "key-differs"]])
        self.assertEqual(rows["wide_first"]["lookup"], "hit")
        self.assertEqual(rows["wide_first"].get("lookup_hit_entry"), 5)
        rows = {r["function"]: r for r in records_of(SUPPLIED_LOG_BOTH)}
        hit = rows["wide_first"]
        self.assertEqual(hit["lookup"], "hit")
        self.assertEqual(hit.get("lookup_rejected"), [[4, "key-differs"]])
        self.assertEqual(hit.get("lookup_hit_entry"), 5)


# Counters of the statistics file of the analyzer of issue #54 for the test
# plugins/eva/tests/value/cache_supplied.c of the analyzer, default run
# (the rows of the times, iterations and coverage left out). The producer
# and the collector are on by default.
STATS = """alarm-count\t\t\t0
cache-hits\tstep\t\t1
cache-hits\tset_out\t\t1
cache-hits\tprecise_first\t\t1
cache-hits\twide_first\t\t1
cache-hits\tloop_on_4\t\t1
cache-hits\twrite_then_spin\t\t1
cache-hits\tnever_returns\t\t1
cache-hits\ttwice\t\t1
cache-hits\tleak_address\t\t1
cache-produced\ttwice\t\t1
cache-production-refused-builtin\tstep\t\t1
cache-production-refused-builtin\tplain\t\t2
cache-production-refused-builtin\tmain\t\t1
cache-refused-supplied-only\tstep\t\t1
cache-refused-supplied-only\tplain\t\t2
cache-refused-supplied-only\ttwice\t\t1
cache-refused-supplied-only\tmain\t\t1
cache-rejected-key-differs\tstep\t\t1
cache-rejected-key-differs\ttwice\t\t1
collector-refused-builtin\tstep\t\t1
collector-refused-builtin\tplain\t\t2
collector-refused-builtin\tmain\t\t1
collector-would-store\ttwice\t\t1
partitioning-index-misses\t\t\t60
"""


class CounterFamilies(unittest.TestCase):
    """H2: counter families, absent counters and measured zeros."""

    def counts(self, text, families):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stats.csv")
            write(path, text)
            return campaign.run_counts(path, families)

    def test_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stats.csv")
            write(path, STATS)
            c = campaign.run_counts(path)
        self.assertEqual(c.get("supplied_hits"), 9)
        self.assertEqual(c.get("collector_would_store"), 1)
        c = self.counts(STATS, set(campaign.FAMILIES))
        self.assertEqual(c["supplied_hits"], 9)
        self.assertEqual(c["supplied_rejected"], 2)
        self.assertEqual(c["supplied_rejected_by_reason"], "key-differs=2")
        self.assertEqual(c["supplied_refused"], 5)
        self.assertEqual(c["collector_would_store"], 1)
        self.assertEqual(c["collector_refused"], 4)
        self.assertEqual(c["collector_refused_by_reason"], "builtin=4")
        self.assertEqual(c["producer_stored"], 1)
        self.assertEqual(c["producer_refused"], 4)
        self.assertEqual(c["hits"], 0)  # measured zero: no memexec counter
        self.assertEqual(c["malloc"], 0)
        c = self.counts(STATS, set(campaign.FAMILIES) - {"memexec"})
        self.assertIsNone(c["hits"])  # memexec not measured

    def test_absent_builtin_counter_is_not_set_a(self):
        c = self.counts("memexec-hits\tf\t\t1\n", {"memexec"})
        self.assertIsNone(c["in_set_a"])
        self.assertIsNone(c["allocation_and_release"])
        c = self.counts("memexec-hits\tf\t\t1\n", {"memexec", "builtin"})
        self.assertTrue(c["in_set_a"])
        self.assertEqual(c["misses"], 0)

    def test_measured_families_of_a_run(self):
        binary = ["builtin", "memexec", "collector", "producer"]
        self.assertEqual(
            campaign.measured_families(binary, "-eva-no-memexec"),
            {"builtin", "collector", "producer"})
        self.assertEqual(
            campaign.measured_families(
                binary, "-eva-memexec -eva-no-cache-collect"),
            {"builtin", "memexec"})


QUERIES_NO_RESULTS = """reach\tget\tget:10:0
unavailable\tget\tget:10:0\tbefore\t*\tt[i]\tno-results
unavailable\tget\tget:10:0\tafter\t*\tt[i]\tno-results
done\t2
"""
QUERIES_RESULTS = """reach\tget\tget:10:0
answer\tget\tget:10:0\tbefore\t*\tt[i]\t1\t0\tT
answer\tget\tget:10:0\tafter\t*\tt[i]\t1\t0\tMNULL=S0
answer\tget\tget:exit\texit\t*\tr\t1\t0\tMNULL=S0
done\t3
"""


def compare_queries_files(a, b):
    """The summary, differences and statements reached in one run written
    by the queries subcommand, as the runner calls it, for two answer
    files. The values of the summary are strings."""
    with tempfile.TemporaryDirectory() as tmp:
        pa, pb = os.path.join(tmp, "a"), os.path.join(tmp, "b")
        write(pa, a)
        write(pb, b)
        prefix = os.path.join(tmp, "queries-")
        with contextlib.redirect_stdout(io.StringIO()):
            campaign.main(["queries", pa, pb, prefix])
        with open(prefix + "summary.tsv") as f:
            summary = dict(l.rstrip("\n").split("\t", 1) for l in f)
        with open(prefix + "differences.tsv") as f:
            details = [tuple(l.rstrip("\n").split("\t"))
                       for l in list(f)[1:]]
        reach = []
        if os.path.exists(prefix + "reached-in-one-run.tsv"):
            with open(prefix + "reached-in-one-run.tsv") as f:
                reach = [tuple(l.rstrip("\n").split("\t"))
                         for l in list(f)[1:]]
        return summary, details, reach


class QueryAvailability(unittest.TestCase):
    """H3 and H8: unavailable states, completion, exit states."""

    def compare(self, a, b):
        return compare_queries_files(a, b)

    def test_unavailable_state_is_not_an_answer(self):
        summary, details, _ = self.compare(QUERIES_RESULTS,
                                           QUERIES_NO_RESULTS)
        self.assertEqual(summary.get("answered_both"), "0")
        self.assertEqual(summary.get("unavailable_b_no-results"), "2")
        self.assertEqual(summary.get("top_a"), "1")
        self.assertEqual(summary.get("top_b"), "0")
        self.assertEqual(summary.get("comparison"), "complete")
        self.assertIn(("get", "get:10:0", "before", "*", "t[i]",
                       "unavailable in B (no-results)", "T", ""), details)

    def test_done_line_is_checked(self):
        cut = QUERIES_RESULTS.replace("done\t3\n", "")
        summary, _, _ = self.compare(QUERIES_RESULTS, cut)
        self.assertEqual(summary.get("complete_b"),
                         "incomplete: no done line")
        self.assertEqual(summary.get("comparison"), "incomplete")
        wrong = QUERIES_RESULTS.replace("done\t3", "done\t4")
        summary, _, _ = self.compare(QUERIES_RESULTS, wrong)
        self.assertEqual(summary.get("complete_b"),
                         "incomplete: done 4, 3 lines")

    def test_exit_states_are_compared(self):
        other = QUERIES_RESULTS.replace("get:exit\texit\t*\tr\t1\t0\tMNULL=S0",
                                        "get:exit\texit\t*\tr\t1\t0\tMNULL=S0,1")
        summary, details, _ = self.compare(QUERIES_RESULTS, other)
        self.assertEqual(summary.get("wider"), "1")
        self.assertIn(("get", "get:exit", "exit", "*", "r", "wider",
                       "MNULL=S0", "MNULL=S0,1"), details)
        missing = QUERIES_RESULTS.replace(
            "answer\tget\tget:exit\texit\t*\tr\t1\t0\tMNULL=S0\n", "")
        missing = missing.replace("done\t3", "done\t2")
        summary, _, _ = self.compare(QUERIES_RESULTS, missing)
        self.assertEqual(summary.get("unavailable_b_missing"), "1")

    def test_statements_reached_in_one_run_are_listed(self):
        other = QUERIES_RESULTS + "reach\tget\tget:11:0\n"
        _, _, reach = self.compare(QUERIES_RESULTS, other)
        self.assertEqual(reach, [("get", "get:11:0", "B")])

    def test_tables_show_incomplete_comparisons(self):
        with tempfile.TemporaryDirectory() as tmp:
            pair = os.path.join(tmp, "comparisons", "c", "x-vs-y")
            os.makedirs(pair)
            write(os.path.join(pair, "pair.tsv"),
                  "case\tc\nbaseline\tx\ncandidate\ty\n")
            write(os.path.join(pair, "queries-summary.tsv"),
                  "queries\t1\ncomplete_a\tcomplete\n"
                  "complete_b\tincomplete: no done line\n"
                  "comparison\tincomplete\n")
            for mode in ("x", "y"):
                run = os.path.join(tmp, "runs", "c", mode)
                os.makedirs(run)
                write(os.path.join(run, "run.tsv"),
                      "case\tc\nmode\t%s\noutcome\tcompleted\n" % mode)
            with contextlib.redirect_stdout(io.StringIO()):
                campaign.main(["tables", tmp])
            with open(os.path.join(tmp, "tables", "queries.tsv")) as f:
                rows = list(csv.DictReader(f, delimiter="\t"))
            with open(os.path.join(tmp, "tables", "tables.md")) as f:
                md = f.read()
        self.assertEqual(rows[0]["comparison"], "incomplete")
        self.assertEqual(rows[0]["complete_b"], "incomplete: no done line")
        self.assertEqual(rows[0]["both_completed"], "True")
        self.assertIn("Pairs: 1, compared: 1, with both runs completed: 1",
                      md)


class MixedForms(unittest.TestCase):
    """H4: inclusion of mixed numeric forms and top answers."""

    def test_mixed_numeric_forms(self):
        inc = lambda a, b: campaign.ival_included(campaign.parse_ival(a),
                                                  campaign.parse_ival(b))
        self.assertTrue(inc("S0", "F0x0p+0..0x1p+0"))
        self.assertFalse(inc("S0", "F0x1p-1..0x1p+0"))
        self.assertFalse(inc("S0", "F-0x0p+0..-0x0p+0"))
        self.assertFalse(inc("S1", "F0x0p+0..0x1p+0"))
        self.assertTrue(inc("Fnan", "I..%0/1"))
        self.assertTrue(inc("F0x0p+0..0x1p+0", "I..%0/1"))
        self.assertFalse(inc("F0x0p+0..0x1p+0", "I0..%0/1"))
        self.assertFalse(inc("I..%0/1", "F-infinity..infinity;nan"))
        c = campaign.classify
        self.assertEqual(c((1, 0, "MNULL=S0"), (1, 0, "MNULL=F0x0p+0..0x1p+0")),
                         "wider")
        self.assertEqual(c((1, 0, "MNULL=Fnan"), (1, 0, "MNULL=I..%0/1")),
                         "wider")

    def test_constrained_pointer_bases(self):
        self.assertFalse(campaign.is_top_answer("Mx=I..%0/1"))
        self.assertFalse(campaign.is_top_answer("MNULL=I..%0/1;x=I..%0/1"))
        c = campaign.classify
        self.assertEqual(c((1, 0, "Mx=I..%0/1"), (1, 0, "Mx=I..%0/1;y=S0")),
                         "wider")
        self.assertEqual(c((1, 0, "Mx=I..%0/1"), (1, 0, "My=I..%0/1")),
                         "incomparable")

    def test_one_sided_top(self):
        a = "answer\tf\tf:1:0\tbefore\t*\tx\t1\t0\tT\ndone\t1\n"
        b = "done\t0\n"
        summary, _, _ = compare_queries_files(a, b)
        self.assertEqual((summary.get("top_a"), summary.get("top_b")),
                         ("1", "0"))


class Interruption(unittest.TestCase):
    """H5: a log cut after two leaf messages and before their outer."""

    CUT = "\n".join(NESTED_LOG_OFF.strip("\n").split("\n")[:6])

    def test_one_open_chain(self):
        with contextlib.redirect_stderr(io.StringIO()):
            rows = records_of(self.CUT)
        inferred = [r["id"] for r in rows if r.get("inferred")]
        self.assertEqual(inferred,
                         ["main#0", "main#0 > outer@nested.c:13/s12#0"])
        outer = [r for r in rows if r["function"] == "outer"]
        self.assertEqual(len(outer), 1)
        self.assertEqual(outer[0]["children"], 2)

    def test_interrupted_run_does_not_align_completely(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "eva.log")
            out = os.path.join(tmp, "records.jsonl")
            write(path, self.CUT)
            with contextlib.redirect_stderr(io.StringIO()):
                campaign.main(["records", path, out])
            prefix = os.path.join(tmp, "alignment-")
            with contextlib.redirect_stdout(io.StringIO()):
                campaign.main(["align", "--same-numbering", out, out,
                               prefix])
            with open(prefix + "summary.tsv") as f:
                summary = dict(l.rstrip("\n").split("\t", 1) for l in f)
        self.assertEqual(summary.get("records_a"), "2")
        self.assertEqual(summary.get("inferred_a"), "2")
        self.assertEqual(summary.get("aligned"), "2")
        self.assertEqual(summary.get("aligned_with_inferred"), "2")
        self.assertEqual(summary.get("interrupted_a"), "True")
        self.assertEqual(summary.get("complete"), "False")
        self.assertIn("interrupted", summary.get("verdict", ""))
        self.assertIn("structural problems", summary.get("verdict", ""))


WATCHDOG = os.path.join(HERE, "..", "bin", "watchdog.py")


class Watchdog(unittest.TestCase):
    """H6: the watchdog records whether it fired and the wait status."""

    def run_watchdog(self, timeout, command):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "measure")
            code = subprocess.run(
                [sys.executable, "-I", WATCHDOG, path, str(timeout), "1",
                 "-", "--"] + command).returncode
            return code, campaign.read_measure(path)

    def test_exit_124_is_not_a_timeout(self):
        code, m = self.run_watchdog(5, ["sh", "-c", "exit 124"])
        self.assertEqual(code, 124)
        self.assertEqual((m["exit"], m["signal"], m["watchdog"]),
                         ("124", "-", "none"))
        self.assertEqual(
            campaign.classify_outcome(0, 2, m, "", False), "error")

    def test_watchdog_fires(self):
        code, m = self.run_watchdog(0.5, ["sleep", "10"])
        self.assertEqual(code, 128 + 15)
        self.assertEqual((m["signal"], m["watchdog"]), ("15", "term"))
        self.assertEqual(
            campaign.classify_outcome(0, 2, m, "", False), "timeout")

    def test_kill_from_outside_is_killed_cause_unknown(self):
        code, m = self.run_watchdog(5, ["sh", "-c", "kill -9 $$"])
        self.assertEqual(code, 137)
        self.assertEqual((m["signal"], m["watchdog"]), ("9", "none"))
        if m["oom_kill_events"] in ("0", "unreadable"):
            self.assertEqual(
                campaign.classify_outcome(0, 2, m, "", False), "killed")

    def test_out_of_memory_evidence(self):
        m = {"status": "137", "signal": "9", "watchdog": "none",
             "oom_kill_events": "1", "kernel_log_oom": "unreadable"}
        self.assertEqual(campaign.oom_evidence(m, ""), "cgroup oom_kill +1")
        self.assertEqual(campaign.classify_outcome(0, 2, m, "", False), "oom")
        m.update(oom_kill_events="unreadable", kernel_log_oom="yes")
        self.assertEqual(campaign.classify_outcome(0, 2, m, "", False), "oom")
        m.update(kernel_log_oom="unreadable")
        self.assertEqual(campaign.classify_outcome(0, 2, m, "", False),
                         "killed")
        # The counter of the cgroup counts every process of the cgroup: it
        # is evidence only for a SIGKILL that the watchdog did not send.
        done = {"status": "0", "exit": "0", "signal": "-", "watchdog": "none",
                "oom_kill_events": "3", "kernel_log_oom": "-"}
        self.assertEqual(campaign.oom_evidence(done, ""), "")
        self.assertEqual(campaign.classify_outcome(0, 0, done, "", True),
                         "completed")
        failed = dict(done, status="1", exit="1")
        self.assertEqual(campaign.classify_outcome(0, 2, failed, "", False),
                         "error")


BUILD_REFERENCE = os.path.join(HERE, "..", "tools", "build-reference.sh")
ARCHIVE = os.path.join(HERE, "..", "tools", "archive-logs.sh")


class Provenance(unittest.TestCase):
    """H7: a patched reference, without building a binary."""

    def test_patched_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = os.path.join(tmp, "repo")
            os.makedirs(repo)
            git = ["git", "-C", repo, "-c", "user.name=t",
                   "-c", "user.email=t@example.org"]
            subprocess.run(["git", "init", "-q", repo], check=True)
            write(os.path.join(repo, "a.txt"), "one\n")
            subprocess.run(git + ["add", "a.txt"], check=True)
            subprocess.run(git + ["commit", "-q", "-m", "a"], check=True)
            revision = subprocess.run(
                ["git", "-C", repo, "rev-parse", "HEAD"], check=True,
                capture_output=True, text=True).stdout.strip()
            patch = os.path.join(tmp, "fix.patch")
            write(patch, "--- a/a.txt\n+++ b/a.txt\n@@ -1 +1 @@\n-one\n+two\n")
            dest = os.path.join(tmp, "ref")
            env = dict(os.environ, CAMPAIGN_PATCH=patch)
            subprocess.run(["bash", BUILD_REFERENCE, "--no-build", repo,
                            "HEAD", dest], check=True, env=env,
                           stdout=subprocess.DEVNULL)
            with open(os.path.join(dest, "a.txt")) as f:
                self.assertEqual(f.read(), "two\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = campaign.main(["provenance", dest, "reference",
                                      os.path.join(tmp, "out", "patches")])
            self.assertEqual(code, 0)
            fields = out.getvalue().rstrip("\n").split("\t")
            with open(patch, "rb") as f:
                digest = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(fields, [revision, digest,
                                      "provenance/patches/reference.patch"])
            with open(os.path.join(tmp, "out", "patches",
                                   "reference.patch")) as f, \
                    open(patch) as g:
                self.assertEqual(f.read(), g.read())
            # A changed patch no longer matches its recorded SHA-256.
            write(os.path.join(dest, "CAMPAIGN_PATCH.patch"), "changed\n")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(campaign.main(
                    ["provenance", dest, "reference",
                     os.path.join(tmp, "out2")]), 1)

    def test_archive_keeps_the_manifest_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out")
            os.makedirs(os.path.join(out, "provenance"))
            write(os.path.join(out, "provenance", "manifest.tsv"),
                  "case\tcustom\n")
            archive = os.path.join(tmp, "logs.tar.gz")
            subprocess.run(["bash", ARCHIVE, out, archive], check=True,
                           stdout=subprocess.DEVNULL)
            with tarfile.open(archive) as tar:
                names = tar.getnames()
        self.assertIn("logs/provenance/manifest.tsv", names)


class Alarms(unittest.TestCase):
    """H8: directories and duplicate keys of the alarms."""

    def test_duplicate_keys_on_the_command_line(self):
        a = (self.HEADER
             + "/run/a/src/x\tf.c\t3\tf\tmem_access\tValid\tp\n"
             + "/run/a/src/y\tf.c\t3\tf\tmem_access\tValid\tp\n")
        b = (self.HEADER
             + "/run/a/src/x\tf.c\t3\tf\tmem_access\tValid\tp\n"
             + "/run/a/src/y\tf.c\t3\tf\tmem_access\tUnknown\tp\n")
        with tempfile.TemporaryDirectory() as tmp:
            pa, pb = os.path.join(tmp, "a"), os.path.join(tmp, "b")
            write(pa, a)
            write(pb, b)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                campaign.main(["alarms", pa, pb])
        lines = out.getvalue().splitlines()
        self.assertIn("other_status\t1", lines)
        self.assertIn("same_status\t1", lines)

    HEADER = "directory\tfile\tline\tfunction\tproperty kind\tstatus\tproperty\n"

    def test_directory_and_duplicates(self):
        a = (self.HEADER
             + "/run/a/src/x\tf.c\t3\tf\tmem_access\tValid\tp\n"
             + "/run/a/src/y\tf.c\t3\tf\tmem_access\tValid\tp\n"
             + ".\tg.c\t1\tg\tassert\tUnknown\tq\n"
             + ".\tg.c\t1\tg\tassert\tUnknown\tq\n")
        b = (self.HEADER
             + "/run/b/src/x\tf.c\t3\tf\tmem_access\tValid\tp\n"
             + "/run/b/src/y\tf.c\t3\tf\tmem_access\tUnknown\tp\n"
             + ".\tg.c\t1\tg\tassert\tUnknown\tq\n"
             + ".\tg.c\t1\tg\tassert\tValid\tq\n")
        with tempfile.TemporaryDirectory() as tmp:
            pa, pb = os.path.join(tmp, "a"), os.path.join(tmp, "b")
            write(pa, a)
            write(pb, b)
            summary, details = campaign.compare_alarms(
                pa, pb, ["/run/a/src"], ["/run/b/src"])
        self.assertEqual(summary["properties_a"], 4)
        self.assertEqual(summary["duplicate_keys_a"], 1)
        self.assertEqual(summary["same_status"], 1)
        self.assertEqual(summary["other_status"], 2)
        self.assertIn(("${SRC}/y", "f.c", "3", "f", "mem_access", "p",
                       "Valid", "Unknown"), details)
        self.assertIn((".", "g.c", "1", "g", "assert", "q", "Unknown*2",
                       "Unknown,Valid"), details)


class Manifest(unittest.TestCase):
    """H9: the manifest does not depend on the snapshot directory."""

    def manifest(self, tmp, name):
        snapshot = os.path.join(tmp, name)
        base = os.path.join(snapshot, "genann", ".frama-c")
        for step, command in (
                ("parse", "frama-c ../genann.c -cpp-extra-args="
                 "-ffile-prefix-map=%s/genann=. -machdep gcc_x86_64"
                 % snapshot),
                ("eva", "frama-c -eva -eva-slevel 9")):
            os.makedirs(os.path.join(base, "genann." + step))
            write(os.path.join(base, "genann." + step, "command"), command)
        targets = os.path.join(tmp, name + ".txt")
        write(targets, "genann/.frama-c/genann.eva\n")
        trees = os.path.join(tmp, name + "-trees.tsv")
        write(trees, "genann\t" + "1" * 40 + "\n")
        out = os.path.join(tmp, name + ".tsv")
        campaign.main(["manifest", snapshot, targets, "0" * 40, out,
                       "--trees", trees])
        with open(out) as f:
            return f.read()

    def test_two_snapshots_give_one_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = self.manifest(tmp, "s1"), self.manifest(tmp, "s2")
        self.assertEqual(first, second)
        self.assertIn("-ffile-prefix-map=${SNAPSHOT}/genann=.", first)


STAGE1 = os.path.join(HERE, "..", "..", "stage1-pilot.sh")


class Stage1Pilot(unittest.TestCase):
    """H10: stage1-pilot.sh checks its four outcomes."""

    RUNNER = """#!/usr/bin/env bash
for last; do :; done
for id in jsmn/jsmn-main.eva/default jsmn/jsmn-example.eva/default; do
  for mode in nocache cache; do
    mkdir -p "$last/runs/$id/$mode"
    outcome=completed
    if [[ $id/$mode == "$FAIL" ]]; then outcome=error; fi
    printf 'outcome\\t%s\\n' "$outcome" > "$last/runs/$id/$mode/run.tsv"
  done
done
"""

    def run_pilot(self, fail):
        with tempfile.TemporaryDirectory() as tmp:
            runner = os.path.join(tmp, "runner.sh")
            write(runner, self.RUNNER)
            env = dict(os.environ, CAMPAIGN_RUNNER=runner, FAIL=fail)
            return subprocess.run(
                ["bash", STAGE1, os.path.join(tmp, "out")], env=env,
                stderr=subprocess.PIPE, text=True)

    def test_outcomes(self):
        self.assertEqual(self.run_pilot("").returncode, 0)
        failed = self.run_pilot("jsmn/jsmn-example.eva/default/cache")
        self.assertEqual(failed.returncode, 1)
        self.assertIn("jsmn/jsmn-example.eva/default cache: outcome error",
                      failed.stderr)

if __name__ == "__main__":
    unittest.main()
