#!/usr/bin/env python3
"""Tools of the case-study campaign: records, alignment, queries, tables.

Subcommands:
  records LOG [OUT]          per-call records of one Eva log, as JSON lines
  align A B [OUT_PREFIX]     align the per-call records of two runs
  queries A B [OUT_PREFIX]   compare the state-query answers of two runs
  alarms A B                 compare two alarms.csv files
  counts STATS               builtin applications and cache activity of a run
  families CMXS              counter families of a compiled Eva plugin
  provenance CHECKOUT ROLE DIR  revision and patch of a Frama-C checkout
  tables RUN_DIR             result tables of a campaign output directory
  manifest ...               see manifest --help

Only the Python standard library is used. Run with python3 -I.
"""

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import os
import re
import shlex
import subprocess
import sys
from collections import Counter, OrderedDict, defaultdict


def open_text(path, mode="r"):
    """Opens a text file, compressed with gzip when its name ends in .gz."""
    if path == "-":
        return sys.stdin if "r" in mode else sys.stdout
    if path.endswith(".gz"):
        return gzip.open(path, mode + "t", encoding="utf-8", errors="replace")
    return open(path, mode, encoding="utf-8", errors="replace")


# ----- Log messages ----------------------------------------------------------

HEADER = re.compile(r"^\[([A-Za-z0-9_-]+)(?::([^\]]*))?\] ?(.*)$")


def messages(lines):
    """Yields (plugin, category, text) for each message of a Frama-C log.

    The text is the rest of the header line, followed by each continuation
    line without its two-space indentation. Lines that are neither a header
    nor a continuation end the current message and are ignored."""
    current = None
    for line in lines:
        line = line.rstrip("\n")
        match = HEADER.match(line)
        if match:
            if current:
                yield current[0], current[1], "\n".join(current[2])
            current = (match.group(1), match.group(2) or "", [match.group(3)])
        elif current and line.startswith("  "):
            current[2].append(line[2:])
        elif current and line == "":
            current[2].append("")
        else:
            if current:
                yield current[0], current[1], "\n".join(current[2])
            current = None
    if current:
        yield current[0], current[1], "\n".join(current[2])


def split_top(text, sep="; "):
    """Splits [text] on [sep] outside parentheses and brackets."""
    parts, depth, start, i = [], 0, 0, 0
    while i < len(text):
        c = text[i]
        if c in "([":
            depth += 1
        elif c in ")]":
            depth = max(0, depth - 1)
        elif depth == 0 and text.startswith(sep, i):
            parts.append(text[start:i])
            i += len(sep)
            start = i
            continue
        i += 1
    parts.append(text[start:])
    return parts


def disposition_kind(value):
    """The kind of a disposition: its text before the first space or
    parenthesis, such as hit, no-candidate, stored or refused."""
    match = re.match(r"[^\s(]+", value)
    return match.group(0) if match else value


ENTRY = re.compile(r"\bentry (\d+)")
REJECTED = re.compile(r"^rejected \(entry (\d+): (.*)\)$")
HIT = re.compile(r"^hit \(entry (\d+)\)$")


def parse_lookup(value):
    """Parses a lookup disposition as the sequence of its candidates.

    The lookup prints no-candidate, or the candidates rejected, oldest first,
    as "rejected (entry N: REASON)", followed by "hit (entry N)" when an
    entry is used, separated by ", ". Returns a dictionary with the kind of
    the lookup (hit when an entry is used, rejected when every candidate is
    rejected, no-candidate, or the first word of an unknown form), the
    rejections as [entry, reason] pairs, the entry used, and the parts that
    are not understood, kept verbatim."""
    result = {"kind": "", "rejected": [], "hit": None, "other": []}
    for part in split_top(value.strip(), ", "):
        part = part.strip()
        rejected, hit = REJECTED.match(part), HIT.match(part)
        if part == "no-candidate":
            continue
        if rejected:
            result["rejected"].append([int(rejected.group(1)),
                                       rejected.group(2)])
        elif hit and result["hit"] is None:
            result["hit"] = int(hit.group(1))
        elif part:
            result["other"].append(part)
    if result["hit"] is not None:
        result["kind"] = "hit"
    elif result["other"]:
        result["kind"] = disposition_kind(result["other"][0])
    elif result["rejected"]:
        result["kind"] = "rejected"
    else:
        result["kind"] = "no-candidate" if value.strip() else ""
    return result


# A frame of a printed callstack: the called function, the call site, and
# the number of the call statement, which the cache messages print after
# the call site since issue #54.
FRAME = re.compile(r"^(.*?) :: (.*?)(?: \(stmt (\d+)\))?$")


def parse_stack(text):
    """Parses a printed Eva callstack. Returns (entry point, frames), the
    frames being (called function, call site, statement number or None)
    from the outermost call to the innermost one."""
    text = " ".join(text.split())
    text = re.sub(r"^<[^>]*> ", "", text)  # callstack hash, if printed
    parts = text.split(" <- ")
    frames = []
    for part in parts[:-1]:
        match = FRAME.match(part)
        if not match:
            raise ValueError("malformed callstack frame: %r" % part)
        stmt = int(match.group(3)) if match.group(3) else None
        frames.append((match.group(1), match.group(2), stmt))
    frames.reverse()
    return parts[-1], frames


def parse_cache_message(text):
    """Parses the text of one message of the category cache.

    Returns a dictionary with the location of the call (empty for the entry
    point), the called function, the dispositions in their order (every
    field is kept verbatim, known or not), the callstack and the number of
    the call statement when the callstack gives it, or None when the message
    is not a call disposition."""
    body, _, stack = text.partition("\nstack:")
    flat = " ".join(body.split())
    if flat.startswith("call to "):
        location, rest = "", flat
    else:
        location, sep, rest = flat.partition(": call to ")
        if not sep:
            return None
        rest = "call to " + rest
    head, sep, fields = rest[len("call to "):].partition(": ")
    if not sep:
        return None
    dispositions = OrderedDict()
    for field in split_top(fields):
        name, sep, value = field.partition(": ")
        if not sep:
            name, value = field, ""
        dispositions[name.strip()] = value.strip()
    record = {
        "site": location,
        "function": head,
        "dispositions": dispositions,
        "stmt": None,
    }
    if stack:
        entry, frames = parse_stack(stack)
        record["entry_point"] = entry
        record["frames"] = frames
        if frames:
            record["stmt"] = frames[-1][2]
    return record


def cache_records(lines):
    """The per-call records of a log, in the order of their messages."""
    records = []
    for plugin, category, text in messages(lines):
        if plugin == "eva" and category in ("cache", "cache-producer"):
            record = parse_cache_message(text)
            if record is not None:
                record["seq"] = len(records)
                records.append(record)
    return records


# ----- Call tree and invocation identity -------------------------------------

BODY_EXECUTIONS = ("analysed", "interrupted")


def kinds(record):
    d = record["dispositions"]
    return (parse_lookup(d.get("lookup", ""))["kind"],
            disposition_kind(d.get("execution", "")),
            disposition_kind(d.get("storage", "")))


def frames_key(record):
    return (record["entry_point"], tuple(record["frames"]))


def build_tree(records):
    """Links each record to the record of its caller and gives it an
    invocation identity.

    Eva prints the message of an analysed or interrupted call after the
    messages of the calls made by its body, and the message of a hit at the
    lookup. The parent of a record whose callstack is S is therefore the
    first later record with an analysed or interrupted body whose callstack
    is S without its last call. When the analysis stops before a call prints
    its message (a run killed or timed out), the calls still open form one
    chain, the callstack of the analysis when it stopped: each of them is
    inferred once from the callstacks of the records it contains, keyed by
    entry point and full callstack, and marked as inferred. The identity of
    a record is the identity of its parent, followed by FUNCTION@SITE#K, or
    FUNCTION@SITE/sN#K when the message gives the number N of the call
    statement, where K counts the earlier siblings with the same function and
    call site.

    Returns (roots, problems)."""
    problems = []
    pending = defaultdict(list)  # (entry, frames) -> records awaiting it
    roots = []
    for record in records:
        if "frames" not in record:
            raise ValueError(
                "message %d has no callstack: enable the categories "
                "cache and callstacks" % record["seq"])
        record["children"] = []
        executed = kinds(record)[1] in BODY_EXECUTIONS
        waiting = pending.pop(frames_key(record), [])
        if waiting and not executed:
            problems.append(
                "record %d: %d nested records before a call without a body"
                % (record["seq"], len(waiting)))
        record["children"].extend(waiting)
        if not record["frames"]:
            roots.append(record)
        else:
            parent = (record["entry_point"], tuple(record["frames"][:-1]))
            pending[parent].append(record)
    # Records left without a parent: the analysis stopped before the parent
    # printed its message. The open calls are inferred from the callstacks,
    # one node per entry point and callstack.
    inferred = {}

    def open_node(key):
        if key in inferred:
            return inferred[key]
        entry, frames = key
        node = {
            "seq": None, "inferred": True, "frames": list(frames),
            "entry_point": entry,
            "function": frames[-1][0] if frames else entry,
            "site": frames[-1][1] if frames else "",
            "stmt": frames[-1][2] if frames else None,
            "dispositions": OrderedDict(execution="open (no message)"),
            "children": [],
        }
        inferred[key] = node
        if frames:
            open_node((entry, frames[:-1]))["children"].append(node)
        else:
            roots.append(node)
        return node

    for key in sorted(pending, key=lambda k: (k[0], len(k[1]))):
        for record in pending[key]:
            problems.append("record %d has no parent message"
                            % record["seq"])
        open_node(key)["children"].extend(pending[key])
    if inferred:
        problems.append("%d calls inferred from the callstacks of an "
                        "interrupted log" % len(inferred))
    roots.sort(key=first_seq)
    counter = Counter()
    for root in roots:
        key = root["entry_point"]
        root["id"] = "%s#%d" % (key, counter[key])
        counter[key] += 1
        assign_ids(root)
    return roots, problems


