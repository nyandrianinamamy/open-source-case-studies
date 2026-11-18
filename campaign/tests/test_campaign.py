"""Unit tests of campaign/tools/campaign.py.

Run from the root of the repository:
  python3 -I -m unittest discover -s campaign/tests -v
"""

import importlib.util
import json
import os
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
  stack: leaf :: nested.c:9 <- outer :: nested.c:13 <- main
[eva:alarm] nested.c:9: Warning:
  signed overflow. assert x + 1 <= 2147483647;
  stack: leaf :: nested.c:9 <- outer :: nested.c:13 <- main
[eva:cache] nested.c:9: call to leaf: lookup: hit (entry 1); execution: not-analysed; storage: none
  stack: leaf :: nested.c:9 <-
         outer :: nested.c:13 <-
         main
[eva:cache] nested.c:13:
  call to outer: lookup: no-candidate; execution: analysed; storage: stored (entry 2)
  stack: outer :: nested.c:13 <- main
[eva:cache] nested.c:14:
  call to outer: lookup: hit (entry 2); execution: not-analysed; storage: none
  stack: outer :: nested.c:14 <- main
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
  stack: leaf :: nested.c:9 <- outer :: nested.c:13 <- main
[eva:cache] nested.c:9:
  call to leaf: lookup: no-candidate; execution: analysed; storage: refused (disabled)
  stack: leaf :: nested.c:9 <- outer :: nested.c:13 <- main
[eva:cache] nested.c:13:
  call to outer: lookup: no-candidate; execution: analysed; storage: refused (disabled)
  stack: outer :: nested.c:13 <- main
[eva:cache] nested.c:9:
  call to leaf: lookup: no-candidate; execution: analysed; storage: refused (disabled)
  stack: leaf :: nested.c:9 <- outer :: nested.c:14 <- main
[eva:cache] nested.c:9:
  call to leaf: lookup: no-candidate; execution: analysed; storage: refused (disabled)
  stack: leaf :: nested.c:9 <- outer :: nested.c:14 <- main
[eva:cache] nested.c:14:
  call to outer: lookup: no-candidate; execution: analysed; storage: refused (disabled)
  stack: outer :: nested.c:14 <- main
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
                         [("outer", "nested.c:13"), ("leaf", "nested.c:9")])
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

    def test_other_messages_are_ignored(self):
        lines = log("[eva:cache] not a call\n[eva] call to x: y")
        self.assertEqual(campaign.cache_records(lines), [])

    def test_callstack_hash(self):
        entry, frames = campaign.parse_stack("<Ab12> f :: a.c:1 <- main")
        self.assertEqual((entry, frames), ("main", [("f", "a.c:1")]))


class Tree(unittest.TestCase):

    def test_identities_and_hits(self):
        rows = records_of(NESTED_LOG)
        ids = [r["id"] for r in rows]
        self.assertEqual(ids, [
            "main#0",
            "main#0 > outer@nested.c:13#0",
            "main#0 > outer@nested.c:13#0 > leaf@nested.c:9#0",
            "main#0 > outer@nested.c:13#0 > leaf@nested.c:9#1",
            "main#0 > outer@nested.c:14#0",
        ])
        by_id = {r["id"]: r for r in rows}
        self.assertEqual(
            by_id["main#0 > outer@nested.c:14#0"]["hit_of"],
            "main#0 > outer@nested.c:13#0")
        self.assertEqual(
            by_id["main#0 > outer@nested.c:13#0 > leaf@nested.c:9#1"]
            ["hit_of"],
            "main#0 > outer@nested.c:13#0 > leaf@nested.c:9#0")

    def test_killed_run_gets_open_parents(self):
        # The run stopped inside the second call to outer: its nested call
        # and main never printed their message.
        text = "\n".join(NESTED_LOG_OFF.strip("\n").split("\n")[:12])
        rows = records_of(text)
        by_id = {r["id"]: r for r in rows}
        self.assertIn("main#0", by_id)
        self.assertEqual(by_id["main#0"]["execution"], "open")
        self.assertIn("main#0 > outer@nested.c:14#0 > leaf@nested.c:9#0",
                      by_id)
        self.assertEqual(by_id["main#0 > outer@nested.c:14#0"]["execution"],
                         "open")

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
            ["main#0 > outer@nested.c:14#0 > leaf@nested.c:9#0",
             "main#0 > outer@nested.c:14#0 > leaf@nested.c:9#1"])

    @staticmethod
    def row(id_, parent, seq, function, site, lookup="no-candidate"):
        return {"id": id_, "parent": parent, "seq": seq,
                "function": function, "site": site, "lookup": lookup,
                "execution": "analysed", "storage": "none",
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
                         [("m", "m", "f@a.c:3", 2, 3, 2, 3)])
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
        self.assertTrue(campaign.is_top_answer("Gx"))
        self.assertTrue(campaign.is_top_answer("MNULL=I..%0/1"))
        self.assertFalse(campaign.is_top_answer("MNULL=I0..%0/1"))


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
            summary, details = campaign.compare_queries(a, b)
        self.assertEqual(summary["queries"], 3)
        self.assertEqual(summary["answered_both"], 2)
        self.assertEqual(summary["equal"], 1)
        self.assertEqual(summary["narrower"], 1)
        self.assertEqual(summary["unavailable_b_no-callstack"], 1)


class Outcomes(unittest.TestCase):

    def outcome(self, status, elapsed=1.0, log="", entry=True, make=0,
                parse=0, measured=True):
        measure = ({"status": str(status), "elapsed_s": str(elapsed)}
                   if measured else None)
        return campaign.classify_outcome(parse, make, measure, log, entry,
                                         60.0)

    def test_classes(self):
        self.assertEqual(self.outcome(0), "completed")
        self.assertEqual(self.outcome(0, entry=False), "incomplete")
        self.assertEqual(self.outcome(124, 60.0), "timeout")
        self.assertEqual(self.outcome(137, 120.0), "timeout")
        self.assertEqual(self.outcome(137, 10.0), "killed")
        self.assertEqual(self.outcome(1), "error")
        self.assertEqual(self.outcome(4), "error")
        self.assertEqual(self.outcome(139), "error")
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
        self.assertEqual(rows, [["f", 3, 1, 0, 0], ["g", 0, 2, 0, 1]])

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


if __name__ == "__main__":
    unittest.main()
