"""Unit tests of the two sources of the activity tables of
campaign/tools/campaign.py: the rows of the statistics file and the
disposition lines of the Eva log, and of the summaries that the comparison
tables read.

A counter is a number only when the statistics file holds its row; what the
log shows is counted apart, under its own names. The tests build run
directories and assert the cells of the tables that `campaign.py tables`
writes from them.

Run from the root of the repository:
  python3 -I -m unittest discover -s campaign/tests -v
"""

import contextlib
import csv
import gzip
import importlib.util
import io
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location(
    "campaign", os.path.join(HERE, "..", "tools", "campaign.py"))
campaign = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(campaign)

FAMILIES = "builtin,memexec,supplied,collector,producer"
BANNER = "[eva] Analyzing a complete application starting at main\n"

# The rows that the pinned analyzer writes at every export, whatever the
# analysis did (README, Counters and dispositions).
ALWAYS = ("alarm-count\t\t\t0\n"
          "analysis-time\t\t\t0.000504\n"
          "fun-coverage\t\t\t0.333333333333\n"
          "memory-usage\t\t\t39152\n"
          "stmt-coverage\t\t\t1.\n")


def export(rows=""):
    """A statistics file as the analyzer exports it: the given rows and the
    rows of every export, sorted by name, stmt-coverage last."""
    lines = (rows + ALWAYS).splitlines(keepends=True)
    return "".join(sorted(lines, key=lambda line: line.split("\t")[0]))


# minimal.c of the fifth review of issue #54: main calls f once. Its log
# under -eva-memexec -eva-msg-key cache,callstacks, with the collector.
MINIMAL_LOG = BANNER + """[eva:cache] minimal.c:3:
  call to f: lookup: no-candidate; execution: analysed; storage: stored (entry 1); collector: would-store
  stack: f :: minimal.c:3 (stmt 6) <- main
[eva:cache]
  call to main: lookup: no-candidate; execution: analysed; storage: stored (entry 2); collector: refused (sweep)
  stack: main
[eva] ====== VALUES COMPUTED ======
"""
# The same analysis started from a session saved with the collector
# disabled: the disposition lines have no collector field.
LOADED_LOG = MINIMAL_LOG.replace("; collector: would-store", "") \
                        .replace("; collector: refused (sweep)", "")
# The statistics of that analysis: the two entries stored.
LOADED_STATS = export("memexec-misses\tf\t\t1\n"
                      "memexec-misses\tmain\t\t1\n"
                      "memexec-stored\tf\t\t1\n"
                      "memexec-stored\tmain\t\t1\n")
# The statistics that a later analysis of the same invocation wrote, with
# memexec and the collector disabled and nothing printed: no cache row.
SILENT_STATS = export("builtin-applied-strlen\tstrlen\t\t9\n")
# Entries supplied by a test module: three calls refused, three candidates
# rejected, and a statistics file that holds one of these counters only.
SUPPLIED_LOG = BANNER + """
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
# A log with a hit, and its statistics.
HIT_LOG = BANNER + """[eva:cache] nested.c:9:
  call to leaf: lookup: no-candidate; execution: analysed; storage: stored (entry 1); collector: would-store
  stack: leaf :: nested.c:9 (stmt 5) <- main
[eva:cache] nested.c:10:
  call to leaf: lookup: hit (entry 1); execution: not-analysed; storage: none
  stack: leaf :: nested.c:10 (stmt 6) <- main
[eva:cache]
  call to main: lookup: no-candidate; execution: analysed; storage: refused (not-cacheable); collector: refused (sweep)
  stack: main
"""
HIT_STATS = export("collector-refused-sweep\tmain\t\t1\n"
                   "collector-would-store\tleaf\t\t1\n"
                   "memexec-hits\tleaf\t\t1\n"
                   "memexec-misses\tleaf\t\t1\n"
                   "memexec-misses\tmain\t\t1\n"
                   "memexec-refused-not-cacheable\tmain\t\t1\n"
                   "memexec-stored\tleaf\t\t1\n")

STATISTICS_CELLS = (
    ("activity", ("hits", "misses", "stored", "refused",
                  "refused_by_reason", "allocation_and_release",
                  "in_set_a")),
    ("collector", ("collector_would_store", "collector_refused",
                   "collector_refused_by_reason", "producer_stored",
                   "producer_refused", "producer_refused_by_reason",
                   "supplied_hits", "supplied_rejected", "supplied_refused",
                   "supplied_rejected_by_reason",
                   "supplied_refused_by_reason")))


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "wt") as f:
        f.write(text)


def main(args):
    """Runs campaign.py in this process: (exit code, output, error
    output)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = campaign.main(args)
    return code, out.getvalue(), err.getvalue()