def first_seq(record):
    if record.get("seq") is not None:
        return record["seq"]
    return min((first_seq(c) for c in record["children"]),
               default=float("inf"))


def site_key(function, site, stmt):
    """The call-site key of a call: FUNCTION@SITE, followed by /sN when the
    number N of the call statement is known."""
    key = "%s@%s" % (function, site)
    return key if stmt is None else "%s/s%d" % (key, stmt)


def assign_ids(record):
    counter = Counter()
    record["children"].sort(key=first_seq)
    for child in record["children"]:
        key = site_key(child["function"], child["site"], child.get("stmt"))
        child["id"] = "%s > %s#%d" % (record["id"], key, counter[key])
        child["parent"] = record["id"]
        counter[key] += 1
        assign_ids(child)


def walk(record):
    yield record
    for child in record["children"]:
        yield from walk(child)


def collector_kind(value):
    return disposition_kind(value) if value else ""


def records_command(args):
    with open_text(args.log) as lines:
        records = cache_records(lines)
    roots, problems = build_tree(records)
    producers = {}
    for root in roots:
        for record in walk(root):
            match = ENTRY.search(record["dispositions"].get("storage", ""))
            if match and kinds(record)[2] == "stored":
                producers[int(match.group(1))] = record["id"]
    out = open_text(args.output, "w") if args.output else sys.stdout
    for root in roots:
        for record in walk(root):
            lookup, execution, storage = kinds(record)
            parsed = parse_lookup(record["dispositions"].get("lookup", ""))
            collector = record["dispositions"].get("collector", "")
            row = OrderedDict()
            row["id"] = record["id"]
            row["parent"] = record.get("parent")
            row["seq"] = record["seq"]
            row["inferred"] = bool(record.get("inferred"))
            row["function"] = record["function"]
            row["site"] = record["site"]
            row["stmt"] = record.get("stmt")
            row["entry_point"] = record["entry_point"]
            row["callstack"] = [list(f) for f in record["frames"]]
            row["dispositions"] = record["dispositions"]
            row["lookup"], row["execution"], row["storage"] = \
                lookup, execution, storage
            row["lookup_rejected"] = parsed["rejected"]
            row["lookup_hit_entry"] = parsed["hit"]
            row["lookup_other"] = parsed["other"]
            row["collector"] = collector_kind(collector)
            row["hit_of"] = (producers.get(parsed["hit"])
                             if parsed["hit"] is not None else None)
            row["children"] = len(record["children"])
            out.write(json.dumps(row) + "\n")
    for problem in problems:
        out.write(json.dumps({"problem": problem}) + "\n")
        print("problem: " + problem, file=sys.stderr)
    if out is not sys.stdout:
        out.close()
    return 0


def load_records_and_problems(path):
    """The per-call records of a records file, and its structural
    problems."""
    rows, problems = [], []
    with open_text(path) as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if "problem" in row:
                problems.append(row["problem"])
            else:
                rows.append(row)
    return rows, problems


def load_records(path):
    return load_records_and_problems(path)[0]


# ----- Alignment of two runs -------------------------------------------------

def child_key(row):
    return site_key(row["function"], row["site"], row.get("stmt"))


def descendants(row, children):
    count = 0
    for child in children.get(row["id"], []):
        count += 1 + descendants(child, children)
    return count


def align(rows_a, rows_b):
    """Aligns the per-call records of two runs, from the entry point down.

    Two records are aligned when their parents are aligned and they have the
    same function, call site and call statement, with:
    - the same sequence of (function, call site, statement) among the
      siblings on both sides: siblings are aligned by position;
    - otherwise, a (function, call site, statement) that occurs exactly once
      on each side.
    Any other group of siblings is undecided: its records are reported and
    not aligned. When a record does not give the number of its call
    statement (a log of a binary that does not print it), two calls on one
    line cannot be told apart: every group of siblings of its parent is
    undecided. The records nested in a call that is a hit in one run and
    analysed in the other are reported as nested under a hit; records
    present in one run only are reported as unmatched."""
    def index(rows):
        children = defaultdict(list)
        roots = []
        for row in rows:
            if row["parent"] is None:
                roots.append(row)
            else:
                children[row["parent"]].append(row)
        for siblings in children.values():
            siblings.sort(key=lambda r: (r["seq"] is None, r["seq"] or 0))
        return roots, children

    roots_a, children_a = index(rows_a)
    roots_b, children_b = index(rows_b)
    result = {"pairs": [], "under_hit": [], "unmatched": [], "undecided": []}

    def unmatched(side, row, children, reason):
        result["unmatched"].append((side, row["id"], reason))
        for child in children.get(row["id"], []):
            unmatched(side, child, children, "parent unmatched")

    def nested_under_hit(side, row, children, hit_side):
        for child in children.get(row["id"], []):
            result["under_hit"].append((side, child["id"], hit_side))
            nested_under_hit(side, child, children, hit_side)

    def undecided(a, b, key, group_a, group_b, reason):
        size_a = sum(1 + descendants(r, children_a) for r in group_a)
        size_b = sum(1 + descendants(r, children_b) for r in group_b)
        result["undecided"].append(
            (a["id"], b["id"], key, len(group_a), len(group_b),
             size_a, size_b, reason))

    def visit(a, b):
        result["pairs"].append((a, b))
        kids_a = children_a.get(a["id"], [])
        kids_b = children_b.get(b["id"], [])
        if not kids_a and not kids_b:
            return
        if a["lookup"] == "hit" and not kids_a and kids_b:
            nested_under_hit("B", b, children_b, "A")
            return
        if b["lookup"] == "hit" and not kids_b and kids_a:
            nested_under_hit("A", a, children_a, "B")
            return
        keys_a = [child_key(r) for r in kids_a]
        keys_b = [child_key(r) for r in kids_b]
        no_number = any(r.get("stmt") is None for r in kids_a + kids_b)
        if not no_number and keys_a == keys_b:
            for x, y in zip(kids_a, kids_b):
                visit(x, y)
            return
        count_a, count_b = Counter(keys_a), Counter(keys_b)
        for key in sorted(set(count_a) | set(count_b)):
            group_a = [r for r in kids_a if child_key(r) == key]
            group_b = [r for r in kids_b if child_key(r) == key]
            if no_number:
                undecided(a, b, key, group_a, group_b,
                          "no statement number")
            elif count_a[key] == 1 and count_b[key] == 1:
                visit(group_a[0], group_b[0])
            elif not group_a or not group_b:
                for r in group_a:
                    unmatched("A", r, children_a, "no call at this site in B")
                for r in group_b:
                    unmatched("B", r, children_b, "no call at this site in A")
            else:
                undecided(a, b, key, group_a, group_b,
                          "repeated calls in another order")

    for key in sorted({r["function"] for r in roots_a} |
                      {r["function"] for r in roots_b}):
        ra = [r for r in roots_a if r["function"] == key]
        rb = [r for r in roots_b if r["function"] == key]
        if len(ra) == len(rb):
            for x, y in zip(ra, rb):
                visit(x, y)
        else:
            for r in ra:
                unmatched("A", r, children_a, "root count differs")
            for r in rb:
                unmatched("B", r, children_b, "root count differs")
    return result


def disposition_pair(a, b):
    return "%s/%s/%s -> %s/%s/%s" % (a["lookup"], a["execution"],
                                     a["storage"], b["lookup"],
                                     b["execution"], b["storage"])


def statement_numbers(rows):
    """Whether the records below the entry point give the number of their
    call statement: all, none or some."""
    calls = [r for r in rows if r["parent"] is not None]
    known = sum(1 for r in calls if r.get("stmt") is not None)
    if known == len(calls):
        return "all"
    return "none" if known == 0 else "some"


