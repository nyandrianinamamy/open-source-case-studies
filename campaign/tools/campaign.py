#!/usr/bin/env python3
"""Tools of the case-study campaign: records, alignment, queries, tables.

Subcommands:
  records LOG [OUT]          per-call records of one Eva log, as JSON lines
  align A B [OUT_PREFIX]     align the per-call records of two runs
  queries A B [OUT_PREFIX]   compare the state-query answers of two runs
  alarms A B                 compare two alarms.csv files
  counts STATS               builtin applications and cache activity of a run
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
FRAME = re.compile(r"^(.*?) :: (.*)$")


def parse_stack(text):
    """Parses a printed Eva callstack. Returns (entry point, frames), the
    frames being (called function, call site) pairs from the outermost call
    to the innermost one."""
    text = " ".join(text.split())
    text = re.sub(r"^<[^>]*> ", "", text)  # callstack hash, if printed
    parts = text.split(" <- ")
    frames = []
    for part in parts[:-1]:
        match = FRAME.match(part)
        if not match:
            raise ValueError("malformed callstack frame: %r" % part)
        frames.append((match.group(1), match.group(2)))
    frames.reverse()
    return parts[-1], frames


def parse_cache_message(text):
    """Parses the text of one message of the category cache.

    Returns a dictionary with the location of the call (empty for the entry
    point), the called function, the dispositions in their order (every
    field is kept verbatim, known or not) and the callstack, or None when
    the message is not a call disposition."""
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
    }
    if stack:
        entry, frames = parse_stack(stack)
        record["entry_point"] = entry
        record["frames"] = frames
    return record


def cache_records(lines):
    """The per-call records of a log, in the order of their messages."""
    records = []
    for plugin, category, text in messages(lines):
        if plugin == "eva" and category == "cache":
            record = parse_cache_message(text)
            if record is not None:
                record["seq"] = len(records)
                records.append(record)
    return records


# ----- Call tree and invocation identity -------------------------------------

BODY_EXECUTIONS = ("analysed", "interrupted")


def kinds(record):
    d = record["dispositions"]
    return (disposition_kind(d.get("lookup", "")),
            disposition_kind(d.get("execution", "")),
            disposition_kind(d.get("storage", "")))


def build_tree(records):
    """Links each record to the record of its caller and gives it an
    invocation identity.

    Eva prints the message of an analysed or interrupted call after the
    messages of the calls made by its body, and the message of a hit at the
    lookup. The parent of a record whose callstack is S is therefore the
    first later record with an analysed or interrupted body whose callstack
    is S without its last call. Records whose parent never printed a message
    (a run killed during the analysis) get an open parent built from their
    callstack. The identity of a record is the identity of its parent,
    followed by FUNCTION@SITE#K where K counts the earlier siblings with the
    same function and call site.

    Returns (roots, problems)."""
    problems = []
    pending = defaultdict(list)  # depth -> records waiting for their parent
    roots = []
    for record in records:
        if "frames" not in record:
            raise ValueError(
                "message %d has no callstack: enable the categories "
                "cache and callstacks" % record["seq"])
        depth = len(record["frames"])
        record["children"] = []
        executed = kinds(record)[1] in BODY_EXECUTIONS
        waiting = pending.pop(depth + 1, [])
        if waiting and not executed:
            problems.append(
                "record %d: %d nested records before a call without a body"
                % (record["seq"], len(waiting)))
        for child in waiting:
            if child["frames"][:-1] != record["frames"] or \
               child["entry_point"] != record["entry_point"]:
                problems.append("record %d: nested record %d has another "
                                "caller" % (record["seq"], child["seq"]))
            record["children"].append(child)
        if depth == 0:
            roots.append(record)
        else:
            pending[depth].append(record)
    # Records left without a parent: the analysis stopped before the parent
    # printed its message. Open parents are rebuilt from the callstacks.
    for depth in sorted(pending, reverse=True):
        for record in pending[depth]:
            problems.append("record %d has no parent message" % record["seq"])
            attach_open_parent(record, roots, pending)
    roots.sort(key=lambda r: first_seq(r))
    counter = Counter()
    for root in roots:
        key = root["entry_point"] if "frames" in root else root["function"]
        root["id"] = "%s#%d" % (key, counter[key])
        counter[key] += 1
        assign_ids(root)
    return roots, problems


def first_seq(record):
    if record.get("seq") is not None:
        return record["seq"]
    return min((first_seq(c) for c in record["children"]), default=0)


def attach_open_parent(record, roots, pending):
    """Attaches [record] to an open parent made from its callstack."""
    frames = record["frames"][:-1]
    depth = len(frames)
    siblings = roots if depth == 0 else pending[depth]
    for candidate in siblings:
        if candidate.get("open") and candidate["frames"] == frames:
            candidate["children"].append(record)
            return
    parent = {
        "seq": None, "open": True, "frames": frames,
        "entry_point": record["entry_point"],
        "function": frames[-1][0] if frames else record["entry_point"],
        "site": frames[-1][1] if frames else "",
        "dispositions": OrderedDict(execution="open (no message)"),
        "children": [record],
    }
    if depth == 0:
        roots.append(parent)
    else:
        attach_open_parent(parent, roots, pending)


def assign_ids(record):
    counter = Counter()
    record["children"].sort(key=first_seq)
    for child in record["children"]:
        key = "%s@%s" % (child["function"], child["site"])
        child["id"] = "%s > %s#%d" % (record["id"], key, counter[key])
        child["parent"] = record["id"]
        counter[key] += 1
        assign_ids(child)


def walk(record):
    yield record
    for child in record["children"]:
        yield from walk(child)


def records_command(args):
    with open_text(args.log) as lines:
        records = cache_records(lines)
    roots, problems = build_tree(records)
    producers = {}
    for root in roots:
        for record in walk(root):
            match = ENTRY.search(record["dispositions"].get("storage", ""))
            if match and kinds(record)[2] == "stored":
                producers[match.group(1)] = record["id"]
    out = open_text(args.output, "w") if args.output else sys.stdout
    for root in roots:
        for record in walk(root):
            lookup, execution, storage = kinds(record)
            row = OrderedDict()
            row["id"] = record["id"]
            row["parent"] = record.get("parent")
            row["seq"] = record["seq"]
            row["function"] = record["function"]
            row["site"] = record["site"]
            row["entry_point"] = record["entry_point"]
            row["callstack"] = [list(f) for f in record["frames"]]
            row["dispositions"] = record["dispositions"]
            row["lookup"], row["execution"], row["storage"] = \
                lookup, execution, storage
            match = ENTRY.search(record["dispositions"].get("lookup", ""))
            row["hit_of"] = (producers.get(match.group(1))
                             if match and lookup == "hit" else None)
            row["children"] = len(record["children"])
            out.write(json.dumps(row) + "\n")
    for problem in problems:
        print("problem: " + problem, file=sys.stderr)
    if out is not sys.stdout:
        out.close()
    return 0


def load_records(path):
    with open_text(path) as f:
        return [json.loads(line) for line in f if line.strip()]


# ----- Alignment of two runs -------------------------------------------------

def child_key(row):
    return "%s@%s" % (row["function"], row["site"])


def descendants(row, children):
    count = 0
    for child in children.get(row["id"], []):
        count += 1 + descendants(child, children)
    return count


def align(rows_a, rows_b):
    """Aligns the per-call records of two runs, from the entry point down.

    Two records are aligned when their parents are aligned and they have the
    same function and call site, with:
    - the same sequence of (function, call site) among the siblings on both
      sides: siblings are aligned by position;
    - otherwise, a (function, call site) that occurs exactly once on each
      side.
    Any other group of siblings is undecided: its records are reported and
    not aligned. The records nested in a call that is a hit in one run and
    analysed in the other are reported as nested under a hit; records present
    in one run only are reported as unmatched."""
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
        if keys_a == keys_b:
            for x, y in zip(kids_a, kids_b):
                visit(x, y)
            return
        count_a, count_b = Counter(keys_a), Counter(keys_b)
        for key in sorted(set(count_a) | set(count_b)):
            group_a = [r for r in kids_a if child_key(r) == key]
            group_b = [r for r in kids_b if child_key(r) == key]
            if count_a[key] == 1 and count_b[key] == 1:
                visit(group_a[0], group_b[0])
            elif not group_a or not group_b:
                for r in group_a:
                    unmatched("A", r, children_a, "no call at this site in B")
                for r in group_b:
                    unmatched("B", r, children_b, "no call at this site in A")
            else:
                size_a = sum(1 + descendants(r, children_a) for r in group_a)
                size_b = sum(1 + descendants(r, children_b) for r in group_b)
                result["undecided"].append(
                    (a["id"], b["id"], key, len(group_a), len(group_b),
                     size_a, size_b))

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


def summarize_alignment(rows_a, rows_b, result):
    """Counts of an alignment, with the number of records of each run."""
    pairs = result["pairs"]
    same = sum(1 for a, b in pairs if a["dispositions"] == b["dispositions"])
    undecided_a = sum(g[5] for g in result["undecided"])
    undecided_b = sum(g[6] for g in result["undecided"])
    summary = OrderedDict()
    summary["records_a"] = len(rows_a)
    summary["records_b"] = len(rows_b)
    summary["aligned"] = len(pairs)
    summary["aligned_same_dispositions"] = same
    summary["aligned_other_dispositions"] = len(pairs) - same
    summary["hit_a_analysed_b"] = sum(
        1 for a, b in pairs if a["lookup"] == "hit" and b["lookup"] != "hit")
    summary["analysed_a_hit_b"] = sum(
        1 for a, b in pairs if a["lookup"] != "hit" and b["lookup"] == "hit")
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
    accounted_a = (len(pairs) + summary["nested_under_hit_b"]
                   + summary["unmatched_a"] + undecided_a)
    accounted_b = (len(pairs) + summary["nested_under_hit_a"]
                   + summary["unmatched_b"] + undecided_b)
    summary["complete"] = (accounted_a == len(rows_a)
                           and accounted_b == len(rows_b)
                           and len(pairs) == len(rows_a) == len(rows_b))
    summary["accounted"] = (accounted_a == len(rows_a)
                            and accounted_b == len(rows_b))
    return summary


def write_tsv(path, header, rows):
    with open_text(path, "w") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def align_command(args):
    rows_a, rows_b = load_records(args.a), load_records(args.b)
    result = align(rows_a, rows_b)
    summary = summarize_alignment(rows_a, rows_b, result)
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
                   "records_a", "records_b"], result["undecided"])
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


def ival_included(a, b):
    if a[0] == "bottom":
        return True
    if b[0] == "bottom":
        return False
    if a[0] == "float" or b[0] == "float":
        if a[0] != b[0]:
            # Integer and float forms of an ival: no element in common
            # except through bottom, handled above.
            return False
        if a[1] is None:
            return b[3]
        if b[1] is None:
            return False
        return (fkey(a[1]) >= fkey(b[1]) and fkey(a[2]) <= fkey(b[2])
                and (not a[3] or b[3]))
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
    """An answer that gives no information on a scalar: the top value, a
    garbled mix, or an integer ival with no bound."""
    if value in ("T",) or value.startswith("G"):
        return True
    if value.startswith("M"):
        try:
            entries = parse_value(value)[1]
        except Undecided:
            return False
        return any(i[0] == "itv" and i[1] is None and i[2] is None
                   and i[4] <= 1 for i in entries.values())
    return False


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
    reach, answers, errors, complete = set(), {}, {}, False
    with open_text(path) as f:
        for line in f:
            fields = line.rstrip("\n").split("\t")
            if fields[0] == "reach":
                reach.add((fields[1], fields[2]))
            elif fields[0] == "answer":
                key = tuple(fields[1:6])
                answers[key] = (int(fields[6]), int(fields[7]), fields[8])
            elif fields[0] == "error":
                errors[tuple(fields[1:6])] = fields[6]
            elif fields[0] == "done":
                complete = True
    return reach, answers, errors, complete


def compare_queries(path_a, path_b):
    reach_a, ans_a, err_a, done_a = load_queries(path_a)
    reach_b, ans_b, err_b, done_b = load_queries(path_b)
    keys = set(ans_a) | set(ans_b) | set(err_a) | set(err_b)
    counts = Counter()
    details = []
    for key in sorted(keys):
        stmt = (key[0], key[1])
        a, b = ans_a.get(key), ans_b.get(key)
        if a is not None and b is not None:
            verdict = classify(a, b)
            counts[verdict] += 1
            if verdict != "equal":
                details.append(key + (verdict, a[2], b[2]))
            for side, answer in (("a", a), ("b", b)):
                if is_top_answer(answer[2]):
                    counts["top_" + side] += 1
            continue
        for side, answer, reach, errors in (("a", a, reach_a, err_a),
                                            ("b", b, reach_b, err_b)):
            if answer is None:
                if key in errors:
                    reason = "error"
                elif stmt not in reach:
                    reason = "unreached"
                elif key[3] != "*":
                    reason = "no-callstack"
                else:
                    reason = "missing"
                counts["unavailable_%s_%s" % (side, reason)] += 1
                other = b if side == "a" else a
                details.append(key + ("unavailable in " + side.upper()
                                      + " (" + reason + ")",
                                      a[2] if a else "", b[2] if b else ""))
    summary = OrderedDict()
    summary["queries"] = len(keys)
    summary["answered_both"] = sum(counts[k] for k in (
        "equal", "wider", "narrower", "incomparable", "undecided"))
    for k in ("equal", "wider", "narrower", "incomparable", "undecided",
              "top_a", "top_b"):
        summary[k] = counts[k]
    for side in ("a", "b"):
        for reason in ("unreached", "no-callstack", "error", "missing"):
            summary["unavailable_%s_%s" % (side, reason)] = \
                counts["unavailable_%s_%s" % (side, reason)]
    summary["reached_a"] = len(reach_a)
    summary["reached_b"] = len(reach_b)
    summary["reached_a_only"] = len(reach_a - reach_b)
    summary["reached_b_only"] = len(reach_b - reach_a)
    summary["complete_a"] = done_a
    summary["complete_b"] = done_b
    return summary, details


def queries_command(args):
    summary, details = compare_queries(args.a, args.b)
    if args.output:
        with open_text(args.output + "summary.tsv", "w") as f:
            for key, value in summary.items():
                f.write("%s\t%s\n" % (key, value))
        write_tsv(args.output + "differences.tsv",
                  ["function", "stmt", "point", "callstack", "lvalue",
                   "verdict", "answer_a", "answer_b"], details)
    for key, value in summary.items():
        print("%s\t%s" % (key, value))
    return 0


# ----- Alarms ------------------------------------------------------------

def load_alarms(path):
    """The alarms and properties of an alarms.csv file written by
    -report-csv: (file, line, function, kind, property) -> status."""
    result = {}
    with open_text(path) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            key = (row["file"], row["line"], row["function"],
                   row["property kind"], row["property"])
            result[key] = row["status"]
    return result


def compare_alarms(path_a, path_b):
    a, b = load_alarms(path_a), load_alarms(path_b)
    summary = OrderedDict()
    summary["properties_a"] = len(a)
    summary["properties_b"] = len(b)
    summary["same_status"] = sum(1 for k in a if k in b and a[k] == b[k])
    summary["other_status"] = sum(1 for k in a if k in b and a[k] != b[k])
    summary["a_only"] = sum(1 for k in a if k not in b)
    summary["b_only"] = sum(1 for k in b if k not in a)
    details = [k + (a.get(k, ""), b.get(k, ""))
               for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
    return summary, details


def alarms_command(args):
    summary, details = compare_alarms(args.a, args.b)
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


def run_counts(stats_path):
    """Builtin applications and cache activity from an Eva statistics
    file (-eva-statistics-file)."""
    builtins = Counter()
    other_builtins = Counter()
    cache = Counter()
    refused = Counter()
    with open_text(stats_path) as f:
        for line in f:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 4:
                continue
            name, value = fields[0], fields[3]
            if name.startswith("builtin-applied-"):
                builtin = name[len("builtin-applied-"):]
                canonical = CANONICAL_BUILTINS.get(builtin)
                if canonical:
                    builtins[canonical] += int(value)
                else:
                    other_builtins[builtin] += int(value)
            elif name.startswith("memexec-refused-"):
                refused[name[len("memexec-refused-"):]] += int(value)
            elif name.startswith("memexec-"):
                cache[name[len("memexec-"):]] += int(value)
    counts = OrderedDict()
    for k in ALLOCATION + RELEASE:
        counts[k] = builtins[k]
    counts["allocation_and_release"] = sum(builtins.values())
    counts["in_set_a"] = sum(builtins.values()) == 0
    counts["hits"] = cache["hits"]
    counts["misses"] = cache["misses"]
    counts["stored"] = cache["stored"]
    counts["refused"] = sum(refused.values())
    counts["refused_by_reason"] = ",".join(
        "%s=%d" % kv for kv in sorted(refused.items()))
    return counts


def function_counts(stats_path):
    """Cache activity per function from an Eva statistics file: rows
    [function, hits, misses, stored, refused], sorted by function."""
    table = defaultdict(Counter)
    with open_text(stats_path) as f:
        for line in f:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 4 or not fields[0].startswith("memexec-"):
                continue
            name = fields[0][len("memexec-"):]
            if name.startswith("refused-"):
                name = "refused"
            table[fields[1]][name] += int(fields[3])
    return [[kf, c["hits"], c["misses"], c["stored"], c["refused"]]
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
    for key, value in run_counts(args.stats).items():
        print("%s\t%s" % (key, value))
    return 0


# ----- Outcome of a run ----------------------------------------------------

# Messages of Frama-C and of the OCaml runtime when memory is exhausted.
OUT_OF_MEMORY = re.compile(
    r"^\[kernel\] Unexpected error \(Out of memory\)|"
    r"^Fatal error: (exception Out of memory|out of memory|"
    r"Not enough heap memory|allocation failure)", re.M)
SIGNAL = re.compile(r"^Command terminated by signal (\d+)", re.M)


def read_measure(path):
    """The values written by GNU time for the measured invocation. When the
    command was killed by a signal, GNU time writes status 0 and a line
    naming the signal: the status is then 128 plus the signal."""
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


def classify_outcome(parse_exit, make_exit, measure, log_text,
                     entry_analysed, timeout_s):
    """The outcome of one run:
    - parse-error: the parsing step failed, Eva did not run;
    - harness-error: the Eva invocation was not measured, or make failed
      after a successful invocation;
    - oom: Frama-C or the OCaml runtime reports that memory is exhausted;
    - timeout: the invocation reached its wall-time limit (status 124 of
      timeout, or 137 when it was killed after the limit);
    - killed: killed by SIGKILL before the limit, as by the out-of-memory
      killer of the system;
    - error: any other nonzero exit status, such as 1 (invalid user input),
      3 (unimplemented feature), 4 (internal error), 125 (unexpected
      exception) or a signal;
    - incomplete: exit status 0 but the analysis of the entry point did
      not end;
    - completed."""
    if parse_exit != 0:
        return "parse-error"
    if measure is None:
        return "harness-error"
    status = int(measure["status"])
    elapsed = float(measure["elapsed_s"])
    if OUT_OF_MEMORY.search(log_text):
        return "oom"
    if status == 124:
        return "timeout"
    if status == 137:
        return "timeout" if elapsed >= timeout_s else "killed"
    if status != 0:
        return "error"
    if make_exit != 0:
        return "harness-error"
    if not entry_analysed:
        return "incomplete"
    return "completed"


def measure_command(args):
    """Prints the measure of a run as key-value lines."""
    for key, value in (read_measure(args.measure) or {}).items():
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
    print(classify_outcome(args.parse_exit, args.make_exit, measure,
                           log_text, entry_analysed, args.timeout))
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


def tables_command(args):
    root = args.run_dir
    runs_dir = os.path.join(root, "runs")
    runs = []
    for dirpath, _, filenames in os.walk(runs_dir):
        if "run.tsv" in filenames:
            runs.append(read_kv(os.path.join(dirpath, "run.tsv")))
    runs.sort(key=lambda r: (r.get("case", ""), r.get("mode", "")))
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
             "`%s`.\n\n" % os.path.basename(os.path.abspath(root)))

    # Outcomes, time and memory.
    header = ["case", "mode", "outcome", "exit", "elapsed_s", "user_s",
              "maxrss_kib", "limit_s"]
    rows = [[r.get(k) or "-" for k in ["case", "mode", "outcome", "exit",
                                        "elapsed_s", "user_s", "maxrss_kib",
                                        "timeout_s"]] for r in runs]
    write_tsv(os.path.join(out_dir, "outcomes.tsv"), header, rows)
    md.write("## Outcomes, time and memory per invocation\n\n")
    md.write(markdown_table(header, rows) + "\n")

    # Cache activity and builtin applications.
    header = ["case", "mode", "hits", "misses", "stored", "refused",
              "refused_by_reason", "allocation_and_release", "in_set_a",
              "recorded_in_set_a", "agrees"]
    rows = []
    for r in runs:
        stats = os.path.join(root, "runs", r["case"], r["mode"],
                             "eva-stats.csv")
        if not os.path.exists(stats):
            rows.append([r["case"], r["mode"]] + ["n/a"] * 9)
            continue
        c = run_counts(stats)
        target = r["case"].rsplit("/", 1)[0]
        rec = recorded.get(target, "")
        mine = "True" if c["in_set_a"] else "False"
        rows.append([r["case"], r["mode"], c["hits"], c["misses"],
                     c["stored"], c["refused"], c["refused_by_reason"] or "-",
                     c["allocation_and_release"], mine, rec or "n/a",
                     ("yes" if rec == mine else "NO") if rec else "n/a"])
    write_tsv(os.path.join(out_dir, "activity.tsv"), header, rows)
    md.write("## Cache activity and set A\n\nTotals per case of the "
             "statistics file. `allocation_and_release` sums the "
             "applications of the allocation and release builtins; a run "
             "is in set A when it is 0. `recorded_in_set_a` is the "
             "membership recorded by the earlier measurement.\n\n")
    md.write(markdown_table(header, rows) + "\n")

    # Cache activity per function, in a file of its own.
    rows = []
    for r in runs:
        stats = os.path.join(root, "runs", r["case"], r["mode"],
                             "eva-stats.csv")
        if os.path.exists(stats):
            rows.extend([r["case"], r["mode"]] + row
                        for row in function_counts(stats))
    write_tsv(os.path.join(out_dir, "functions.tsv"),
              ["case", "mode", "function", "hits", "misses", "stored",
               "refused"], rows)
    md.write("The hits, misses, stores and refusals per function are in "
             "`functions.tsv`.\n\n")

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
    align_keys = ["records_a", "records_b", "aligned",
                  "aligned_other_dispositions", "hit_a_analysed_b",
                  "analysed_a_hit_b", "nested_under_hit_a",
                  "nested_under_hit_b", "unmatched_a", "unmatched_b",
                  "undecided_groups", "accounted", "complete"]
    query_keys = ["queries", "answered_both", "equal", "wider", "narrower",
                  "incomparable", "undecided", "top_a", "top_b",
                  "unavailable_a_no-callstack", "unavailable_b_no-callstack",
                  "unavailable_a_unreached", "unavailable_b_unreached",
                  "reached_a_only", "reached_b_only"]
    alarm_keys = ["properties_a", "properties_b", "same_status",
                  "other_status", "a_only", "b_only"]
    for title, name, keys in (
            ("Alignment of the per-call records", "alignment", align_keys),
            ("State queries", "queries", query_keys),
            ("Alarms and property statuses", "alarms", alarm_keys)):
        header = ["case", "A", "B"] + keys
        rows = []
        for dirpath, pair in comparisons:
            values = read_kv(os.path.join(dirpath, name + "-summary.tsv"))
            if not values:
                rows.append([pair["case"], pair["baseline"],
                             pair["candidate"]] + ["n/a"] * len(keys))
                continue
            rows.append([pair["case"], pair["baseline"], pair["candidate"]]
                        + [values.get(k) or "-" for k in keys])
        write_tsv(os.path.join(out_dir, name + ".tsv"), header, rows)
        md.write("## %s\n\nRun A is the baseline, run B the candidate.\n\n"
                 % title)
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
        # are written relative to ${FRAMAC_SHARE} and ${FRAMAC_LIB}.
        for path, name in ((args.share, "${FRAMAC_SHARE}"),
                           (args.lib, "${FRAMAC_LIB}")):
            if path:
                path = path.rstrip("/")
                parse_argv = [a.replace(path, name) for a in parse_argv]
                eva_argv = [a.replace(path, name) for a in eva_argv]
        sources = [a for a in parse_argv
                   if a.endswith((".c", ".i", ".h", ".json"))
                   and not a.startswith("-")]
        tree = args.trees.get(directory, "") if hasattr(args, "trees") else ""
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
    p.set_defaults(func=align_command)
    p = sub.add_parser("queries")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("output", nargs="?")
    p.set_defaults(func=queries_command)
    p = sub.add_parser("alarms")
    p.add_argument("a")
    p.add_argument("b")
    p.set_defaults(func=alarms_command)
    p = sub.add_parser("counts")
    p.add_argument("stats")
    p.set_defaults(func=counts_command)
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