def add_run(root, case="c", mode="cache", stats=None, log=None, fields=None,
            files=None):
    """A run directory as the runner leaves it: run.tsv, the statistics
    file, the Eva log and the records derived from it, compressed, and the
    given files."""
    run = os.path.join(root, "runs", case, mode)
    values = {"case": case, "mode": mode, "flag": "-eva-memexec",
              "extra_eva_flags": "-", "outcome": "completed",
              "counter_families": FAMILIES}
    values.update(fields or {})
    write(os.path.join(run, "run.tsv"),
          "".join("%s\t%s\n" % kv for kv in values.items()
                  if kv[1] is not None))
    if stats is not None:
        write(os.path.join(run, "eva-stats.csv"), stats)
    if log is not None:
        write(os.path.join(run, "eva.log"), log)
        main(["records", os.path.join(run, "eva.log"),
              os.path.join(run, "records.jsonl")])
        for name in ("eva.log", "records.jsonl"):
            with open(os.path.join(run, name)) as f:
                write(os.path.join(run, name + ".gz"), f.read())
            os.remove(os.path.join(run, name))
    for name, text in (files or {}).items():
        write(os.path.join(run, name), text)
    return run


class Result:
    """The tables written by `campaign.py tables` for a directory."""

    def __init__(self, root, *options):
        self.code, self.md, self.err = main(["tables", root] + list(options))
        self.tables = {}
        directory = os.path.join(root, "tables")
        for name in os.listdir(directory):
            if name.endswith(".tsv"):
                with open(os.path.join(directory, name), newline="") as f:
                    self.tables[name[:-4]] = list(
                        csv.DictReader(f, delimiter="\t"))

    def row(self, table, index=0):
        if table not in self.tables:
            raise AssertionError("no table %s.tsv" % table)
        return self.tables[table][index]


def tables_of_run(*options, **run):
    with tempfile.TemporaryDirectory() as tmp:
        add_run(tmp, **run)
        return Result(tmp, *options)