def summarize_alignment(rows_a, rows_b, result, problems_a=(),
                        problems_b=(), numbering="same"):
    """Counts of an alignment and its verdict.

    The records of each run are counted apart from the calls inferred from
    the callstacks of an interrupted log. [numbering] is "same" when both
    runs are known to number the statements of the program alike (the same
    revision of the analyzer on the same case), "not established"
    otherwise. The alignment is complete when every record of both runs is
    aligned, no call is inferred or interrupted, no structural problem was
    found in either log, both logs give the statement numbers and the
    numbering is the same; [verdict] says why it is not."""
    def inferred(row):
        return bool(row.get("inferred"))

    def interrupted(rows):
        return any(inferred(r) or r["execution"] == "interrupted"
                   for r in rows)

    pairs = result["pairs"]
    observed = [(a, b) for a, b in pairs
                if not inferred(a) and not inferred(b)]
    same = sum(1 for a, b in observed
               if a["dispositions"] == b["dispositions"])
    undecided_a = sum(g[5] for g in result["undecided"])
    undecided_b = sum(g[6] for g in result["undecided"])
    summary = OrderedDict()
    summary["records_a"] = sum(1 for r in rows_a if not inferred(r))
    summary["records_b"] = sum(1 for r in rows_b if not inferred(r))
    summary["inferred_a"] = sum(1 for r in rows_a if inferred(r))
    summary["inferred_b"] = sum(1 for r in rows_b if inferred(r))
    summary["aligned"] = len(observed)
    summary["aligned_with_inferred"] = len(pairs) - len(observed)
    summary["aligned_same_dispositions"] = same
    summary["aligned_other_dispositions"] = len(observed) - same
    summary["hit_a_analysed_b"] = sum(
        1 for a, b in observed if a["lookup"] == "hit"
        and b["lookup"] != "hit")
    summary["analysed_a_hit_b"] = sum(
        1 for a, b in observed if a["lookup"] != "hit"
        and b["lookup"] == "hit")
    summary["nested_under_hit_a"] = sum(
        1 for s, _, h in result["under_hit"] if s == "B")
    summary["nested_under_hit_b"] = sum(
        1 for s, _, h in result["under_hit"] if s == "A")
    summary["unmatched_a"] = sum(1 for s, _, _ in result["unmatched"]
                                 if s == "A")
    summary["unmatched_b"] = sum(1 for s, _, _ in result["unmatched"]
                                 if s == "B")
    summary["undecided_groups"] = len(result["undecided"])
    summary["undecided_records_a"] = undecided_a
    summary["undecided_records_b"] = undecided_b
    summary["interrupted_a"] = interrupted(rows_a)
    summary["interrupted_b"] = interrupted(rows_b)
    summary["problems_a"] = len(problems_a)
    summary["problems_b"] = len(problems_b)
    summary["statement_numbers_a"] = statement_numbers(rows_a)
    summary["statement_numbers_b"] = statement_numbers(rows_b)
    summary["numbering"] = numbering
    accounted_a = (len(pairs) + summary["nested_under_hit_b"]
                   + summary["unmatched_a"] + undecided_a)
    accounted_b = (len(pairs) + summary["nested_under_hit_a"]
                   + summary["unmatched_b"] + undecided_b)
    summary["accounted"] = (accounted_a == len(rows_a)
                            and accounted_b == len(rows_b))
    reasons = []
    if not summary["accounted"]:
        reasons.append("records not accounted for")
    if summary["interrupted_a"] or summary["interrupted_b"]:
        reasons.append("interrupted")
    if problems_a or problems_b:
        reasons.append("structural problems")
    if summary["statement_numbers_a"] != "all" or \
       summary["statement_numbers_b"] != "all":
        reasons.append("statement numbers missing")
    if numbering != "same":
        reasons.append("numbering not established")
    if not (len(observed) == summary["records_a"] == summary["records_b"]
            and len(pairs) == len(rows_a) == len(rows_b)):
        reasons.append("not every record aligned")
    summary["complete"] = not reasons
    summary["verdict"] = "complete" if not reasons else \
        "incomplete: " + ", ".join(reasons)
    return summary


def write_tsv(path, header, rows):
    with open_text(path, "w") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def align_command(args):
    rows_a, problems_a = load_records_and_problems(args.a)
    rows_b, problems_b = load_records_and_problems(args.b)
    result = align(rows_a, rows_b)
    numbering = "same" if args.same_numbering else "not established"
    summary = summarize_alignment(rows_a, rows_b, result, problems_a,
                                  problems_b, numbering)
    if args.output:
        with open_text(args.output + "summary.tsv", "w") as f:
            for key, value in summary.items():
                f.write("%s\t%s\n" % (key, value))
        write_tsv(args.output + "differences.tsv",
                  ["id_a", "id_b", "dispositions_a", "dispositions_b"],
                  [(a["id"], b["id"], json.dumps(a["dispositions"]),
                    json.dumps(b["dispositions"]))
                   for a, b in result["pairs"]
                   if a["dispositions"] != b["dispositions"]])
        write_tsv(args.output + "under-hit.tsv",
                  ["side", "id", "hit_in"], result["under_hit"])
        write_tsv(args.output + "unmatched.tsv",
                  ["side", "id", "reason"], result["unmatched"])
        write_tsv(args.output + "undecided.tsv",
                  ["parent_a", "parent_b", "call", "calls_a", "calls_b",
                   "records_a", "records_b", "reason"], result["undecided"])
        write_tsv(args.output + "problems.tsv", ["side", "problem"],
                  [("A", p) for p in problems_a]
                  + [("B", p) for p in problems_b])
    for key, value in summary.items():
        print("%s\t%s" % (key, value))
    return 0


# ----- State queries ---------------------------------------------------------

class Undecided(Exception):
    """Raised when an inclusion cannot be decided on the written forms."""


def parse_ival(text):
    if text == "B":
        return ("bottom",)
    if text.startswith("S"):
        return ("set", frozenset(int(x) for x in text[1:].split(",") if x))
    if text.startswith("I"):
        match = re.match(r"^I(-?\d*)\.\.(-?\d*)%(-?\d+)/(\d+)$", text)
        if not match:
            raise Undecided(text)
        lo = int(match.group(1)) if match.group(1) else None
        hi = int(match.group(2)) if match.group(2) else None
        return ("itv", lo, hi, int(match.group(3)), int(match.group(4)))
    if text == "Fnan":
        return ("float", None, None, True)
    if text.startswith("F"):
        body, nan = text[1:], False
        if body.endswith(";nan"):
            body, nan = body[:-4], True
        lo, _, hi = body.partition("..")
        return ("float", float.fromhex(lo), float.fromhex(hi), nan)
    raise Undecided(text)


def fkey(x):
    """Total order on floats where -0.0 is below +0.0."""
    return (x, math.copysign(1.0, x))


def itv_count(lo, hi, modu):
    if lo is None or hi is None:
        return None
    return (hi - lo) // modu + 1 if modu else 1


INT_TOP = ("itv", None, None, 0, 1)


def is_int_top(ival):
    """The top of Eva's numeric values (Ival.top): every integer."""
    return ival[0] == "itv" and ival[1] is None and ival[2] is None \
        and ival[4] <= 1


def float_has_plus_zero(f):
    if f[1] is None:
        return False
    return fkey(f[1]) <= fkey(0.0) <= fkey(f[2])


def ival_included(a, b):
    """Inclusion of two numeric values, as Ival.is_included decides it.
    Integers and floats are mixed as Eva mixes them: a float value is
    included in an integer value only when that value is the top of the
    numeric values, and an integer value in a float value only when it is
    the integer 0 and the float value contains +0."""
    if a[0] == "bottom":
        return True
    if b[0] == "bottom":
        return False
    if a[0] == "float" and b[0] == "float":
        if a[1] is None:
            return b[3]
        if b[1] is None:
            return False
        return (fkey(a[1]) >= fkey(b[1]) and fkey(a[2]) <= fkey(b[2])
                and (not a[3] or b[3]))
    if a[0] == "float":
        return is_int_top(b)
    if b[0] == "float":
        return a[0] == "set" and a[1] == frozenset([0]) \
            and float_has_plus_zero(b)
    if a[0] == "set":
        if b[0] == "set":
            return a[1] <= b[1]
        _, lo, hi, rem, modu = b
        return all((lo is None or x >= lo) and (hi is None or x <= hi)
                   and (modu == 0 or (x - rem) % modu == 0) for x in a[1])
    _, lo, hi, rem, modu = a
    if b[0] == "set":
        count = itv_count(lo, hi, modu)
        if count is None or count > len(b[1]):
            return False
        return all(lo + k * modu in b[1] for k in range(count))
    _, lo2, hi2, rem2, modu2 = b
    if lo2 is not None and (lo is None or lo < lo2):
        return False
    if hi2 is not None and (hi is None or hi > hi2):
        return False
    if modu2 <= 1:
        return True
    return modu % modu2 == 0 and (rem - rem2) % modu2 == 0