class RemovedInferences(unittest.TestCase):
    """The witnesses of the fifth review of issue #54. In each, the recorded
    command, the mode, the families of the binary and the log all describe
    an analysis with memexec and the collector, and the statistics file has
    no row of the counters: every one of those cells is -, never 0."""

    def assert_cells(self, result, expected, table):
        row = result.row(table)
        found = {k: row.get(k) for k in expected}
        self.assertEqual(found, expected)

    def assert_no_cache_counter(self, result):
        """Every cell of the cache counters and of set A is -."""
        self.assertEqual(result.code, 0)
        for table, columns in STATISTICS_CELLS:
            self.assert_cells(result, {k: "-" for k in columns}, table)

    def assert_log(self, result, **expected):
        self.assert_cells(result, {k: str(v) for k, v in expected.items()},
                          "log")

    def test_command_with_a_lost_argument_boundary(self):
        # Finding 1. The operand of -ocode ended with a backslash; the
        # recorded command joins it to -then, which hides the second stage,
        # the one that wrote the statistics.
        command = ("frama-c-measure -eva -eva-slevel 300 -eva-memexec "
                   "-eva-msg-key=+cache,+callstacks -load "
                   "x.parse/framac.sav -ocode unused\\ -then -eva "
                   "-eva-no-cache-collect -eva-no-memexec -eva-verbose 0\n")
        result = tables_of_run(stats=SILENT_STATS, log=MINIMAL_LOG,
                               files={"command": command})
        self.assert_no_cache_counter(result)
        # What the log shows stays in the table of the log, and the two
        # sources are said to disagree.
        self.assert_log(result, analysis_starts=1, disposition_lines=2,
                        lookup_hit=0, storage_stored=2,
                        collector_would_store=1, collector_refused=1)
        self.assertEqual(
            result.row("log")["sources"],
            'disagree: "collector: refused (sweep)" log 1, statistics -; '
            '"collector: would-store" log 1, statistics -; '
            '"storage: stored" log 2, statistics -')

    def test_options_outside_the_recorded_command(self):
        # Finding 2. FRAMAC_DEVONLY_OPTIONS_POST appends a silent stage, and
        # a module loaded with -load-module runs Eva again: one analysis is
        # logged, another one wrote the statistics, and the command records
        # neither.
        for command in (
                "frama-c -eva minimal.c -eva-memexec -eva-msg-key "
                "cache,callstacks -eva-statistics-file eva-stats.csv\n",
                "frama-c -eva minimal.c -eva-memexec -eva-msg-key "
                "cache,callstacks -eva-statistics-file eva-stats.csv "
                "-load-module ./second_stage.cmxs\n"):
            with self.subTest(command=command):
                result = tables_of_run(stats=export(), log=MINIMAL_LOG,
                                       files={"command": command})
                self.assert_no_cache_counter(result)
                self.assert_log(result, analysis_starts=1, storage_stored=2)
                self.assertTrue(
                    result.row("log")["sources"].startswith("disagree: "))

    def test_options_of_a_loaded_session(self):
        # Finding 2. The session loaded with -load had the collector
        # disabled: the command does not say so. The memexec rows are
        # numbers; the collector and the producer have no row.
        command = ("frama-c -load parsed.sav -eva -eva-memexec -eva-msg-key "
                   "cache,callstacks -eva-statistics-file eva-stats.csv\n")
        result = tables_of_run(stats=LOADED_STATS, log=LOADED_LOG,
                               files={"command": command})
        self.assert_cells(result, {
            "collector_would_store": "-", "collector_refused": "-",
            "collector_refused_by_reason": "-", "producer_stored": "-",
            "producer_refused": "-", "producer_refused_by_reason": "-"},
                          "collector")
        self.assert_cells(result, {
            "hits": "-", "misses": "2", "stored": "2", "refused": "-",
            "refused_by_reason": "-", "in_set_a": "-"}, "activity")
        # The log has no collector field: no count of it, not a zero.
        self.assert_log(result, lookup_hit=0, storage_stored=2,
                        collector_would_store="-", collector_refused="-",
                        producer_stored="-",
                        sources="agree on 1 kind")

    def test_missing_command_file(self):
        # Finding 3. Without the command of the analyzer, neither the Make
        # invocation nor the flags of the mode stand for it.
        make = ("make -C runs/jsmn/jsmn-example.eva/default/cache/src/jsmn/"
                ".frama-c -f GNUmakefile -f runs/jsmn/jsmn-example.eva/"
                "default/cache/mode.mk FRAMAC=campaign/bin/frama-c-measure "
                "jsmn-example.eva \n")
        for files in ({"eva-command": make}, {}):
            with self.subTest(files=sorted(files)):
                result = tables_of_run(stats=SILENT_STATS, log=MINIMAL_LOG,
                                       files=files)
                self.assert_no_cache_counter(result)
                self.assert_log(result, analysis_starts=1, storage_stored=2)

    def test_one_row_of_a_family(self):
        # Finding 4. One counter of the supplied entries has a row: the
        # others are not zero for that, and the log shows three refusals.
        result = tables_of_run(
            stats=export("cache-rejected-product\tstep\t\t1\n"),
            log=SUPPLIED_LOG,
            files={"command": "frama-c -eva -eva-memexec\n"})
        self.assert_cells(result, {
            "supplied_hits": "-", "supplied_rejected": "1",
            "supplied_rejected_by_reason": "product=1",
            "supplied_refused": "-", "supplied_refused_by_reason": "-",
            "collector_would_store": "-", "collector_refused": "-"},
                          "collector")
        self.assert_log(result, lookup_rejected=3,
                        lookup_rejected_by_reason="product=3",
                        storage_refused=3,
                        storage_refused_by_reason="supplied-only=3",
                        collector_would_store=0, collector_refused=3)
        # Both numbers are printed, and neither is chosen.
        self.assertEqual(
            result.row("log")["sources"],
            'disagree: "collector: refused (builtin)" log 3, statistics -; '
            '"lookup: rejected (product)" log 3, statistics 1; '
            '"storage: refused (supplied-only)" log 3, statistics -')

    def test_one_row_of_the_memexec_family(self):
        # The same for memexec: stored entries do not make a zero of the
        # hits, nor of the refusals.
        result = tables_of_run(stats=LOADED_STATS, log=LOADED_LOG)
        self.assert_cells(result, {"hits": "-", "misses": "2", "stored": "2",
                                   "refused": "-", "refused_by_reason": "-"},
                          "activity")

    def test_rows_of_one_function(self):
        # The same per function: a function with a row of one counter has
        # no zero of the others.
        result = tables_of_run(stats=HIT_STATS, log=HIT_LOG)
        rows = {r["function"]: r for r in result.tables["functions"]}
        self.assertEqual(
            [rows["leaf"][k] for k in ("hits", "misses", "stored", "refused",
                                       "collector_would_store",
                                       "collector_refused")],
            ["1", "1", "1", "-", "1", "-"])
        self.assertEqual(
            [rows["main"][k] for k in ("hits", "misses", "stored", "refused",
                                       "collector_would_store",
                                       "collector_refused")],
            ["-", "1", "-", "1", "-", "1"])

    def test_no_option_makes_a_zero(self):
        # The commands, flags and family records of the earlier reviews: a
        # statistics file without cache rows gives no zero under any.
        commands = (
            "frama-c -eva -eva-memexec\n",
            "frama-c -eva -eva-no-memexec\n",
            "frama-c -eva -eva-no-cache-collect -eva-cache-collect\n",
            "frama-c -eva -eva-memexec -then -eva-no-memexec\n",
            "frama-c -eva -eva-memexec -then-last -print\n",
            "frama-c -eva -eva-memexec -then-replace -print\n",
            "frama-c -eva -then-on p -eva\n",
            "frama-c -load framac.sav -then -eva -eva-no-cache-collect "
            "-eva-no-memexec -eva-verbose 0\n",
            "frama-c -eva -eva-memexec -commands-file cmds\n",
            None)
        for command in commands:
            for families in (FAMILIES, "builtin,collector,producer", None):
                for log in (MINIMAL_LOG, None):
                    with self.subTest(command=command, families=families,
                                      log=log is not None):
                        result = tables_of_run(
                            stats=export(), log=log,
                            fields={"counter_families": families},
                            files={"command": command} if command else {})
                        self.assert_no_cache_counter(result)

    def test_counts_command(self):
        # The subcommand prints the same cells, without any option that
        # names families or flags.
        with tempfile.TemporaryDirectory() as tmp:
            stats = os.path.join(tmp, "eva-stats.csv")
            log = os.path.join(tmp, "eva.log")
            write(stats, SILENT_STATS)
            write(log, MINIMAL_LOG)
            code, out, _ = main(["counts", stats, "--log", log])
        cells = dict(line.split("\t") for line in out.splitlines())
        self.assertEqual(code, 0)
        self.assertEqual((cells["hits"], cells["stored"],
                          cells["collector_would_store"],
                          cells["producer_stored"], cells["in_set_a"]),
                         ("-",) * 5)
        self.assertEqual((cells["export_rows"],
                          cells["allocation_and_release_rows"]), ("6", "0"))
        # The counts of the log have names of their own.
        self.assertEqual((cells["log_analysis_starts"],
                          cells["log_storage_stored"],
                          cells["log_collector_would_store"]),
                         ("1", "2", "1"))
        self.assertEqual(len(cells), len(out.splitlines()))
        self.assertTrue(cells["sources"].startswith("disagree: "))


class StatisticsRows(unittest.TestCase):
    """A number is the sum of the rows of its counter in a complete export
    of the analyzer."""

    def test_rows_are_numbers(self):
        result = tables_of_run(stats=HIT_STATS, log=HIT_LOG)
        row = result.row("activity")
        self.assertEqual(
            [row[k] for k in ("export_rows", "hits", "misses", "stored",
                              "refused", "refused_by_reason")],
            ["12", "1", "2", "1", "1", "not-cacheable=1"])
        row = result.row("collector")
        self.assertEqual(
            [row[k] for k in ("collector_would_store", "collector_refused",
                              "collector_refused_by_reason")],
            ["1", "1", "sweep=1"])

    def test_a_row_that_holds_zero_is_a_zero(self):
        # No analyzer of the campaign writes such a row; if one did, the
        # row would count.
        result = tables_of_run(stats=export("memexec-hits\tf\t\t0\n"))
        self.assertEqual(result.row("activity")["hits"], "0")
        self.assertEqual(result.row("activity")["misses"], "-")

    def test_every_family(self):
        stats = export(
            "cache-hits\tstep\t\t1\ncache-hits\ttwice\t\t2\n"
            "cache-produced\ttwice\t\t1\n"
            "cache-production-refused-builtin\tmain\t\t4\n"
            "cache-refused-supplied-only\tplain\t\t2\n"
            "cache-refused-supplied-only\tmain\t\t3\n"
            "cache-rejected-key-differs\tstep\t\t2\n"
            "cache-rejected-product\tstep\t\t1\n"
            "collector-refused-builtin\tmain\t\t4\n"
            "collector-would-store\ttwice\t\t1\n")
        row = tables_of_run(stats=stats).row("collector")
        self.assertEqual(
            {k: row[k] for k in dict(STATISTICS_CELLS)["collector"]},
            {"collector_would_store": "1", "collector_refused": "4",
             "collector_refused_by_reason": "builtin=4",
             "producer_stored": "1", "producer_refused": "4",
             "producer_refused_by_reason": "builtin=4",
             "supplied_hits": "3", "supplied_rejected": "3",
             "supplied_refused": "5",
             "supplied_rejected_by_reason": "key-differs=2,product=1",
             "supplied_refused_by_reason": "supplied-only=5"})

    def test_rows_of_other_counters_are_not_read(self):
        stats = export("memexec-collector-swept\tf\t\t7\n"
                       "memexec-hits\tf\t\t3\n")
        row = tables_of_run(stats=stats).row("activity")
        self.assertEqual((row["hits"], row["misses"], row["refused"]),
                         ("3", "-", "-"))

    def test_a_file_that_is_not_a_complete_export(self):
        # The analyzer writes the rows sorted by name and stmt-coverage
        # last. A file that is empty, cut, without that row, out of order
        # or with a row that is not a count gives no cell: its other rows
        # are not evidence that a counter has no row.
        whole = export("memexec-hits\tf\t\t3\n")
        cases = {
            "missing": None,
            "empty": "",
            "the rows of a family alone": "memexec-hits\tf\t\t3\n",
            "cut in its last line": whole[:-1],
            "cut before its last row": whole[:whole.index("stmt-coverage")],
            "two exports": whole + whole,
            "not sorted": export() + "memexec-hits\tf\t\t3\n",
            "a count that is not a decimal":
                export("memexec-hits\tf\t\tmany\n"),
            "a negative count": export("memexec-hits\tf\t\t-1\n"),
            "a count without a function": export("memexec-hits\t\t\t3\n"),
            "a line of three fields": export("memexec-hits\tf\t3\n"),
        }
        for name, text in cases.items():
            with self.subTest(case=name):
                result = tables_of_run(stats=text)
                row = result.row("activity")
                self.assertEqual(
                    [row[k] for k in ("export_rows", "hits",
                                      "allocation_and_release_rows",
                                      "in_set_a")], ["-"] * 4)
                self.assertEqual(result.tables["functions"], [])
                if text is not None:
                    self.assertIn("its counters are not read", result.err)

    def test_set_a_needs_a_row(self):
        # The allocation and release builtins: without a row there is no
        # sum and no membership, only the number of such rows, 0, among
        # the rows of the file.
        with tempfile.TemporaryDirectory() as tmp:
            recorded = os.path.join(tmp, "recorded.tsv")
            write(recorded, "target\tin_A\njsmn/a.eva\tTrue\n"
                  "jsmn/b.eva\tFalse\njsmn/c.eva\tTrue\n")
            add_run(tmp, case="jsmn/a.eva/default",
                    stats=export("builtin-applied-strlen\tstrlen\t\t9\n"))
            add_run(tmp, case="jsmn/b.eva/default", stats=export(
                "builtin-applied-Frama_C_free\tmy_free\t\t1\n"
                "builtin-applied-malloc\tmalloc\t\t2\n"))
            add_run(tmp, case="jsmn/c.eva/default",
                    stats=export("builtin-applied-malloc\tmalloc\t\t2\n"))
            add_run(tmp, case="jsmn/d.eva/default",
                    stats=export("builtin-applied-malloc\tmalloc\t\t0\n"))
            result = Result(tmp, "--recorded-set-a", recorded)
        columns = ("export_rows", "allocation_and_release_rows",
                   "allocation_and_release", "in_set_a",
                   "recorded_in_set_a", "agrees")
        self.assertEqual(
            [[r[k] for k in columns] for r in result.tables["activity"]],
            [["6", "0", "-", "-", "True", "-"],
             ["7", "2", "3", "False", "False", "yes"],
             ["6", "1", "2", "False", "True", "NO"],
             ["6", "1", "0", "True", "-", "-"]])

    def test_prose_of_the_tables(self):
        result = tables_of_run(stats=export(), log=MINIMAL_LOG)
        self.assertIn("it is never a zero", result.md)
        self.assertIn("a cell is 0 only when a row holds 0", result.md)
        self.assertNotIn("was not measured", result.md)
        self.assertNotIn("which no campaign run supplies", result.md)
        self.assertIn("## Dispositions counted in the Eva log (log-derived)",
                      result.md)
        self.assertIn("there is no such line among the `disposition_lines` "
                      "disposition lines of this log", result.md)