def parse_value(text):
    if text == "B":
        return ("bottom",)
    if text == "T":
        return ("top",)
    if text.startswith("G"):
        return ("garbled", frozenset(x for x in text[1:].split(";") if x))
    if text.startswith("M"):
        # Items are separated by ";", which also starts the suffix ";nan" of
        # a float: base names never contain ";" or "=", so an item with no
        # "=" is that suffix and belongs to the previous item.
        items = []
        for item in text[1:].split(";"):
            if item and "=" not in item and items:
                items[-1] += ";" + item
            elif item:
                items.append(item)
        entries = {}
        for item in items:
            base, _, ival = item.partition("=")
            entries[base] = parse_ival(ival)
        return ("map", entries)
    raise Undecided(text)


def value_included(a, b):
    if a[0] == "bottom" or b[0] == "top":
        return True
    if b[0] == "bottom" or a[0] == "top":
        return a[0] == b[0]
    if a[0] == "garbled":
        return b[0] == "garbled" and a[1] <= b[1]
    if b[0] == "garbled":
        return set(a[1]) <= b[1]
    if a[0] == "map" and not a[1]:
        return True
    return all(base in b[1] and ival_included(ival, b[1][base])
               for base, ival in a[1].items())


def answer_included(a, b):
    """Inclusion of two answers (initialized, escaping, value): a value
    that may be uninitialized or escaping is included only in another that
    may be too."""
    init_a, esc_a, value_a = a
    init_b, esc_b, value_b = b
    if init_a == 0 and init_b == 1:
        return False
    if esc_a == 1 and esc_b == 0:
        return False
    return value_included(parse_value(value_a), parse_value(value_b))


def is_top_answer(value):
    """Whether an answer is top: the top of Eva's values (T), or a value
    with no address whose numbers are the top of the integers
    (MNULL=I..%0/1) or every float and NaN (MNULL=F-inf..inf;nan). A
    garbled mix, or an address with any offset (Mx=I..%0/1), is not top:
    it keeps its bases. The written form is read alone, whatever the answer
    of the other run."""
    if value == "T":
        return True
    if not value.startswith("M"):
        return False
    try:
        entries = parse_value(value)[1]
    except (Undecided, ValueError):
        return False
    if list(entries) != ["NULL"]:
        return False
    ival = entries["NULL"]
    return is_int_top(ival) or (
        ival[0] == "float" and ival[1] == float("-inf")
        and ival[2] == float("inf") and ival[3])


def is_garbled_answer(value):
    return value.startswith("G")


def classify(a, b):
    """Compares answer [b] of the candidate run with answer [a] of the
    baseline run: equal, wider, narrower, incomparable or undecided. The
    same written answer is equal, even when its form is not understood."""
    if a == b:
        return "equal"
    try:
        ab = answer_included(a, b)
        ba = answer_included(b, a)
    except (Undecided, ValueError):
        return "undecided"
    if ab and ba:
        return "equal"
    if ab:
        return "wider"
    if ba:
        return "narrower"
    return "incomparable"


def load_queries(path):
    """Reads the answers of a run. Returns a dictionary: the reached
    statements, the answers, the queries without an answer by reason
    (unavailable or error), whether the file is complete and why not. A
    file is complete when it ends with its done line and the count of that
    line is the number of answer, unavailable and error lines."""
    reach, answers, unavailable = set(), {}, {}
    done, rows = None, 0
    with open_text(path) as f:
        for line in f:
            fields = line.rstrip("\n").split("\t")
            if fields[0] == "reach":
                reach.add((fields[1], fields[2]))
            elif fields[0] == "answer":
                rows += 1
                answers[tuple(fields[1:6])] = \
                    (int(fields[6]), int(fields[7]), fields[8])
            elif fields[0] == "unavailable":
                rows += 1
                unavailable[tuple(fields[1:6])] = fields[6]
            elif fields[0] == "error":
                rows += 1
                unavailable[tuple(fields[1:6])] = "error"
            elif fields[0] == "done":
                done = int(fields[1])
    if done is None:
        status = "incomplete: no done line"
    elif done != rows:
        status = "incomplete: done %d, %d lines" % (done, rows)
    else:
        status = "complete"
    return {"reach": reach, "answers": answers, "unavailable": unavailable,
            "status": status}


UNAVAILABLE_REASONS = ("unreached", "no-callstack", "no-results",
                       "top-state", "disabled-domain", "error", "missing")


def compare_queries(path_a, path_b):
    """Compares the answers of run B with those of run A, query by query.

    Each query asked in either run is counted once: answered in both runs
    (equal, wider, narrower, incomparable or undecided), or without an
    answer on a side, with the reason. Top answers are counted on each side
    over all the answers of that side. Returns the summary, the queries that
    are not equal, and the statements reached in one run only."""
    qa, qb = load_queries(path_a), load_queries(path_b)
    ans_a, ans_b = qa["answers"], qb["answers"]
    keys = (set(ans_a) | set(ans_b) | set(qa["unavailable"])
            | set(qb["unavailable"]))
    counts = Counter()
    details = []
    for side, q in (("a", qa), ("b", qb)):
        for answer in q["answers"].values():
            if is_top_answer(answer[2]):
                counts["top_" + side] += 1
            if is_garbled_answer(answer[2]):
                counts["garbled_" + side] += 1
    for key in sorted(keys):
        stmt = (key[0], key[1])
        a, b = ans_a.get(key), ans_b.get(key)
        if a is not None and b is not None:
            verdict = classify(a, b)
            counts[verdict] += 1
            if verdict != "equal":
                details.append(key + (verdict, a[2], b[2]))
            continue
        for side, answer, q in (("a", a, qa), ("b", b, qb)):
            if answer is None:
                if key in q["unavailable"]:
                    reason = q["unavailable"][key]
                elif key[2] != "exit" and stmt not in q["reach"]:
                    reason = "unreached"
                elif key[3] != "*":
                    reason = "no-callstack"
                else:
                    reason = "missing"
                if reason not in UNAVAILABLE_REASONS:
                    reason = "other"
                counts["unavailable_%s_%s" % (side, reason)] += 1
                details.append(key + ("unavailable in " + side.upper()
                                      + " (" + reason + ")",
                                      a[2] if a else "", b[2] if b else ""))
    summary = OrderedDict()
    summary["queries"] = len(keys)
    summary["answered_a"] = len(ans_a)
    summary["answered_b"] = len(ans_b)
    summary["answered_both"] = sum(counts[k] for k in (
        "equal", "wider", "narrower", "incomparable", "undecided"))
    for k in ("equal", "wider", "narrower", "incomparable", "undecided",
              "top_a", "top_b", "garbled_a", "garbled_b"):
        summary[k] = counts[k]
    for side in ("a", "b"):
        for reason in UNAVAILABLE_REASONS + ("other",):
            summary["unavailable_%s_%s" % (side, reason)] = \
                counts["unavailable_%s_%s" % (side, reason)]
    summary["reached_a"] = len(qa["reach"])
    summary["reached_b"] = len(qb["reach"])
    summary["reached_a_only"] = len(qa["reach"] - qb["reach"])
    summary["reached_b_only"] = len(qb["reach"] - qa["reach"])
    summary["complete_a"] = qa["status"]
    summary["complete_b"] = qb["status"]
    summary["comparison"] = (
        "complete" if qa["status"] == qb["status"] == "complete"
        else "incomplete")
    reach = sorted([s + ("A",) for s in qa["reach"] - qb["reach"]]
                   + [s + ("B",) for s in qb["reach"] - qa["reach"]])
    return summary, details, reach


def queries_command(args):
    summary, details, reach = compare_queries(args.a, args.b)
    if args.output:
        with open_text(args.output + "summary.tsv", "w") as f:
            for key, value in summary.items():
                f.write("%s\t%s\n" % (key, value))
        write_tsv(args.output + "differences.tsv",
                  ["function", "stmt", "point", "callstack", "lvalue",
                   "verdict", "answer_a", "answer_b"], details)
        write_tsv(args.output + "reached-in-one-run.tsv",
                  ["function", "stmt", "reached_only_in"], reach)
    for key, value in summary.items():
        print("%s\t%s" % (key, value))
    return 0


# ----- Alarms ------------------------------------------------------------

def normalize_directory(directory, roots=()):
    """The directory of an alarm with the root of the run removed: the
    source snapshot of each run is a fresh directory, so a path under one of
    [roots] is written relative to it, from ${SRC}."""
    for root in roots:
        root = root.rstrip("/")
        if root and (directory == root or directory.startswith(root + "/")):
            return "${SRC}" + directory[len(root):]
    return directory