class LogCounts(unittest.TestCase):
    """What the log shows: counts of its disposition lines by kind, next
    to the number of analysis starts of that log."""

    COUNTS = ("analysis_starts", "disposition_lines", "lookup_hit",
              "lookup_no_candidate", "lookup_rejected",
              "lookup_rejected_by_reason", "storage_stored", "storage_none",
              "storage_refused", "storage_refused_by_reason",
              "collector_would_store", "collector_refused",
              "collector_refused_by_reason", "producer_stored",
              "producer_refused", "producer_refused_by_reason", "log_note")

    def log_row(self, log, stats=None):
        row = tables_of_run(stats=stats, log=log).row("log")
        self.assertEqual(list(row)[2:], list(self.COUNTS) + ["sources"])
        return row

    def test_counts_by_kind(self):
        row = self.log_row(HIT_LOG, HIT_STATS)
        self.assertEqual(
            [row[k] for k in self.COUNTS],
            ["1", "3", "1", "2", "0", "none", "1", "1", "1",
             "not-cacheable=1", "1", "1", "sweep=1", "-", "-", "-", "-"])
        self.assertEqual(row["sources"], "agree on 5 kinds")

    def test_a_zero_is_no_such_line_among_the_lines(self):
        # Caching disabled: three lines, none with a hit. The statistics
        # have no memexec row, and stay -.
        log = MINIMAL_LOG.replace("stored (entry 1)", "refused (disabled)") \
                         .replace("stored (entry 2)", "refused (disabled)")
        stats = export("collector-refused-sweep\tmain\t\t1\n"
                       "collector-would-store\tf\t\t1\n")
        result = tables_of_run(stats=stats, log=log)
        row = result.row("log")
        self.assertEqual(
            [row[k] for k in ("analysis_starts", "disposition_lines",
                              "lookup_hit", "lookup_no_candidate",
                              "storage_stored", "storage_refused",
                              "storage_refused_by_reason", "sources")],
            ["1", "2", "0", "2", "0", "2", "disabled=2",
             "agree on 2 kinds"])
        self.assertEqual(result.row("activity")["hits"], "-")
        self.assertEqual(result.row("activity")["stored"], "-")

    def test_no_disposition_line(self):
        for log in (BANNER, BANNER + "[eva] done\n"):
            row = self.log_row(log, HIT_STATS)
            self.assertEqual(
                [row[k] for k in self.COUNTS],
                ["1", "0"] + ["-"] * 14 + ["no disposition line"])
            self.assertEqual(row["sources"], "-")

    def test_no_log(self):
        row = self.log_row(None, HIT_STATS)
        self.assertEqual([row[k] for k in self.COUNTS],
                         ["-"] * 16 + ["no log"])

    def test_more_than_one_analysis_start(self):
        # Two analyses printed their lines: the counts of the log are not
        # those of one analysis.
        result = tables_of_run(stats=HIT_STATS, log=HIT_LOG + MINIMAL_LOG)
        row = result.row("log")
        self.assertEqual(
            [row[k] for k in self.COUNTS],
            ["2", "5"] + ["-"] * 14 + ["2 analysis starts"])
        self.assertEqual(row["sources"], "-")
        # The rows of the statistics file stay what they are.
        self.assertEqual(result.row("activity")["hits"], "1")

    def test_no_analysis_start(self):
        row = self.log_row(HIT_LOG[len(BANNER):], HIT_STATS)
        self.assertEqual(
            [row[k] for k in self.COUNTS],
            ["0", "3"] + ["-"] * 14 + ["0 analysis starts"])

    def test_a_cache_message_of_another_form(self):
        # A line cut in its fields, a field that the tool does not know, a
        # storage of another form: the log shows no count.
        for old, new in (
                ("storage: none", "storage: no"),
                ("storage: none", "storage: none; future: yes"),
                ("storage: stored (entry 1)", "storage: stored"),
                ("execution: not-analysed", "execution: skipped"),
                ("lookup: hit (entry 1)", "lookup: hit")):
            with self.subTest(new=new):
                row = self.log_row(HIT_LOG.replace(old, new), HIT_STATS)
                self.assertEqual(
                    [row[k] for k in self.COUNTS],
                    ["1", "2"] + ["-"] * 14
                    + ["1 cache message(s) of another form than a "
                       "disposition line"])
                self.assertEqual(row["sources"], "-")

    def test_producer_field(self):
        # The producer field is printed under a category of its own: a log
        # without it shows no count of the producer, not a zero.
        log = HIT_LOG.replace(
            "collector: would-store",
            "collector: would-store; producer: stored (entry 1)").replace(
                "collector: refused (sweep)",
                "collector: refused (sweep); producer: refused (sweep)")
        stats = HIT_STATS.replace(
            "collector-refused-sweep",
            "cache-produced\tleaf\t\t1\n"
            "cache-production-refused-sweep\tmain\t\t1\n"
            "collector-refused-sweep")
        row = self.log_row(log, stats)
        self.assertEqual(
            [row[k] for k in ("producer_stored", "producer_refused",
                              "producer_refused_by_reason", "sources")],
            ["1", "1", "sweep=1", "agree on 7 kinds"])
        # Without the field in the log, the rows of the producer are not
        # compared with anything.
        row = self.log_row(HIT_LOG, stats)
        self.assertEqual(
            [row[k] for k in ("producer_stored", "producer_refused",
                              "sources")], ["-", "-", "agree on 5 kinds"])

    def test_sources_are_compared_and_never_combined(self):
        # A row without a line, a line without a row, two different
        # numbers: each is reported, and each table keeps its own number.
        stats = HIT_STATS.replace("memexec-hits\tleaf\t\t1",
                                  "memexec-hits\tleaf\t\t4")
        result = tables_of_run(stats=stats, log=HIT_LOG)
        self.assertEqual(result.row("activity")["hits"], "4")
        self.assertEqual(result.row("log")["lookup_hit"], "1")
        self.assertEqual(result.row("log")["sources"],
                         'disagree: "lookup: hit" log 1, statistics 4')
        stats = HIT_STATS.replace("memexec-hits\tleaf\t\t1\n", "")
        result = tables_of_run(stats=stats, log=HIT_LOG)
        self.assertEqual(result.row("activity")["hits"], "-")
        self.assertEqual(result.row("log")["lookup_hit"], "1")
        self.assertEqual(result.row("log")["sources"],
                         'disagree: "lookup: hit" log 1, statistics -')
        log = HIT_LOG.replace("lookup: hit (entry 1); execution: "
                              "not-analysed; storage: none",
                              "lookup: no-candidate; execution: analysed; "
                              "storage: refused (disabled)")
        result = tables_of_run(stats=HIT_STATS, log=log)
        self.assertEqual(result.row("activity")["hits"], "1")
        self.assertEqual(result.row("log")["lookup_hit"], "0")
        self.assertEqual(result.row("log")["sources"],
                         'disagree: "lookup: hit" log 0, statistics 1')

    def test_statistics_that_are_not_an_export_are_not_compared(self):
        row = self.log_row(HIT_LOG, "memexec-hits\tleaf\t\t1\n")
        self.assertEqual((row["lookup_hit"], row["sources"]), ("1", "-"))

    def test_the_log_is_read_not_the_records(self):
        # The records of another log do not stand for the log of the run.
        with tempfile.TemporaryDirectory() as tmp:
            run = add_run(tmp, stats=HIT_STATS, log=HIT_LOG)
            write(os.path.join(run, "eva.log.gz"), BANNER)
            row = Result(tmp).row("log")
        self.assertEqual((row["disposition_lines"], row["lookup_hit"],
                          row["log_note"]),
                         ("0", "-", "no disposition line"))


class Summaries(unittest.TestCase):
    """A comparison table reads a summary only when the file is one that
    the tool writes, whole: a field of a partial file is not a result."""

    CASE = "fixtures/nested-hit.c/default"
    HISTORICAL = ("PASS nested-hit: two runs of the same binary align "
                  "completely")

    def summary(self, *options):
        """The alignment summary that the tool writes for two runs of one
        log, both completed unless [options] say otherwise."""
        with tempfile.TemporaryDirectory() as tmp:
            log = os.path.join(tmp, "eva.log")
            records = os.path.join(tmp, "records.jsonl")
            write(log, HIT_LOG)
            main(["records", log, records])
            arguments = {"--ast-a": "0" * 64, "--ast-b": "0" * 64,
                         "--pp-a": "a" * 64 + ":" + "b" * 64,
                         "--pp-b": "a" * 64 + ":" + "b" * 64,
                         "--outcome-a": "completed",
                         "--outcome-b": "completed",
                         "--entry-point": "main"}
            arguments.update(zip(options[::2], options[1::2]))
            main(["align"] + [x for kv in arguments.items() for x in kv]
                 + [records, records, os.path.join(tmp, "alignment-")])
            with open(os.path.join(tmp, "alignment-summary.tsv")) as f:
                return f.read()

    def tables(self, summary, directory=None, name="alignment", runs=True):
        with tempfile.TemporaryDirectory() as tmp:
            pair = os.path.join(
                tmp, "comparisons",
                directory or os.path.join(self.CASE, "cache-vs-cache.2"))
            write(os.path.join(pair, "pair.tsv"),
                  "case\t%s\nbaseline\tcache\ncandidate\tcache.2\n"
                  % self.CASE)
            if summary is not None:
                write(os.path.join(pair, name + "-summary.tsv"), summary)
            write(os.path.join(tmp, "fixtures.txt"), self.HISTORICAL + "\n")
            if runs:
                for mode in ("cache", "cache.2"):
                    add_run(tmp, case=self.CASE, mode=mode)
            return Result(tmp)

    def assert_unavailable(self, result, table="alignment"):
        self.assertEqual(result.code, 0)
        self.assertIn("Current alignment unavailable", result.md)
        self.assertNotIn("complete=False", result.md)
        self.assertNotIn("complete=True", result.md)
        self.assertNotIn("superseded", result.md)
        for row in result.tables[table]:
            self.assertEqual(
                {k: v for k, v in row.items()
                 if k not in ("case", "A", "B", "both_completed")},
                {k: "-" for k in row
                 if k not in ("case", "A", "B", "both_completed")})

    def test_summary_with_the_numbering_alone(self):
        # Finding 5 of the fifth review: with numbering=same alone, the
        # tables printed complete=False and called the recorded result
        # superseded, while alignment.tsv showed -.
        result = self.tables("numbering\tsame\n")
        self.assert_unavailable(result)
        self.assertEqual(result.row("alignment")["numbering"], "-")
        self.assertIn("with a valid summary: 0", result.md)
        self.assertIn("not a valid summary", result.err)

    def test_validated_values(self):
        whole = self.summary()
        result = self.tables(whole)
        self.assertIn("is `complete=True`", result.md)
        self.assertEqual((result.row("alignment")["complete"],
                          result.row("alignment")["verdict"]),
                         ("True", "complete"))
        result = self.tables(self.summary("--outcome-b", "timeout"))
        self.assertIn("superseded", result.md)
        self.assertIn("`complete=False`", result.md)
        self.assertIn("0 of 1 alignments with a valid summary are complete",
                      result.md)
        self.assertIn("the verdict `incomplete: outcome of B: timeout`",
                      result.md)
        self.assertEqual(result.row("alignment")["complete"], "False")

    def test_every_field_is_needed_and_checked(self):
        # A summary without one of its fields, with a field that is not a
        # value of its kind, with a line twice or with a line cut is not
        # read at all.
        whole = self.summary("--outcome-b", "timeout")
        lines = whole.splitlines(keepends=True)
        self.assertEqual(len(lines), len(campaign.ALIGNMENT_SUMMARY))
        for index, line in enumerate(lines):
            key = line.split("\t")[0]
            for name, text in (
                    ("without", "".join(lines[:index] + lines[index + 1:])),
                    ("empty", whole.replace(line, key + "\t\n")),
                    ("invalid", whole.replace(line, key + "\tperhaps\n")),
                    ("twice", whole.replace(line, line + line)),
                    ("no value", whole.replace(line, key + "\n"))):
                if name == "invalid" and key in (
                        "entry_point", "outcome_a", "outcome_b", "verdict"):
                    continue  # free text: any word is a value
                with self.subTest(field=key, change=name):
                    self.assert_unavailable(self.tables(text))
        self.assert_unavailable(self.tables(whole[:-1]))
        self.assert_unavailable(self.tables(whole + "later\t1\n"))
        self.assert_unavailable(self.tables(""))
        self.assert_unavailable(self.tables(None))

    def test_verdict_that_its_fields_do_not_allow(self):
        whole = self.summary("--outcome-b", "timeout")
        self.assertIn("complete\tFalse\n", whole)
        self.assert_unavailable(self.tables(
            whole.replace("complete\tFalse\n", "complete\tTrue\n")))
        self.assert_unavailable(self.tables(
            self.summary().replace("complete\tTrue\n", "complete\tFalse\n")))

    def test_pair_that_names_another_directory(self):
        # The directory of the review: comparisons/fixture, whose pair.tsv
        # names another comparison. Its cells would go to that one.
        result = self.tables(self.summary(), directory="fixture")
        self.assertIn("Current alignment unavailable", result.md)
        self.assertEqual(result.tables["alignment"], [])
        self.assertIn("Left out of every table", result.md)
        self.assertIn("`comparisons/fixture`", result.md)
        self.assertIn("left out", result.err)

    def test_other_summaries(self):
        for name, text in (("queries", "queries\t5\nequal\t5\n"
                            "comparison\tcomplete\n"),
                           ("alarms", "properties_a\t3\nsame_status\t3\n")):
            with self.subTest(summary=name):
                result = self.tables(text, name=name)
                row = result.row(name)
                self.assertEqual(
                    {v for k, v in row.items()
                     if k not in ("case", "A", "B", "both_completed")},
                    {"-"})
                self.assertIn("with a valid summary: 0", result.md)

    def test_both_completed_needs_the_two_outcomes(self):
        # Without the run.tsv of a run, or without its outcome, the tables
        # do not say that the runs did not complete.
        whole = self.summary()
        result = self.tables(whole, runs=False)
        self.assertEqual(result.row("alignment")["both_completed"], "-")
        self.assertIn("of which both runs completed: 0", result.md)
        with tempfile.TemporaryDirectory() as tmp:
            pair = os.path.join(tmp, "comparisons", "c", "x-vs-y")
            write(os.path.join(pair, "pair.tsv"),
                  "case\tc\nbaseline\tx\ncandidate\ty\n")
            write(os.path.join(pair, "alignment-summary.tsv"), whole)
            add_run(tmp, mode="x")
            add_run(tmp, mode="y", fields={"outcome": None})
            self.assertEqual(
                Result(tmp).row("alignment")["both_completed"], "-")
            add_run(tmp, mode="y", fields={"outcome": "timeout"})
            self.assertEqual(
                Result(tmp).row("alignment")["both_completed"], "False")
            add_run(tmp, mode="y")
            self.assertEqual(
                Result(tmp).row("alignment")["both_completed"], "True")