def load_alarms(path, roots=()):
    """The alarms and properties of an alarms.csv file written by
    -report-csv, as a multiset: (directory, file, line, function, kind,
    property) -> Counter of statuses. The directory is normalised by
    [normalize_directory]. Returns the multiset and the number of keys that
    occur more than once."""
    result = defaultdict(Counter)
    with open_text(path) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            key = (normalize_directory(row.get("directory", ""), roots),
                   row["file"], row["line"], row["function"],
                   row["property kind"], row["property"])
            result[key][row["status"]] += 1
    duplicates = sum(1 for c in result.values() if sum(c.values()) > 1)
    return result, duplicates


def compare_alarms(path_a, path_b, roots_a=(), roots_b=()):
    """Compares the properties of two runs. A key that occurs several times
    in a file is compared as a multiset of statuses, so that a change of
    status of one occurrence is not lost."""
    a, dup_a = load_alarms(path_a, roots_a)
    b, dup_b = load_alarms(path_b, roots_b)

    def status(c):
        return ",".join("%s*%d" % kv if kv[1] > 1 else kv[0]
                        for kv in sorted(c.items()))

    summary = OrderedDict()
    summary["properties_a"] = sum(sum(c.values()) for c in a.values())
    summary["properties_b"] = sum(sum(c.values()) for c in b.values())
    summary["keys_a"] = len(a)
    summary["keys_b"] = len(b)
    summary["duplicate_keys_a"] = dup_a
    summary["duplicate_keys_b"] = dup_b
    summary["same_status"] = sum(1 for k in a if k in b and a[k] == b[k])
    summary["other_status"] = sum(1 for k in a if k in b and a[k] != b[k])
    summary["a_only"] = sum(1 for k in a if k not in b)
    summary["b_only"] = sum(1 for k in b if k not in a)
    details = [k + (status(a.get(k, Counter())), status(b.get(k, Counter())))
               for k in sorted(set(a) | set(b))
               if a.get(k, Counter()) != b.get(k, Counter())]
    return summary, details


def alarms_command(args):
    summary, details = compare_alarms(args.a, args.b, args.root_a or (),
                                      args.root_b or ())
    for key, value in summary.items():
        print("%s\t%s" % (key, value))
    for row in details:
        print("difference\t" + "\t".join(row))
    return 0


# ----- Builtin applications and cache activity -------------------------------

# Names under which the allocation and release builtins are applied: the
# replaced libc function or the builtin itself, as in the measurement of
# set A (issue #28 of nyandrianinamamy/frama-c).
CANONICAL_BUILTINS = {
    "malloc": "malloc", "Frama_C_malloc": "malloc",
    "calloc": "calloc", "Frama_C_calloc": "calloc",
    "realloc": "realloc", "Frama_C_realloc": "realloc",
    "reallocarray": "reallocarray", "Frama_C_reallocarray": "reallocarray",
    "alloca": "alloca", "Frama_C_alloca": "alloca",
    "__fc_vla_alloc": "vla_alloc", "Frama_C_vla_alloc": "vla_alloc",
    "free": "free", "Frama_C_free": "free",
    "__fc_vla_free": "vla_free", "Frama_C_vla_free": "vla_free",
}
ALLOCATION = ["malloc", "calloc", "realloc", "reallocarray", "alloca",
              "vla_alloc"]
RELEASE = ["free", "vla_free"]


# Counter families of the statistics file. A family is measured in a run
# when the binary has its counters and the run enables them: then a counter
# with no row is a measured zero. Otherwise its value is absent, written -.
#   builtin:   builtin-applied-NAME, every run of a binary that has it
#   memexec:   memexec-hits, -misses, -stored, -refused-REASON, with
#              -eva-memexec
#   supplied:  cache-hits, cache-rejected-REASON, cache-refused-REASON, the
#              entries supplied by a test module
#   collector: collector-would-store, collector-refused-REASON, unless
#              -eva-no-cache-collect
#   producer:  cache-produced, cache-production-refused-REASON, the entries
#              produced from the bodies observed by the collector, unless
#              -eva-no-cache-collect
FAMILIES = ("builtin", "memexec", "supplied", "collector", "producer")
FAMILY_PREFIXES = (("builtin-applied-", "builtin"), ("memexec-", "memexec"),
                   ("cache-produced", "producer"),
                   ("cache-production-", "producer"),
                   ("cache-", "supplied"), ("collector-", "collector"))
# A counter name of each family, looked for in the compiled Eva plugin to
# tell whether a binary has the family.
FAMILY_MARKERS = {"builtin": b"builtin-applied-", "memexec": b"memexec-hits",
                  "supplied": b"cache-rejected-",
                  "collector": b"collector-would-store",
                  "producer": b"cache-production-refused-"}


def stats_rows(stats_path):
    """The rows (name, function, value) of the counters of the families."""
    rows = []
    with open_text(stats_path) as f:
        for line in f:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 4:
                continue
            for prefix, family in FAMILY_PREFIXES:
                if fields[0].startswith(prefix):
                    rows.append((family, fields[0], fields[1],
                                 int(fields[3])))
                    break
    return rows


def measured_families(binary_families, mode_flags):
    """The families measured by a run: those of the binary, without
    memexec unless the run enables it, and without the collector when the
    run disables it."""
    flags = mode_flags.split()
    families = set(binary_families)
    if "-eva-memexec" not in flags:
        families.discard("memexec")
    if "-eva-no-cache-collect" in flags:
        families.discard("collector")
        families.discard("producer")
    return families


def family_of_binary(cmxs_path):
    """The counter families that a compiled Eva plugin has."""
    with open(cmxs_path, "rb") as f:
        data = f.read()
    return [k for k in FAMILIES if FAMILY_MARKERS[k] in data]


def run_counts(stats_path, measured=FAMILIES):
    """Builtin applications, cache activity and collector verdicts from an
    Eva statistics file (-eva-statistics-file). A counter of a family that
    the run did not measure is None."""
    builtins = Counter()
    values = Counter()
    by_reason = defaultdict(Counter)
    for family, name, _, value in stats_rows(stats_path):
        if family == "builtin":
            canonical = CANONICAL_BUILTINS.get(name[len("builtin-applied-"):])
            if canonical:
                builtins[canonical] += value
            continue
        for prefix in ("memexec-refused-", "cache-rejected-",
                       "cache-refused-", "collector-refused-",
                       "cache-production-refused-"):
            if name.startswith(prefix):
                by_reason[prefix[:-1]][name[len(prefix):]] += value
                name = prefix[:-1]
        values[name] += value

    def get(family, value):
        return value if family in measured else None

    def reasons(key):
        return ",".join("%s=%d" % kv for kv in sorted(by_reason[key].items()))

    counts = OrderedDict()
    for k in ALLOCATION + RELEASE:
        counts[k] = get("builtin", builtins[k])
    total = sum(builtins.values())
    counts["allocation_and_release"] = get("builtin", total)
    counts["in_set_a"] = get("builtin", total == 0)
    counts["hits"] = get("memexec", values["memexec-hits"])
    counts["misses"] = get("memexec", values["memexec-misses"])
    counts["stored"] = get("memexec", values["memexec-stored"])
    counts["refused"] = get("memexec", values["memexec-refused"])
    counts["refused_by_reason"] = get("memexec", reasons("memexec-refused"))
    counts["supplied_hits"] = get("supplied", values["cache-hits"])
    counts["supplied_rejected"] = get("supplied", values["cache-rejected"])
    counts["supplied_rejected_by_reason"] = \
        get("supplied", reasons("cache-rejected"))
    counts["supplied_refused"] = get("supplied", values["cache-refused"])
    counts["supplied_refused_by_reason"] = \
        get("supplied", reasons("cache-refused"))
    counts["collector_would_store"] = \
        get("collector", values["collector-would-store"])
    counts["collector_refused"] = get("collector", values["collector-refused"])
    counts["collector_refused_by_reason"] = \
        get("collector", reasons("collector-refused"))
    counts["producer_stored"] = get("producer", values["cache-produced"])
    counts["producer_refused"] = \
        get("producer", values["cache-production-refused"])
    counts["producer_refused_by_reason"] = \
        get("producer", reasons("cache-production-refused"))
    return counts


def function_counts(stats_path, measured=FAMILIES):
    """Cache activity and collector verdicts per function from an Eva
    statistics file: rows [function, hits, misses, stored, refused,
    collector_would_store, collector_refused], sorted by function, None for
    a family the run did not measure."""
    table = defaultdict(Counter)
    for family, name, function, value in stats_rows(stats_path):
        if family not in ("memexec", "collector"):
            continue
        for prefix in ("memexec-refused-", "collector-refused-"):
            if name.startswith(prefix):
                name = prefix[:-1]
        table[function][name] += value

    def get(family, value):
        return value if family in measured else None

    return [[kf, get("memexec", c["memexec-hits"]),
             get("memexec", c["memexec-misses"]),
             get("memexec", c["memexec-stored"]),
             get("memexec", c["memexec-refused"]),
             get("collector", c["collector-would-store"]),
             get("collector", c["collector-refused"])]
            for kf, c in sorted(table.items())]


TIMED_MODES = ("nocache", "cache", "reference")


def time_rows(runs):
    """Elapsed times of the first run of each mode of each case, and the
    ratios cache/nocache and cache/reference when both runs completed and
    were measured. A run that did not complete gives its outcome instead of
    a time; the runs of the fixtures are not measured."""
    def measured(r):
        return (r is not None and r.get("outcome") == "completed"
                and r.get("elapsed_s", "") != "")

    by_case = OrderedDict()
    for r in runs:
        if r.get("mode") in TIMED_MODES:
            by_case.setdefault(r["case"], {})[r["mode"]] = r
    rows = []
    for case, modes in by_case.items():
        cells = []
        for mode in TIMED_MODES:
            r = modes.get(mode)
            if r is None:
                cells.append("not run")
            elif r.get("outcome") != "completed":
                cells.append(r.get("outcome", ""))
            elif not measured(r):
                cells.append("not measured")
            else:
                cells.append(r["elapsed_s"])

        def ratio(mode):
            a, b = modes.get("cache"), modes.get(mode)
            if not (measured(a) and measured(b)):
                return "n/a"
            denominator = float(b["elapsed_s"])
            if denominator == 0:
                return "n/a"
            return "%.3f" % (float(a["elapsed_s"]) / denominator)
        rows.append([case] + cells + [ratio("nocache"), ratio("reference")])
    return rows


def counts_command(args):
    families = FAMILIES
    if args.families is not None:
        families = measured_families(
            [f for f in args.families.split(",") if f], args.flags or "")
    for key, value in run_counts(args.stats, families).items():
        print("%s\t%s" % (key, cell(value)))
    return 0


def families_command(args):
    print(",".join(family_of_binary(args.cmxs)))
    return 0


# ----- Provenance of a binary ------------------------------------------------