class Runs(unittest.TestCase):
    """What a run does not record is not taken from its command or from a
    default."""

    def test_run_that_names_another_directory(self):
        # The files of a run are read in runs/CASE/MODE: a run.tsv copied
        # from another run would give the cells of that directory to it.
        with tempfile.TemporaryDirectory() as tmp:
            add_run(tmp, stats=HIT_STATS, log=HIT_LOG)
            other = add_run(tmp, mode="nocache", stats=export())
            write(os.path.join(other, "run.tsv"),
                  "case\tc\nmode\tcache\noutcome\tcompleted\n")
            result = Result(tmp)
        self.assertEqual([(r["case"], r["mode"])
                          for r in result.tables["activity"]],
                         [("c", "cache")])
        self.assertEqual(result.row("activity")["hits"], "1")
        self.assertIn("`runs/c/nocache`", result.md)

    MEASURE = ("status\t0\nexit\t0\nsignal\t-\nwatchdog\tnone\n"
               "elapsed_s\t0.5\n")

    def recompute(self, run_fields, manifest_entry=None):
        with tempfile.TemporaryDirectory() as tmp:
            fields = {"parse_exit": "0", "make_exit": "0", "outcome": "-"}
            fields.update(run_fields)
            for mode in ("x", "y"):
                run = add_run(tmp, mode=mode, fields=fields)
                write(os.path.join(run, "measure"), self.MEASURE)
                write(os.path.join(run, "eva.log"), HIT_LOG)
            if manifest_entry:
                header = campaign.MANIFEST_HEADER
                row = {"case": "c", "entry_point": manifest_entry}
                write(os.path.join(tmp, "provenance", "manifest.tsv"),
                      "\t".join(header) + "\n"
                      + "\t".join(row.get(c, "-") for c in header) + "\n")
            write(os.path.join(tmp, "comparisons", "c", "x-vs-y",
                               "pair.tsv"),
                  "case\tc\nbaseline\tx\ncandidate\ty\n")
            code, _, _ = main(["recompute", tmp])
            self.assertEqual(code, 0)
            result = Result(tmp)
            return (result.row("outcomes")["outcome"],
                    result.row("alignment")["verdict"])

    def test_entry_point_is_recorded_or_unknown(self):
        # The entry point comes from run.tsv or from the manifest of the
        # campaign. It is not read from the command and has no default: a
        # run without it is not completed, and its alignment says so.
        self.assertEqual(self.recompute({"entry_point": "main"})[0],
                         "completed")
        self.assertEqual(self.recompute({}, manifest_entry="main")[0],
                         "completed")
        self.assertEqual(self.recompute({"entry_point": "other"})[0],
                         "incomplete")
        outcome, verdict = self.recompute({})
        self.assertEqual(outcome, "harness-error")
        self.assertIn("entry point not given", verdict)


if __name__ == "__main__":
    unittest.main()



if __name__ == "__main__":
    unittest.main()