def checkout_provenance(checkout):
    """The revision of a Frama-C checkout and the patch applied on top of
    it: (revision, patch SHA-256, patch file). A directory made by
    tools/build-reference.sh records its revision in CAMPAIGN_REVISION and,
    when a patch was applied, keeps the patch in CAMPAIGN_PATCH.patch and
    its SHA-256 in CAMPAIGN_PATCH_SHA256. A git working tree must have no
    local change; its HEAD is the revision. The patch fields are empty when
    no patch was applied. Raises ValueError when no revision is known."""
    revision_file = os.path.join(checkout, "CAMPAIGN_REVISION")
    if os.path.exists(revision_file):
        with open(revision_file) as f:
            lines = [l.strip() for l in f if l.strip()]
        if len(lines) != 1 or not re.fullmatch(r"[0-9a-f]{40}", lines[0]):
            raise ValueError("%s must hold one revision" % revision_file)
        patch = os.path.join(checkout, "CAMPAIGN_PATCH.patch")
        digest_file = os.path.join(checkout, "CAMPAIGN_PATCH_SHA256")
        if not os.path.exists(patch):
            if os.path.exists(digest_file):
                raise ValueError("%s has no patch" % digest_file)
            return lines[0], "", ""
        with open(patch, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        with open(digest_file) as f:
            recorded = f.read().strip()
        if recorded != digest:
            raise ValueError("the patch of %s does not match its SHA-256"
                             % checkout)
        return lines[0], digest, patch
    git = ["git", "-C", checkout]
    try:
        head = subprocess.run(git + ["rev-parse", "HEAD"], check=True,
                              capture_output=True, text=True).stdout.strip()
        status = subprocess.run(
            git + ["status", "--porcelain", "--untracked-files=no"],
            check=True, capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError):
        raise ValueError("no revision for %s" % checkout)
    if status.strip():
        raise ValueError("the checkout %s has local changes" % checkout)
    return head, "", ""


def provenance_command(args):
    """Prints the revision, patch SHA-256 and archived patch of a checkout,
    separated by tabulations, and copies the patch into the provenance
    directory as ROLE.patch."""
    try:
        revision, digest, patch = checkout_provenance(args.checkout)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    kept = ""
    if patch:
        os.makedirs(args.patches, exist_ok=True)
        kept = os.path.join(args.patches, args.role + ".patch")
        with open(patch, "rb") as src, open(kept, "wb") as dst:
            dst.write(src.read())
        kept = os.path.join("provenance", "patches", args.role + ".patch")
    print("%s\t%s\t%s" % (revision, digest or "-", kept or "-"))
    return 0


# ----- Outcome of a run ----------------------------------------------------

# Messages of Frama-C and of the OCaml runtime when memory is exhausted.
OUT_OF_MEMORY = re.compile(
    r"^\[kernel\] Unexpected error \(Out of memory\)|"
    r"^Fatal error: (exception Out of memory|out of memory|"
    r"Not enough heap memory|allocation failure)", re.M)
SIGNAL = re.compile(r"^Command terminated by signal (\d+)", re.M)


def read_measure(path):
    """The values written by watchdog.py for the measured invocation, or by
    GNU time in the runs of earlier revisions of this harness. GNU time
    writes status 0 and a line naming the signal when the command was killed
    by a signal: the status is then 128 plus the signal."""
    if not os.path.exists(path):
        return None
    with open_text(path) as f:
        text = f.read()
    measure = OrderedDict()
    for line in text.splitlines():
        key, sep, value = line.partition("\t")
        if sep:
            measure[key] = value
    match = SIGNAL.search(text)
    if match:
        measure["signal"] = match.group(1)
        measure["status"] = str(128 + int(match.group(1)))
    return measure


def oom_evidence(measure, log_text):
    """The evidence that memory was exhausted: the message of Frama-C or of
    the OCaml runtime in the log, or for a command killed by SIGKILL that
    the watchdog did not send, the out-of-memory killer in the memory
    events of the cgroup or in the kernel log. Empty when there is none."""
    if OUT_OF_MEMORY.search(log_text):
        return "log"
    if measure.get("signal") == "9" and measure.get("watchdog") != "kill":
        events = measure.get("oom_kill_events", "")
        if events.isdigit() and int(events) > 0:
            return "cgroup oom_kill +" + events
        if measure.get("kernel_log_oom") == "yes":
            return "kernel log"
    return ""


def classify_outcome(parse_exit, make_exit, measure, log_text,
                     entry_analysed, timeout_s=None):
    """The outcome of one run:
    - parse-error: the parsing step failed, Eva did not run;
    - harness-error: the Eva invocation was not measured, or make failed
      after a successful invocation;
    - timeout: the watchdog sent its signal at the wall-time limit; a run
      measured by an earlier revision of this harness, which did not record
      it, is never classified as a timeout;
    - oom: Frama-C or the OCaml runtime reports that memory is exhausted, or
      the out-of-memory killer of the system is reported to have killed it;
    - killed: killed by SIGKILL that the watchdog did not send, with no
      evidence of the out-of-memory killer: cause unknown;
    - error: any other nonzero exit status or signal, such as 1 (invalid
      user input), 3 (unimplemented feature), 4 (internal error), 125
      (unexpected exception), or 124 when the watchdog did not fire;
    - incomplete: exit status 0 but the analysis of the entry point did
      not end;
    - completed.
    [timeout_s] is not used: the outcome does not depend on the elapsed
    time."""
    if parse_exit != 0:
        return "parse-error"
    if measure is None:
        return "harness-error"
    if measure.get("watchdog", "none") != "none":
        return "timeout"
    if oom_evidence(measure, log_text):
        return "oom"
    status = int(measure["status"])
    if measure.get("signal") == "9":
        return "killed"
    if status != 0:
        return "error"
    if make_exit != 0:
        return "harness-error"
    if not entry_analysed:
        return "incomplete"
    return "completed"


def measure_command(args):
    """Prints the measure of a run as key-value lines, with the exit status
    of the command as exit, or 128 plus the signal, as status."""
    for key, value in (read_measure(args.measure) or {}).items():
        if key == "exit":
            continue
        print("%s\t%s" % ("exit" if key == "status" else key, value))
    return 0


def outcome_command(args):
    run = args.run
    measure = read_measure(os.path.join(run, "measure"))
    log_text = ""
    if os.path.exists(os.path.join(run, "eva.log")):
        with open_text(os.path.join(run, "eva.log")) as f:
            log_text = f.read()
    entry_analysed = False
    records = os.path.join(run, "records.jsonl")
    if os.path.exists(records):
        entry_analysed = any(r["parent"] is None and
                             r["execution"] == "analysed"
                             for r in load_records(records))
    outcome = classify_outcome(args.parse_exit, args.make_exit, measure,
                               log_text, entry_analysed)
    evidence = oom_evidence(measure, log_text) if measure else ""
    print("%s\t%s" % (outcome, evidence or "-"))
    return 0


# ----- Tables ------------------------------------------------------------

def read_kv(path):
    result = OrderedDict()
    if os.path.exists(path):
        with open_text(path) as f:
            for line in f:
                key, _, value = line.rstrip("\n").partition("\t")
                if key:
                    result[key] = value
    return result


def markdown_table(header, rows):
    out = io.StringIO()
    out.write("| " + " | ".join(header) + " |\n")
    out.write("|" + "|".join("---" for _ in header) + "|\n")
    for row in rows:
        out.write("| " + " | ".join(str(x) for x in row) + " |\n")
    return out.getvalue()


def run_families(run, stats_path):
    """The counter families measured by a run: from the families of its
    binary and its options, recorded in run.tsv, or, for a run that does not
    record them, the families with at least one row in its statistics."""
    if run.get("counter_families", "") not in ("",):
        binary = [f for f in run["counter_families"].split(",") if f]
        flags = " ".join(run.get(k, "") for k in ("flag", "extra_eva_flags"))
        return measured_families(binary, flags)
    return {family for family, _, _, _ in stats_rows(stats_path)}


def cell(value):
    if value is None or value == "":
        return "-"
    if value is True or value is False:
        return "True" if value else "False"
    return value


def tables_command(args):
    root = args.run_dir
    runs_dir = os.path.join(root, "runs")
    runs = []
    for dirpath, _, filenames in os.walk(runs_dir):
        if "run.tsv" in filenames:
            runs.append(read_kv(os.path.join(dirpath, "run.tsv")))
    runs.sort(key=lambda r: (r.get("case", ""), r.get("mode", "")))
    by_run = {(r.get("case"), r.get("mode")): r for r in runs}
    recorded = {}
    if args.recorded_set_a and os.path.exists(args.recorded_set_a):
        with open_text(args.recorded_set_a) as f:
            for row in csv.DictReader(
                    (l for l in f if not l.startswith("#")), delimiter="\t"):
                recorded[row["target"]] = row["in_A"]
    out_dir = os.path.join(root, "tables")
    os.makedirs(out_dir, exist_ok=True)
    md = io.StringIO()
    md.write("# Result tables\n\nProduced by `campaign.py tables` from "
             "`%s`. A cell `-` is a value that was not measured.\n\n"
             % os.path.basename(os.path.abspath(root)))

    # Outcomes, time and memory.
    keys = ["case", "mode", "outcome", "exit", "signal", "watchdog",
            "oom_evidence", "elapsed_s", "user_s", "maxrss_kib", "timeout_s"]
    header = keys[:-1] + ["limit_s"]
    rows = [[cell(r.get(k)) for k in keys] for r in runs]
    write_tsv(os.path.join(out_dir, "outcomes.tsv"), header, rows)
    md.write("## Outcomes, time and memory per invocation\n\n`watchdog` is "
             "the last signal sent at the wall-time limit (`none` when it "
             "did not fire); `oom_evidence` the evidence that memory was "
             "exhausted.\n\n")
    md.write(markdown_table(header, rows) + "\n")

    def stats_of(r):
        path = os.path.join(root, "runs", r["case"], r["mode"],
                            "eva-stats.csv")
        return path if os.path.exists(path) else None

    # Cache activity and builtin applications.
    header = ["case", "mode", "hits", "misses", "stored", "refused",
              "refused_by_reason", "allocation_and_release", "in_set_a",
              "recorded_in_set_a", "agrees"]
    rows = []
    collector_rows = []
    for r in runs:
        stats = stats_of(r)
        if stats is None:
            rows.append([r["case"], r["mode"]] + ["-"] * 9)
            collector_rows.append([r["case"], r["mode"]] + ["-"] * 10)
            continue
        c = run_counts(stats, run_families(r, stats))
        target = r["case"].rsplit("/", 1)[0]
        rec = recorded.get(target, "")
        mine = cell(c["in_set_a"])
        agrees = "-"
        if rec and mine != "-":
            agrees = "yes" if rec == mine else "NO"
        rows.append([r["case"], r["mode"]] + [cell(c[k]) for k in (
            "hits", "misses", "stored", "refused", "refused_by_reason",
            "allocation_and_release")] + [mine, rec or "-", agrees])
        collector_rows.append([r["case"], r["mode"]] + [cell(c[k]) for k in (
            "collector_would_store", "collector_refused",
            "collector_refused_by_reason", "producer_stored",
            "producer_refused", "producer_refused_by_reason",
            "supplied_hits", "supplied_rejected", "supplied_refused",
            "supplied_rejected_by_reason")])
    write_tsv(os.path.join(out_dir, "activity.tsv"), header, rows)
    md.write("## Cache activity and set A\n\nTotals per case of the "
             "statistics file; memexec counts only in the modes that "
             "enable it. `allocation_and_release` sums the "
             "applications of the allocation and release builtins; a run "
             "is in set A when it is 0. `recorded_in_set_a` is the "
             "membership recorded by the earlier measurement.\n\n")
    md.write(markdown_table(header, rows) + "\n")
    header = ["case", "mode", "collector_would_store", "collector_refused",
              "collector_refused_by_reason", "producer_stored",
              "producer_refused", "producer_refused_by_reason",
              "supplied_hits", "supplied_rejected", "supplied_refused",
              "supplied_rejected_by_reason"]
    write_tsv(os.path.join(out_dir, "collector.tsv"), header,
              collector_rows)
    md.write("## Collector verdicts, produced and supplied entries\n\n"
             "Verdicts of the body access collector on the bodies analysed "
             "to completion, the entries the producer stored from them or "
             "refused (no lookup reads them), and the counters of entries "
             "supplied by a test module, which no campaign run supplies.\n\n")
    md.write(markdown_table(header, collector_rows) + "\n")

    # Cache activity per function, in a file of its own.
    rows = []
    for r in runs:
        stats = stats_of(r)
        if stats:
            rows.extend([r["case"], r["mode"]] + [cell(x) for x in row]
                        for row in function_counts(stats,
                                                   run_families(r, stats)))
    write_tsv(os.path.join(out_dir, "functions.tsv"),
              ["case", "mode", "function", "hits", "misses", "stored",
               "refused", "collector_would_store", "collector_refused"],
              rows)
    md.write("The hits, misses, stores, refusals and collector verdicts per "
             "function are in `functions.tsv`.\n\n")

    # Times of the modes.
    header = ["case", "nocache_s", "cache_s", "reference_s",
              "cache_over_nocache", "cache_over_reference"]
    rows = time_rows(runs)
    write_tsv(os.path.join(out_dir, "times.tsv"), header, rows)
    md.write("## Elapsed time per mode\n\nElapsed time of the first run of "
             "each mode, or its outcome when it did not complete. A ratio is "
             "given only when both runs completed.\n\n")
    md.write(markdown_table(header, rows) + "\n")

    # Comparisons.
    comparisons = []
    comp_dir = os.path.join(root, "comparisons")
    for dirpath, _, filenames in os.walk(comp_dir):
        if "pair.tsv" in filenames:
            comparisons.append((dirpath, read_kv(
                os.path.join(dirpath, "pair.tsv"))))
    comparisons.sort(key=lambda c: (c[1].get("case", ""),
                                    c[1].get("baseline", ""),
                                    c[1].get("candidate", "")))

    def completed(pair):
        return all(by_run.get((pair["case"], pair[k]), {}).get("outcome")
                   == "completed" for k in ("baseline", "candidate"))

    align_keys = ["records_a", "records_b", "inferred_a", "inferred_b",
                  "aligned", "aligned_other_dispositions", "hit_a_analysed_b",
                  "analysed_a_hit_b", "nested_under_hit_a",
                  "nested_under_hit_b", "unmatched_a", "unmatched_b",
                  "undecided_groups", "problems_a", "problems_b",
                  "accounted", "complete", "verdict"]
    query_keys = ["queries", "answered_both", "equal", "wider", "narrower",
                  "incomparable", "undecided", "top_a", "top_b",
                  "unavailable_a_no-callstack", "unavailable_b_no-callstack",
                  "unavailable_a_unreached", "unavailable_b_unreached",
                  "unavailable_a_no-results", "unavailable_b_no-results",
                  "reached_a_only", "reached_b_only", "complete_a",
                  "complete_b", "comparison"]
    alarm_keys = ["properties_a", "properties_b", "duplicate_keys_a",
                  "duplicate_keys_b", "same_status", "other_status",
                  "a_only", "b_only"]
    for title, name, keys in (
            ("Alignment of the per-call records", "alignment", align_keys),
            ("State queries", "queries", query_keys),
            ("Alarms and property statuses", "alarms", alarm_keys)):
        header = ["case", "A", "B", "both_completed"] + keys
        rows = []
        compared = both = 0
        for dirpath, pair in comparisons:
            values = read_kv(os.path.join(dirpath, name + "-summary.tsv"))
            done = completed(pair)
            if values:
                compared += 1
                both += done
            rows.append([pair["case"], pair["baseline"], pair["candidate"],
                         cell(done)]
                        + [cell(values.get(k)) for k in keys])
        write_tsv(os.path.join(out_dir, name + ".tsv"), header, rows)
        md.write("## %s\n\nRun A is the baseline, run B the candidate. "
                 "Pairs: %d, compared: %d, with both runs completed: %d.\n\n"
                 % (title, len(comparisons), compared, both))
        md.write(markdown_table(header, rows) + "\n")
    with open_text(os.path.join(out_dir, "tables.md"), "w") as f:
        f.write(md.getvalue())
    sys.stdout.write(md.getvalue())
    return 0


# ----- Manifest ----------------------------------------------------------

MANIFEST_HEADER = ["case", "target", "directory", "configuration",
                   "oscs_revision", "directory_tree", "entry_point",
                   "domains", "precision", "harness", "sources", "machdep",
                   "parse_flags", "eva_flags", "configuration_sha256"]

PRECISION_OPTIONS = ("-eva-precision", "-eva-slevel", "-eva-plevel",
                     "-eva-ilevel", "-eva-partition-history",
                     "-eva-split-return", "-eva-subdivide-non-linear",
                     "-eva-auto-loop-unroll", "-eva-min-loop-unroll",
                     "-eva-widening-delay", "-eva-widening-period",
                     "-eva-slevel-function", "-eva-split-limit",
                     "-eva-oracle-depth", "-eva-octagon-through-calls",
                     "-eva-equality-through-calls", "-eva-multidim-disjunctive-invariants")


def option_values(argv, name):
    """Values of an option in an argument vector, in both forms -opt v and
    -opt=v."""
    values = []
    for i, arg in enumerate(argv):
        if arg == name and i + 1 < len(argv):
            values.append(argv[i + 1])
        elif arg.startswith(name + "="):
            values.append(arg[len(name) + 1:])
    return values


def manifest_row(case, target, directory, revision, tree, parse_argv,
                 eva_argv, sources):
    fc_dir = directory + "/.frama-c"
    entry = (option_values(eva_argv, "-main")
             or option_values(parse_argv, "-main") or ["main"])[-1]
    domains = option_values(eva_argv, "-eva-domains")
    precision = []
    for opt in PRECISION_OPTIONS:
        for value in option_values(eva_argv, opt):
            precision.append("%s=%s" % (opt, value))
    harness = [s for s in sources
               if not s.startswith(("../", "/", "${FRAMAC_SHARE}"))]
    machdep = (option_values(parse_argv, "-machdep") or [""])[-1]
    parse_flags = [a for a in parse_argv if a not in sources]
    config = json.dumps([parse_flags, eva_argv, sources], sort_keys=True)
    return [case, target, directory, "default", revision, tree, entry,
            ",".join(domains) or "cvalue", " ".join(precision) or "-",
            " ".join(harness) or "-", " ".join(sources), machdep or "-",
            shlex.join(parse_flags), shlex.join(eva_argv),
            hashlib.sha256(config.encode()).hexdigest()]


def manifest_command(args):
    """Builds the manifest from a snapshot of the case studies in which
    make has written the command files of each target (see
    tools/make-manifest.sh)."""
    rows = []
    with open(args.targets) as f:
        targets = [l.strip() for l in f if l.strip()]
    for entry in targets:
        directory, _, target_file = entry.partition("/.frama-c/")
        target = target_file[:-len(".eva")]
        base = os.path.join(args.snapshot, directory, ".frama-c")
        with open(os.path.join(base, target + ".parse", "command")) as f:
            parse_argv = shlex.split(f.read())[1:]
        with open(os.path.join(base, target + ".eva", "command")) as f:
            eva_argv = shlex.split(f.read())[1:]
        # Paths into the build of Frama-C do not depend on the case: they
        # are written relative to ${FRAMAC_SHARE} and ${FRAMAC_LIB}. Paths
        # into the temporary snapshot, such as the one of a
        # -ffile-prefix-map option, are written relative to ${SNAPSHOT}, so
        # that the manifest and its digests do not depend on where the
        # snapshot was made.
        snapshots = sorted({args.snapshot.rstrip("/"),
                            os.path.realpath(args.snapshot)},
                           key=len, reverse=True)
        for path, name in ([(args.share, "${FRAMAC_SHARE}"),
                            (args.lib, "${FRAMAC_LIB}")]
                           + [(p, "${SNAPSHOT}") for p in snapshots]):
            if path:
                path = path.rstrip("/")
                parse_argv = [a.replace(path, name) for a in parse_argv]
                eva_argv = [a.replace(path, name) for a in eva_argv]
        sources = [a for a in parse_argv
                   if a.endswith((".c", ".i", ".h", ".json"))
                   and not a.startswith("-")]
        tree = (getattr(args, "trees", None) or {}).get(directory, "")
        case = "%s/%s.eva/default" % (directory, target)
        rows.append(manifest_row(case, target + ".eva", directory,
                                 args.revision, tree, parse_argv, eva_argv,
                                 sources))
    with open_text(args.output, "w") as f:
        f.write("# Cases of the campaign: one target of the case studies "
                "with one fixed configuration.\n")
        f.write("# Generated by tools/make-manifest.sh at revision %s.\n"
                % args.revision)
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(MANIFEST_HEADER)
        writer.writerows(rows)
    return 0


def read_manifest(path):
    with open_text(path) as f:
        return list(csv.DictReader((l for l in f if not l.startswith("#")),
                                   delimiter="\t"))


def manifest_get_command(args):
    """Prints one field of the manifest rows of the given cases."""
    rows = {r["case"]: r for r in read_manifest(args.manifest)}
    for case in args.cases:
        if case not in rows:
            print("unknown case: " + case, file=sys.stderr)
            return 1
        print(rows[case][args.field])
    return 0


# ----- Command line --------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("records")
    p.add_argument("log")
    p.add_argument("output", nargs="?")
    p.set_defaults(func=records_command)
    p = sub.add_parser("align")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("output", nargs="?",
                   help="prefix of the output files")
    p.add_argument("--same-numbering", action="store_true",
                   help="both runs number the statements alike: the same "
                   "revision of the analyzer on the same case")
    p.set_defaults(func=align_command)
    p = sub.add_parser("queries")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("output", nargs="?")
    p.set_defaults(func=queries_command)
    p = sub.add_parser("alarms")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--root-a", action="append",
                   help="root of the sources of run A, written ${SRC}")
    p.add_argument("--root-b", action="append",
                   help="root of the sources of run B, written ${SRC}")
    p.set_defaults(func=alarms_command)
    p = sub.add_parser("counts")
    p.add_argument("stats")
    p.add_argument("--families",
                   help="counter families of the binary, comma-separated "
                   "(default: every family is measured)")
    p.add_argument("--flags", help="Eva options of the run")
    p.set_defaults(func=counts_command)
    p = sub.add_parser("families")
    p.add_argument("cmxs", help="the compiled Eva plugin of a binary")
    p.set_defaults(func=families_command)
    p = sub.add_parser("provenance")
    p.add_argument("checkout")
    p.add_argument("role")
    p.add_argument("patches", help="directory that receives ROLE.patch")
    p.set_defaults(func=provenance_command)
    p = sub.add_parser("measure")
    p.add_argument("measure")
    p.set_defaults(func=measure_command)
    p = sub.add_parser("outcome")
    p.add_argument("run")
    p.add_argument("parse_exit", type=int)
    p.add_argument("make_exit", type=int)
    p.add_argument("timeout", type=float)
    p.set_defaults(func=outcome_command)
    p = sub.add_parser("tables")
    p.add_argument("run_dir")
    p.add_argument("--recorded-set-a")
    p.set_defaults(func=tables_command)
    p = sub.add_parser("manifest")
    p.add_argument("snapshot")
    p.add_argument("targets")
    p.add_argument("revision")
    p.add_argument("output")
    p.add_argument("--trees")
    p.add_argument("--share",
                   help="share directory of the Frama-C build, written "
                   "${FRAMAC_SHARE} in the manifest")
    p.add_argument("--lib",
                   help="library directory of the Frama-C build, written "
                   "${FRAMAC_LIB} in the manifest")
    p.set_defaults(func=manifest_command)
    p = sub.add_parser("manifest-get")
    p.add_argument("manifest")
    p.add_argument("field")
    p.add_argument("cases", nargs="+")
    p.set_defaults(func=manifest_get_command)
    args = parser.parse_args(argv)
    if getattr(args, "trees", None) is not None and \
       isinstance(args.trees, str):
        trees = {}
        with open(args.trees) as f:
            for line in f:
                directory, _, tree = line.strip().partition("\t")
                trees[directory] = tree
        args.trees = trees
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
