#!/usr/bin/env -S python3 -I
"""Tools of the case-study campaign: records, alignment, queries, tables.

Subcommands:
  records LOG [OUT]          per-call records of one Eva log, as JSON lines
  align A B [OUT_PREFIX]     align the per-call records of two runs
  queries A B [OUT_PREFIX]   compare the state-query answers of two runs
  alarms A B                 compare two alarms.csv files
  counts STATS [--log LOG]   counters of a statistics file, and the
                             dispositions counted in the log of its run
  families CMXS              counter names held by a compiled Eva plugin
  provenance CHECKOUT ROLE DIR  revision and patch of a Frama-C checkout
  home ACTION ...            find or write ~ for the home directory
  tables RUN_DIR             result tables of a campaign output directory
  ast LISTING                SHA-256 of an AST listing of the query module
  preprocessing LOG TMPDIR   digests of the preprocessing of a parse step
  compare OUTPUT CASE A B    compare two runs of a case as the runner does
  recompute RUN_DIR          records, outcomes, comparisons and tables again
  manifest ...               see manifest --help

Only the Python standard library is used. Run with python3 -I.
"""

import argparse
import contextlib
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
import zlib
from collections import Counter, OrderedDict, defaultdict


# A count, a status or a version written in a file of the tools: ASCII
# digits, at most 18. str.isdigit accepts other digits, such as superscripts,
# that int then rejects, and int rejects a decimal of several thousand
# digits: a file that holds one is malformed, never a reason to stop.
DECIMAL = re.compile(r"[0-9]{1,18}")


def decimal(text):
    """The value of [text] when it is a bounded ASCII decimal, else None."""
    return int(text) if DECIMAL.fullmatch(text or "") else None


def open_text(path, mode="r"):
    """Opens a text file, compressed with gzip when its name ends in .gz."""
    if path == "-":
        return sys.stdin if "r" in mode else sys.stdout
    if path.endswith(".gz"):
        return gzip.open(path, mode + "t", encoding="utf-8", errors="replace")
    return open(path, mode, encoding="utf-8", errors="replace")


class TSVError(ValueError):
    pass


def validate_tsv_header(path, fields, expected):
    fields = fields or []
    problems = []
    duplicates = [name for name, count in Counter(fields).items() if count > 1]
    missing = [name for name in expected if name not in fields]
    unknown = [name for name in fields if name not in expected]
    for label, names in (("duplicate", duplicates), ("missing", missing),
                         ("unknown", unknown)):
        if names:
            problems.append("%s column(s) %s" % (label, ", ".join(map(repr, names))))
    if problems:
        raise TSVError("%s: %s" % (path, "; ".join(problems)))


def read_header_tsv(path, expected, comments=False):
    """Read a named-column TSV after checking its schema."""
    with open_text(path) as f:
        lines = (line for line in f if not line.startswith("#")) if comments else f
        reader = csv.DictReader(lines, delimiter="\t", strict=True)
        try:
            validate_tsv_header(path, reader.fieldnames, expected)
            for row in reader:
                if None in row or None in row.values():
                    raise TSVError("%s: row %d has the wrong number of columns"
                                   % (path, reader.line_num))
                yield row
        except csv.Error as error:
            raise TSVError("%s: %s" % (path, error)) from error


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


ENTRY = re.compile(r"\bentry ([0-9]{1,18})\b")
REJECTED = re.compile(r"^rejected \(entry ([0-9]{1,18}): (.*)\)$")
HIT = re.compile(r"^hit \(entry ([0-9]{1,18})\)$")


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
FRAME = re.compile(r"^(.*?) :: (.*?)(?: \(stmt ([0-9]{1,18})\))?$")


def parse_stack(text):
    """Parses a printed Eva callstack. Returns (entry point, frames), the
    frames being (called function, call site, statement number or None)
    from the outermost call to the innermost one. Raises ValueError on a
    frame that does not have the form FUNCTION :: SITE."""
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
    is not a call disposition. Raises ValueError on a malformed callstack."""
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


IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SITE = re.compile(r"^\S.*:[0-9]{1,18}$")


def stack_problem(record, numbered):
    """Why the callstack of a record is malformed, or None. The terminal
    frame is the name of an entry point. A record without other frames is
    the call of that entry point, whose message has no location; every
    other record has a location, and each of its frames a function name and
    a call site FILE:LINE, with the number of its statement when the log
    numbers the statements; its innermost frame is the called function. A
    log cut inside a message leaves such a record."""
    entry, frames = record["entry_point"], record["frames"]
    if not IDENTIFIER.match(entry):
        return "malformed callstack: entry point %r" % entry
    if not frames and (record["function"] != entry or record["site"]):
        return ("malformed callstack: %s at %s is not the entry point %s"
                % (record["function"], record["site"] or "no location",
                   entry))
    if frames and not record["site"]:
        return "malformed message: the call to %s has no location" \
            % record["function"]
    for function, site, stmt in frames:
        if not IDENTIFIER.match(function) or not SITE.match(site) or \
           (numbered and stmt is None):
            return "malformed callstack frame: %s :: %s%s" % (
                function, site, "" if stmt is None else " (stmt %d)" % stmt)
    if frames and frames[-1][0] != record["function"]:
        return ("malformed callstack: the innermost frame %s is not the "
                "called function %s" % (frames[-1][0], record["function"]))
    return None


def parse_log(lines):
    """The per-call records of a log, in the order of their messages, and
    the structural problems of the log.

    A message of the categories cache and cache-producer that is not a call
    disposition, has no callstack or has a malformed one is a problem, and
    gives no record: a log cut inside a message leaves one. The log numbers
    the statements when a frame of one of its messages has a number; then
    every frame must have one."""
    parsed, problems = [], []
    count = 0
    for plugin, category, text in messages(lines):
        if plugin != "eva" or category not in ("cache", "cache-producer"):
            continue
        count += 1
        try:
            record = parse_cache_message(text)
        except ValueError as e:
            problems.append("message %d: %s" % (count, e))
            continue
        if record is None:
            problems.append("message %d is not a call disposition: %r"
                            % (count, " ".join(text.split())[:80]))
        elif "frames" not in record:
            problems.append("message %d has no callstack: enable the "
                            "categories cache and callstacks" % count)
        else:
            record["message"] = count
            parsed.append(record)
    numbered = any(f[2] is not None for r in parsed for f in r["frames"])
    records = []
    for record in parsed:
        problem = stack_problem(record, numbered)
        if problem:
            problems.append("message %d: %s" % (record["message"], problem))
            continue
        record["seq"] = len(records)
        records.append(record)
    return records, problems


def cache_records(lines):
    """The well-formed per-call records of a log, in the order of their
    messages."""
    return parse_log(lines)[0]


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
        records, problems = parse_log(lines)
    roots, tree_problems = build_tree(records)
    problems += tree_problems
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


# The evidence that two runs number the statements of their programs alike.
# A run of this runner records the digest of the listing of its AST
# (ast_sha256, of the format AST_FORMAT) and the digests of its
# preprocessing (pp_command_sha256 and pp_text_sha256, see
# preprocessing_evidence). The numbering of two runs is:
# - same: equal AST digests and equal preprocessing digests;
# - preprocessing differs: equal AST digests, but the preprocessing digests
#   differ;
# - different: the AST digests differ;
# - recorded command: runs of an archive whose AST was listed again
#   afterwards (ast_source imported) and that have no preprocessing digest:
#   equal AST digests, and equal preprocessing recorded by their commands
#   (recorded_preprocessing); the preprocessed text was not compared;
# - asserted: runs recorded before the AST digest existed, whose numbering
#   is asserted, on the command line or by run_numbering; nothing of their
#   programs is compared;
# - not established: anything else, such as a digest missing or a listing
#   of another format.
# The pairs below the entry point depend on the statement numbers: they are
# made only when the numbering is same, recorded command or asserted, and
# only same makes an alignment complete.
AST_FORMAT = "2"
SHA256 = re.compile(r"[0-9a-f]{64}", re.I | re.ASCII)
NUMBERINGS = ("same", "preprocessing differs", "different",
              "recorded command", "not established", "asserted")
NUMBERING_REASONS = {"different": "AST digests differ",
                     "preprocessing differs": "preprocessing differs",
                     "not established": "numbering not established"}
# An asserted numbering rests on the fields that run_numbering compares in
# the two run.tsv, and on no digest: the verdict names those fields and
# claims nothing about the preprocessing.
ASSERTED_VERDICT = ("numbering asserted from equal recorded revisions, "
                    "patch and extra options, not checked by digest")
RECORDED_VERDICT = ("AST digests equal, preprocessing compared by the "
                    "recorded command only")
# The numberings that pair the calls below the entry point but leave an
# alignment incomplete: the reason, and the verdict when it is the only one.
WEAK_NUMBERING = {
    "asserted": ("numbering asserted, not checked by digest",
                 ASSERTED_VERDICT),
    "recorded command": ("preprocessing compared by the recorded command "
                         "only", RECORDED_VERDICT)}


def valid_sha256(digest):
    return SHA256.fullmatch(digest or "") is not None


def valid_preprocessing(pair):
    command, separator, text = (pair or "").partition(":")
    return bool(separator and valid_sha256(command) and valid_sha256(text))


def numbering_state(digest_a, digest_b, asserted=False, pp_a=None,
                    pp_b=None):
    """Compare two AST digests and two command:text digest pairs. An
    explicit assertion is available for runs recorded before AST digests."""
    digests = (digest_a, digest_b)
    if not all(valid_sha256(d) for d in digests):
        if (asserted and pp_a is None and pp_b is None
                and all(d is None or valid_sha256(d) for d in digests)):
            return "asserted"
        return "not established"
    if not (valid_preprocessing(pp_a) and valid_preprocessing(pp_b)):
        return "not established"
    if digest_a.lower() != digest_b.lower():
        return "different"
    return "same" if pp_a.lower() == pp_b.lower() else "preprocessing differs"


def align(rows_a, rows_b, numbering="not established"):
    """Aligns the per-call records of two runs, from the entry point down.

    Two records are aligned when their parents are aligned and they have the
    same function, call site and call statement, with:
    - the same sequence of (function, call site, statement) among the
      siblings on both sides: siblings are aligned by position;
    - otherwise, a (function, call site, statement) that occurs exactly once
      on each side.
    Any other group of siblings is undecided: its records are reported and
    not aligned. The statement numbers of two runs are compared only when
    [numbering] is same or asserted (see [numbering_state]): otherwise every
    group of siblings below the entry point is undecided. When a record does
    not give the number of its call statement (a log of a binary that does
    not print it), two calls on one line cannot be told apart: every group
    of siblings of its parent is undecided. The records nested in a call
    that is a hit in one run and analysed in the other are reported as
    nested under a hit; records present in one run only are reported as
    unmatched."""
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
        unpaired = NUMBERING_REASONS.get(numbering)
        if numbering not in WEAK_NUMBERING and numbering != "same":
            unpaired = unpaired or "numbering not established"
        if not unpaired and not no_number and keys_a == keys_b:
            for x, y in zip(kids_a, kids_b):
                visit(x, y)
            return
        count_a, count_b = Counter(keys_a), Counter(keys_b)
        for key in sorted(set(count_a) | set(count_b)):
            group_a = [r for r in kids_a if child_key(r) == key]
            group_b = [r for r in kids_b if child_key(r) == key]
            if unpaired:
                undecided(a, b, key, group_a, group_b, unpaired)
            elif no_number:
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


def entry_point_recorded(rows, entry=None):
    """Whether the log has the record of the entry point [entry], or of any
    entry point when [entry] is None: the message of a call without a
    parent, not inferred from the stacks of its callees. With [entry], it
    must be the only root."""
    roots = [r for r in rows if r["parent"] is None]
    if entry is None:
        return any(not r.get("inferred") for r in roots)
    return len(roots) == 1 and roots[0]["function"] == entry and \
        not roots[0].get("inferred")


def entry_point_problems(rows, entry):
    """Why the records of a run are not one tree of the entry point
    configured for its target: the run must have one root, the call of
    [entry], and every callstack must end in [entry]."""
    problems = []
    roots = [r for r in rows if r["parent"] is None]
    if len(roots) != 1:
        problems.append("%d roots instead of the entry point %s alone"
                        % (len(roots), entry))
    for root in roots:
        if root["function"] != entry:
            problems.append("root %s is not the entry point %s"
                            % (root["function"], entry))
    others = sorted({r["entry_point"] for r in rows
                     if r["entry_point"] != entry})
    if others:
        problems.append("callstacks end in %s, not in the entry point %s"
                        % (", ".join(others), entry))
    return problems


def summarize_alignment(rows_a, rows_b, result, problems_a=(),
                        problems_b=(), numbering="not established",
                        outcomes=(None, None), entry_point=None):
    """Counts of an alignment and its verdict.

    The records of each run are counted apart from the calls inferred from
    the callstacks of an interrupted log. [numbering] is the evidence that
    both runs number the statements of their programs alike (see
    [numbering_state]); [outcomes] are the outcomes of the two runs, None
    when not given. The alignment is complete when every record of both
    runs is aligned, no call is inferred or interrupted, no structural
    problem was found in either log, both logs have the record of the entry
    point and give the statement numbers, the digests of the two ASTs are
    equal, and both runs completed; [verdict] says why it is not. When the
    only reason is a numbering asserted without digest, the verdict says so
    instead of complete."""
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
    summary["entry_point"] = entry_point or "-"
    summary["entry_point_a"] = entry_point_recorded(rows_a, entry_point)
    summary["entry_point_b"] = entry_point_recorded(rows_b, entry_point)
    summary["outcome_a"] = outcomes[0] or "-"
    summary["outcome_b"] = outcomes[1] or "-"
    accounted_a = (len(pairs) + summary["nested_under_hit_b"]
                   + summary["unmatched_a"] + undecided_a)
    accounted_b = (len(pairs) + summary["nested_under_hit_a"]
                   + summary["unmatched_b"] + undecided_b)
    summary["accounted"] = (accounted_a == len(rows_a)
                            and accounted_b == len(rows_b))
    reasons = []
    if entry_point is None:
        reasons.append("entry point not given")
    for side, outcome in zip("AB", outcomes):
        if outcome is None:
            reasons.append("outcome of %s not given" % side)
        elif outcome != "completed":
            reasons.append("outcome of %s: %s" % (side, outcome))
    for side in "ab":
        if not summary["entry_point_" + side]:
            reasons.append("no record of the entry point in "
                           + side.upper())
    if not summary["accounted"]:
        reasons.append("records not accounted for")
    if summary["interrupted_a"] or summary["interrupted_b"]:
        reasons.append("interrupted")
    if problems_a or problems_b:
        reasons.append("structural problems")
    if summary["statement_numbers_a"] != "all" or \
       summary["statement_numbers_b"] != "all":
        reasons.append("statement numbers missing")
    if numbering in NUMBERING_REASONS:
        reasons.append(NUMBERING_REASONS[numbering])
    elif numbering != "same" and numbering not in WEAK_NUMBERING:
        reasons.append("numbering not established")
    if not (len(observed) == summary["records_a"] == summary["records_b"]
            and len(pairs) == len(rows_a) == len(rows_b)):
        reasons.append("not every record aligned")
    weak = WEAK_NUMBERING.get(numbering)
    if weak:
        reasons.append(weak[0])
    summary["complete"] = not reasons
    if not reasons:
        summary["verdict"] = "complete"
    elif weak and reasons == [weak[0]]:
        summary["verdict"] = weak[1]
    else:
        summary["verdict"] = "incomplete: " + ", ".join(reasons)
    return summary


def write_tsv(path, header, rows):
    with open_text(path, "w") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def write_alignment(prefix, path_a, path_b, numbering, outcomes,
                    entry_point=None, entry_point_b=None):
    """Aligns the records files of two runs and writes the summary and the
    lists of an alignment under [prefix]. [entry_point] is the entry point
    configured for the target; [entry_point_b], when given, that of run B,
    which must be the same. Returns the summary."""
    rows_a, problems_a = load_records_and_problems(path_a)
    rows_b, problems_b = load_records_and_problems(path_b)
    if entry_point is not None:
        problems_a += entry_point_problems(rows_a, entry_point)
        problems_b += entry_point_problems(rows_b, entry_point)
        if entry_point_b not in (None, entry_point):
            problems_b.append("the entry point of B is %s, not %s"
                              % (entry_point_b, entry_point))
    result = align(rows_a, rows_b, numbering)
    summary = summarize_alignment(rows_a, rows_b, result, problems_a,
                                  problems_b, numbering, outcomes,
                                  entry_point)
    if prefix:
        with open_text(prefix + "summary.tsv", "w") as f:
            for key, value in summary.items():
                f.write("%s\t%s\n" % (key, value))
        write_tsv(prefix + "differences.tsv",
                  ["id_a", "id_b", "dispositions_a", "dispositions_b"],
                  [(a["id"], b["id"], json.dumps(a["dispositions"]),
                    json.dumps(b["dispositions"]))
                   for a, b in result["pairs"]
                   if a["dispositions"] != b["dispositions"]])
        write_tsv(prefix + "under-hit.tsv",
                  ["side", "id", "hit_in"], result["under_hit"])
        write_tsv(prefix + "unmatched.tsv",
                  ["side", "id", "reason"], result["unmatched"])
        write_tsv(prefix + "undecided.tsv",
                  ["parent_a", "parent_b", "call", "calls_a", "calls_b",
                   "records_a", "records_b", "reason"], result["undecided"])
        write_tsv(prefix + "problems.tsv", ["side", "problem"],
                  [("A", p) for p in problems_a]
                  + [("B", p) for p in problems_b])
    return summary


def align_command(args):
    numbering = numbering_state(args.ast_a, args.ast_b,
                                args.assert_numbering, args.pp_a, args.pp_b)
    summary = write_alignment(args.output, args.a, args.b, numbering,
                              (args.outcome_a, args.outcome_b),
                              args.entry_point)
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


QUERY_FIELDS = {"format": 2, "reach": 3, "answer": 9, "unavailable": 7,
                "error": 7}


def load_queries(path):
    """Reads the answers of a run. Returns a dictionary: the reached
    statements, the answers, the queries without an answer by reason
    (unavailable or error), whether the file declares its reached exit
    points (format 2), whether the file is complete and why not.

    A file is complete when every line is well formed, ends with a newline,
    and the last line, and only it, is a done line whose count is the number
    of answer, unavailable and error lines. Any other file is incomplete,
    with the first reason found; it never raises an exception."""
    reach, answers, unavailable = set(), {}, {}
    done, rows, problem, version = None, 0, None, 1
    with open_text(path) as f:
        text = f.read()
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    elif text:
        problem = "the last line is cut"
    for number, line in enumerate(lines, 1):
        fields = line.split("\t")
        kind = fields[0]
        if done is not None:
            problem = problem or "a line after the done line"
            break
        if kind == "done":
            if len(fields) == 2 and decimal(fields[1]) is not None:
                done = decimal(fields[1])
            else:
                problem = problem or "malformed done line"
                break
            continue
        if QUERY_FIELDS.get(kind) != len(fields):
            problem = problem or "malformed line %d" % number
            continue
        if kind == "format":
            if decimal(fields[1]) is not None:
                version = decimal(fields[1])
            else:
                problem = problem or "malformed line %d" % number
        elif kind == "reach":
            reach.add((fields[1], fields[2]))
        elif kind == "answer":
            if not (fields[6] in ("0", "1") and fields[7] in ("0", "1")):
                problem = problem or "malformed line %d" % number
                continue
            rows += 1
            answers[tuple(fields[1:6])] = \
                (int(fields[6]), int(fields[7]), fields[8])
        elif kind == "unavailable":
            rows += 1
            unavailable[tuple(fields[1:6])] = fields[6]
        else:
            rows += 1
            unavailable[tuple(fields[1:6])] = "error"
    if problem:
        status = "incomplete: " + problem
    elif done is None:
        status = "incomplete: no done line"
    elif done != rows:
        status = "incomplete: done %d, %d lines" % (done, rows)
    else:
        status = "complete"
    return {"reach": reach, "answers": answers, "unavailable": unavailable,
            "exits_declared": version >= 2, "status": status}


UNAVAILABLE_REASONS = ("unreached", "no-callstack", "no-results",
                       "top-state", "disabled-domain", "error", "missing")


def missing_reason(q, key):
    """Why the answers [q] of a run have no answer to the query [key]:
    - the reason written for it (unavailable or error);
    - for a query in one callstack, the reason no-results or
      disabled-domain written for the same query over all callstacks: the
      state of the function was not saved, so no callstack is enumerated;
    - unreached, when its statement, or for an exit query the exit point of
      its function, is not reached;
    - for an exit query of a file written before the exit points were
      declared (without format 2), which wrote the exit queries of a
      function only when its results were saved and its exit reached:
      no-callstack when the same query over all callstacks is in the file,
      missing otherwise, the file saying nothing of that exit;
    - no-callstack, when the statement is reached but not in that
      callstack;
    - missing otherwise."""
    if key in q["unavailable"]:
        return q["unavailable"][key]
    if key[3] != "*":
        over_all = q["unavailable"].get(key[:3] + ("*",) + key[4:])
        if over_all in ("no-results", "disabled-domain"):
            return over_all
    if key[2] == "exit" and not q["exits_declared"]:
        over_all = key[:3] + ("*",) + key[4:]
        if key[3] != "*" and (over_all in q["answers"]
                              or over_all in q["unavailable"]):
            return "no-callstack"
        return "missing"
    if (key[0], key[1]) not in q["reach"]:
        return "unreached"
    if key[3] != "*":
        return "no-callstack"
    return "missing"


def numbered_query(key):
    """Whether the key (function, statement, point, callstack, lvalue) of a
    query depends on the numbering of the program: it names a statement
    (FUNCTION:LINE:K, the K-th statement of a line) or a callstack below the
    entry point (with a call site CALLEE@CALLER:LINE:K). The exit of a
    function over all callstacks, or in the entry point, does not."""
    return not key[1].endswith(":exit") or "|" in key[3]


def numbering_reasons(numbering):
    """The reasons that a numbering gives against a complete comparison,
    and whether it pairs the statements of two runs (same, or one of
    WEAK_NUMBERING)."""
    if numbering == "same":
        return [], True
    if numbering in WEAK_NUMBERING:
        return [WEAK_NUMBERING[numbering][0]], True
    return [NUMBERING_REASONS.get(numbering, "numbering not established")], \
        False


def compare_queries(path_a, path_b, numbering="not established"):
    """Compares the answers of run B with those of run A, query by query.

    Each query asked in either run is counted once: answered in both runs
    (equal, wider, narrower, incomparable or undecided), without an answer
    on a side, with the reason, or unpaired. A query whose key depends on
    the numbering (numbered_query) is unpaired unless [numbering] pairs the
    statements of the two runs (numbering_reasons): its key may name
    different statements in the two runs. Top answers are counted on each
    side over all the answers of that side. The comparison is complete when
    both files are complete and the numbering is same. Returns the summary,
    the queries that are not equal, the unpaired queries and the statements
    reached in one run only."""
    qa, qb = load_queries(path_a), load_queries(path_b)
    against, paired = numbering_reasons(numbering)
    ans_a, ans_b = qa["answers"], qb["answers"]
    keys = (set(ans_a) | set(ans_b) | set(qa["unavailable"])
            | set(qb["unavailable"]))
    counts = Counter()
    details, unpaired = [], []
    for side, q in (("a", qa), ("b", qb)):
        for answer in q["answers"].values():
            if is_top_answer(answer[2]):
                counts["top_" + side] += 1
            if is_garbled_answer(answer[2]):
                counts["garbled_" + side] += 1
    for key in sorted(keys):
        a, b = ans_a.get(key), ans_b.get(key)
        if not paired and numbered_query(key):
            unpaired.append(key + (against[0], a[2] if a else "",
                                   b[2] if b else ""))
            continue
        if a is not None and b is not None:
            verdict = classify(a, b)
            counts[verdict] += 1
            if verdict != "equal":
                details.append(key + (verdict, a[2], b[2]))
            continue
        for side, answer, q in (("a", a, qa), ("b", b, qb)):
            if answer is None:
                reason = missing_reason(q, key)
                if reason not in UNAVAILABLE_REASONS:
                    reason = "other"
                counts["unavailable_%s_%s" % (side, reason)] += 1
                details.append(key + ("unavailable in " + side.upper()
                                      + " (" + reason + ")",
                                      a[2] if a else "", b[2] if b else ""))
    summary = OrderedDict()
    summary["queries"] = len(keys)
    summary["numbering"] = numbering
    summary["unpaired"] = len(unpaired)
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
    # The statements reached in one run only, compared by their keys: only
    # when the numbering pairs the statements.
    reach = []
    if paired:
        reach = sorted([s + ("A",) for s in qa["reach"] - qb["reach"]]
                       + [s + ("B",) for s in qb["reach"] - qa["reach"]])
    summary["reached_a_only"] = (len(qa["reach"] - qb["reach"]) if paired
                                 else "-")
    summary["reached_b_only"] = (len(qb["reach"] - qa["reach"]) if paired
                                 else "-")
    summary["complete_a"] = qa["status"]
    summary["complete_b"] = qb["status"]
    reasons = ["answer file of %s incomplete" % side
               for side, q in (("A", qa), ("B", qb))
               if q["status"] != "complete"] + against
    summary["comparison"] = ("incomplete: " + ", ".join(reasons) if reasons
                             else "complete")
    return summary, details, unpaired, reach


def write_queries(prefix, summary, details, unpaired, reach):
    with open_text(prefix + "summary.tsv", "w") as f:
        for key, value in summary.items():
            f.write("%s\t%s\n" % (key, value))
    write_tsv(prefix + "differences.tsv",
              ["function", "stmt", "point", "callstack", "lvalue",
               "verdict", "answer_a", "answer_b"], details)
    write_tsv(prefix + "unpaired.tsv",
              ["function", "stmt", "point", "callstack", "lvalue",
               "reason", "answer_a", "answer_b"], unpaired)
    write_tsv(prefix + "reached-in-one-run.tsv",
              ["function", "stmt", "reached_only_in"], reach)


def queries_command(args):
    numbering = numbering_state(args.ast_a, args.ast_b,
                                args.assert_numbering, args.pp_a, args.pp_b)
    summary, details, unpaired, reach = compare_queries(args.a, args.b,
                                                        numbering)
    if args.output:
        write_queries(args.output, summary, details, unpaired, reach)
    for key, value in summary.items():
        print("%s\t%s" % (key, value))
    return 0


# ----- Alarms ------------------------------------------------------------

def normalize_directory(directory, roots=()):
    """The directory of an alarm with the root of the run removed: the
    source snapshot of each run is a fresh directory, so a path under one of
    [roots] is written relative to it, from ${SRC}. A root is a path, or a
    compiled pattern that matches the root at the start of the
    directory."""
    for root in roots:
        if hasattr(root, "match"):
            match = root.match(directory)
            if match:
                return "${SRC}" + directory[match.end():]
            continue
        root = root.rstrip("/")
        if root and (directory == root or directory.startswith(root + "/")):
            return "${SRC}" + directory[len(root):]
    return directory


ALARMS_COLUMNS = ("directory", "file", "line", "function", "property kind",
                  "status", "property")


def load_alarms(path, roots=()):
    """The alarms and properties of an alarms.csv file written by
    -report-csv, as a multiset: (directory, file, line, function, kind,
    property) -> Counter of statuses. The directory is normalised by
    [normalize_directory]. Returns the multiset and the number of keys that
    occur more than once."""
    result = defaultdict(Counter)
    for row in read_header_tsv(path, ALARMS_COLUMNS):
        key = (normalize_directory(row["directory"], roots),
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


# ----- Counters of the statistics file ---------------------------------------

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


# The counters of the statistics file (-eva-statistics-file) that the tables
# read, in families:
#   builtin:   builtin-applied-NAME
#   memexec:   memexec-hits, -misses, -stored, -refused-REASON
#   supplied:  cache-hits, cache-rejected-REASON, cache-refused-REASON, the
#              entries supplied by a test module
#   collector: collector-would-store, collector-refused-REASON
#   producer:  cache-produced, cache-production-refused-REASON
# The analyzer creates the row of a counter when it increments it and
# writes no row for a counter it never incremented. A counter is therefore a
# number only when the file holds a row of it; without a row it is absent,
# written -, never 0. Nothing else gives it a value: not the options of
# the run, not its log, not another row of its family (README.md, Counters
# and dispositions).
FAMILIES = ("builtin", "memexec", "supplied", "collector", "producer")
MEMEXEC_REFUSALS = ("not-cacheable", "no-inout", "footprint-top",
                    "relate-top", "relate-unclosed", "exception")
COUNTER_NAMES = {
    "memexec": {"memexec-hits", "memexec-misses", "memexec-stored",
                *("memexec-refused-" + reason for reason in MEMEXEC_REFUSALS)},
    "supplied": {"cache-hits"},
    "collector": {"collector-would-store"},
    "producer": {"cache-produced"},
}
COUNTER_REASONS = {
    "builtin": ("builtin-applied-",),
    "memexec": (),
    "supplied": ("cache-rejected-", "cache-refused-"),
    "collector": ("collector-refused-",),
    "producer": ("cache-production-refused-",),
}
# The counters summed over their reasons: the prefix of their rows.
REASON_PREFIXES = ("memexec-refused-", "cache-rejected-", "cache-refused-",
                   "collector-refused-", "cache-production-refused-")
# A counter name of each family, looked for in the compiled Eva plugin and
# recorded with the binary. It decides no cell of the tables.
FAMILY_MARKERS = {"builtin": b"builtin-applied-", "memexec": b"memexec-hits",
                  "supplied": b"cache-rejected-",
                  "collector": b"collector-would-store",
                  "producer": b"cache-production-refused-"}
# The last row of an export. The analyzer writes the file when an analysis
# ends, one row per statistic that was set, sorted by name, and it sets
# stmt-coverage before every export: a file that ends with this row was
# written whole.
EXPORT_LAST_ROW = "stmt-coverage"


def counter_family(name):
    """The family of a counter that the tables read, or None for another
    row of the statistics file."""
    for family, prefixes in COUNTER_REASONS.items():
        if name in COUNTER_NAMES.get(family, ()) or any(
                name.startswith(p) and len(name) > len(p) for p in prefixes):
            return family
    return None


def read_statistics(path):
    """The counters of a statistics file. Returns (rows, count, None): the
    rows of the counters that the tables read, as (name, function, value),
    and the number of rows of the file; or ([], None, reason) when the file
    is not a complete export, and then none of its rows is read.

    A complete export has four fields separated by tabulations on every
    line (name, function, location, value), each line ended by a newline,
    the names in ascending order, and stmt-coverage as its last row. Every
    row of a counter of the tables must have a function and a bounded
    decimal value."""
    if not path or not os.path.exists(path):
        return [], None, "no statistics file"
    with open_text(path) as f:
        text = f.read()
    if not text:
        return [], None, "the statistics file is empty"
    if not text.endswith("\n"):
        return [], None, "the last line of the statistics file is cut"
    rows, names = [], []
    for number, line in enumerate(text[:-1].split("\n"), 1):
        fields = line.split("\t")
        if len(fields) != 4 or not fields[0]:
            return [], None, ("line %d of the statistics file does not "
                              "have four fields" % number)
        names.append(fields[0])
        if counter_family(fields[0]) is not None:
            value = decimal(fields[3])
            if value is None or not fields[1]:
                return [], None, ("line %d of the statistics file is not "
                                  "the count of a function" % number)
            rows.append((fields[0], fields[1], value))
    if names != sorted(names):
        return [], None, ("the rows of the statistics file are not sorted "
                          "by name")
    if names[-1] != EXPORT_LAST_ROW:
        return [], None, ("the statistics file does not end with the row "
                          + EXPORT_LAST_ROW)
    return rows, len(names), None


def family_of_binary(cmxs_path):
    """The counter families whose names a compiled Eva plugin holds."""
    with open(cmxs_path, "rb") as f:
        data = f.read()
    return [k for k in FAMILIES if FAMILY_MARKERS[k] in data]


def statistics_counts(rows, export_rows):
    """The cells that the rows of a complete export give (read_statistics):
    builtin applications, cache activity, collector verdicts, produced and
    supplied entries. A counter is the sum of its rows, and None when the
    export has no row of it; a list by reason is None when no reason has a
    row. [export_rows] is the number of rows of the export, None when the
    file is not one: every cell is then None."""
    builtins, values, by_reason = {}, {}, {}
    builtin_rows = 0
    for name, _, value in rows:
        if name.startswith("builtin-applied-"):
            canonical = CANONICAL_BUILTINS.get(name[len("builtin-applied-"):])
            if canonical:
                builtins[canonical] = builtins.get(canonical, 0) + value
                builtin_rows += 1
            continue
        for prefix in REASON_PREFIXES:
            if name.startswith(prefix):
                reasons = by_reason.setdefault(prefix[:-1], {})
                reason = name[len(prefix):]
                reasons[reason] = reasons.get(reason, 0) + value
                name = prefix[:-1]
        values[name] = values.get(name, 0) + value

    def reasons(key):
        if key not in by_reason:
            return None
        return ",".join("%s=%d" % kv for kv in sorted(by_reason[key].items()))

    counts = OrderedDict()
    counts["export_rows"] = export_rows
    for k in ALLOCATION + RELEASE:
        counts[k] = builtins.get(k)
    # The rows of the allocation and release builtins: their number, which
    # is a fact of the file, and their sum. Without a row there is no sum,
    # and no membership in set A either way.
    counts["allocation_and_release_rows"] = \
        None if export_rows is None else builtin_rows
    total = sum(builtins.values()) if builtin_rows else None
    counts["allocation_and_release"] = total
    counts["in_set_a"] = None if total is None else total == 0
    counts["hits"] = values.get("memexec-hits")
    counts["misses"] = values.get("memexec-misses")
    counts["stored"] = values.get("memexec-stored")
    counts["refused"] = values.get("memexec-refused")
    counts["refused_by_reason"] = reasons("memexec-refused")
    counts["supplied_hits"] = values.get("cache-hits")
    counts["supplied_rejected"] = values.get("cache-rejected")
    counts["supplied_rejected_by_reason"] = reasons("cache-rejected")
    counts["supplied_refused"] = values.get("cache-refused")
    counts["supplied_refused_by_reason"] = reasons("cache-refused")
    counts["collector_would_store"] = values.get("collector-would-store")
    counts["collector_refused"] = values.get("collector-refused")
    counts["collector_refused_by_reason"] = reasons("collector-refused")
    counts["producer_stored"] = values.get("cache-produced")
    counts["producer_refused"] = values.get("cache-production-refused")
    counts["producer_refused_by_reason"] = \
        reasons("cache-production-refused")
    return counts


def run_counts(stats_path):
    """The cells of a statistics file (statistics_counts): every one is
    None when the file is not a complete export."""
    rows, export_rows, _ = read_statistics(stats_path)
    return statistics_counts(rows, export_rows)


def function_counts(rows):
    """The memexec and collector counters of each function in the rows of
    a complete export (read_statistics): rows [function, hits, misses,
    stored, refused, collector_would_store, collector_refused], sorted by
    function, None where the function has no row of the counter."""
    table = defaultdict(dict)
    for name, function, value in rows:
        if counter_family(name) not in ("memexec", "collector"):
            continue
        for prefix in ("memexec-refused-", "collector-refused-"):
            if name.startswith(prefix):
                name = prefix[:-1]
        table[function][name] = table[function].get(name, 0) + value
    return [[function] + [c.get(k) for k in (
        "memexec-hits", "memexec-misses", "memexec-stored", "memexec-refused",
        "collector-would-store", "collector-refused")]
            for function, c in sorted(table.items())]


# ----- Dispositions counted in the Eva log -----------------------------------

# What a log shows is reported as what the log shows: counts of its
# disposition lines by the words of their fields, next to the number of
# analysis starts of that log. A count of 0 means that there is no such line
# among the disposition lines of the log. These counts are never turned
# into counters of the statistics file, and no counter into a count.
ANALYSIS_START = re.compile(
    r"\[eva\] Analyzing (?:a complete|an incomplete) application starting at .+"
)
LOG_REJECTED = r"rejected \(entry [0-9]{1,18}: ([^(),;]+)\)"
LOG_HIT = r"hit \(entry [0-9]{1,18}\)"
LOG_LOOKUP = re.compile(
    r"no-candidate|%s|%s(?:, %s)*(?:, %s)?"
    % (LOG_HIT, LOG_REJECTED, LOG_REJECTED, LOG_HIT))
LOG_EXECUTIONS = ("analysed", "not-analysed", "interrupted")
LOG_STORAGE = re.compile(
    r"none|stored \(entry [0-9]{1,18}\)|refused \(([^(),;]+)\)")
LOG_COLLECTOR = re.compile(r"would-store|refused \(([^(),;]+)\)")
LOG_PRODUCER = re.compile(
    r"stored \(entry [0-9]{1,18}\)|refused \(([^(),;]+)\)")
LOG_FIELDS = (["lookup", "execution", "storage"],
              ["lookup", "execution", "storage", "collector"],
              ["lookup", "execution", "storage", "collector", "producer"])
LOG_COLUMNS = [
    "analysis_starts", "disposition_lines", "lookup_hit",
    "lookup_no_candidate", "lookup_rejected", "lookup_rejected_by_reason",
    "storage_stored", "storage_none", "storage_refused",
    "storage_refused_by_reason", "collector_would_store",
    "collector_refused", "collector_refused_by_reason", "producer_stored",
    "producer_refused", "producer_refused_by_reason", "log_note", "sources"]


def disposition_kinds(dispositions):
    """The kinds that one disposition line shows, each in the words of the
    message: "lookup: hit", "lookup: no-candidate", "lookup: rejected
    (REASON)" once per rejected candidate, "storage: stored", "storage:
    none", "storage: refused (REASON)", "collector: would-store",
    "collector: refused (REASON)", "producer: stored" and "producer:
    refused (REASON)". None when the line has another field or a field of
    another form than the pinned analyzer prints: a line that the tool does
    not understand shows nothing."""
    if list(dispositions) not in LOG_FIELDS:
        return None
    lookup = dispositions["lookup"]
    storage = LOG_STORAGE.fullmatch(dispositions["storage"])
    if not LOG_LOOKUP.fullmatch(lookup) or not storage or \
       dispositions["execution"] not in LOG_EXECUTIONS:
        return None
    kinds = ["lookup: rejected (%s)" % reason
             for reason in re.findall(LOG_REJECTED, lookup)]
    if re.search(LOG_HIT, lookup):
        kinds.append("lookup: hit")
    elif lookup == "no-candidate":
        kinds.append("lookup: no-candidate")
    kinds.append("storage: " + re.sub(r" \(entry [0-9]+\)", "",
                                      storage.group(0)))
    for field, pattern in (("collector", LOG_COLLECTOR),
                           ("producer", LOG_PRODUCER)):
        if field in dispositions:
            match = pattern.fullmatch(dispositions[field])
            if not match:
                return None
            kinds.append("%s: %s" % (field, re.sub(r" \(entry [0-9]+\)", "",
                                                   match.group(0))))
    return kinds


def log_counts(log_path):
    """What an Eva log shows of the dispositions of its calls. Returns the
    cells of LOG_COLUMNS but sources, and the counter of the kinds
    (disposition_kinds), or None when the kinds are not counted.

    analysis_starts is the number of lines that announce an analysis, and
    disposition_lines the number of messages of the categories cache and
    cache-producer that are call dispositions of a known form. The kinds
    are counted only when the log has exactly one analysis start, at least
    one disposition line and no cache message of another form; otherwise
    their cells are None and log_note says why. A count of 0 then means
    that no disposition line of this log shows the kind. The cells of the
    collector and of the producer are None when no disposition line has
    that field: a field that the log does not print shows no count."""
    counts = OrderedDict((k, None) for k in LOG_COLUMNS[:-1])
    if not log_path:
        counts["log_note"] = "no log"
        return counts, None
    with open_text(log_path) as f:
        lines = f.read().split("\n")
    starts = sum(ANALYSIS_START.fullmatch(line.rstrip("\r")) is not None
                 for line in lines)
    kinds, known, unknown = Counter(), 0, 0
    for plugin, category, text in messages(lines):
        if plugin != "eva" or category not in ("cache", "cache-producer"):
            continue
        # The fields come before the callstack: a message cut inside its
        # stack still shows them.
        record = parse_cache_message(text.partition("\nstack:")[0])
        found = disposition_kinds(record["dispositions"]) if record else None
        if found is None:
            unknown += 1
        else:
            known += 1
            kinds.update(found)
    counts["analysis_starts"] = starts
    counts["disposition_lines"] = known
    if unknown:
        counts["log_note"] = ("%d cache message(s) of another form than a "
                              "disposition line" % unknown)
    elif starts != 1:
        counts["log_note"] = "%d analysis starts" % starts
    elif not known:
        counts["log_note"] = "no disposition line"
    if counts["log_note"]:
        return counts, None

    def by_reason(prefix):
        found = sorted((k[len(prefix):-1], n) for k, n in kinds.items()
                       if k.startswith(prefix))
        return (sum(n for _, n in found),
                ",".join("%s=%d" % kv for kv in found) or "none")

    counts["lookup_hit"] = kinds["lookup: hit"]
    counts["lookup_no_candidate"] = kinds["lookup: no-candidate"]
    counts["lookup_rejected"], counts["lookup_rejected_by_reason"] = \
        by_reason("lookup: rejected (")
    counts["storage_stored"] = kinds["storage: stored"]
    counts["storage_none"] = kinds["storage: none"]
    counts["storage_refused"], counts["storage_refused_by_reason"] = \
        by_reason("storage: refused (")
    if printed(kinds, "collector"):
        counts["collector_would_store"] = kinds["collector: would-store"]
        counts["collector_refused"], \
            counts["collector_refused_by_reason"] = \
            by_reason("collector: refused (")
    if printed(kinds, "producer"):
        counts["producer_stored"] = kinds["producer: stored"]
        counts["producer_refused"], counts["producer_refused_by_reason"] = \
            by_reason("producer: refused (")
    return counts, kinds


def printed(kinds, field):
    """Whether a disposition line counted in [kinds] has the field
    [field]."""
    return any(k.startswith(field + ": ") for k in kinds)


# The kinds of a disposition line that have a counter at the seam of the
# pinned analyzer, which increments it before it prints the line: the
# counter of each kind. memexec-misses is incremented at the lookup and has
# no kind of its own; "lookup: no-candidate", "storage: none" and "storage:
# refused (disabled)" have no counter.
def counter_kind(name):
    """The kind of disposition line that a counter of the statistics file
    counts, or None."""
    if name in ("memexec-hits", "cache-hits"):
        return "lookup: hit"
    if name == "memexec-stored":
        return "storage: stored"
    if name == "collector-would-store":
        return "collector: would-store"
    if name == "cache-produced":
        return "producer: stored"
    for prefix, kind in (("memexec-refused-", "storage: refused (%s)"),
                         ("cache-refused-", "storage: refused (%s)"),
                         ("collector-refused-", "collector: refused (%s)"),
                         ("cache-rejected-", "lookup: rejected (%s)"),
                         ("cache-production-refused-",
                          "producer: refused (%s)")):
        if name.startswith(prefix) and len(name) > len(prefix):
            return kind % name[len(prefix):]
    return None


UNCOUNTED_KINDS = ("lookup: no-candidate", "storage: none",
                   "storage: refused (disabled)")


def compare_sources(kinds, rows, problem):
    """Whether the kinds counted in a log (log_counts) and the rows of the
    statistics file of the same run (read_statistics) give the same
    numbers, kind by kind. It reports and fills no cell: None when either
    source is not usable; "disagree: ..." with each kind whose two numbers
    differ, or that the log shows and no row counts; otherwise the number
    of kinds that have the same number in both, or "no kind in both".

    A kind without a line is compared as the log count 0 with the rows of
    its counter. The kinds of the collector and of the producer are
    compared only when a disposition line of the log has that field: the
    analyzer prints the producer field under a category of its own."""
    if kinds is None or problem:
        return None
    counted = {}
    for name, _, value in rows:
        kind = counter_kind(name)
        if kind:
            counted[kind] = counted.get(kind, 0) + value
    absent = tuple(field + ": " for field in ("collector", "producer")
                   if not printed(kinds, field))
    equal, differing = 0, []
    for kind in sorted(set(kinds) | set(counted)):
        if kind in UNCOUNTED_KINDS or kind.startswith(absent):
            continue
        seen, row = kinds.get(kind, 0), counted.get(kind)
        if row == seen:
            equal += 1
        elif row is not None or seen:
            differing.append('"%s" log %d, statistics %s'
                             % (kind, seen, "-" if row is None else row))
    if differing:
        return "disagree: " + "; ".join(differing)
    if not equal:
        return "no kind in both"
    return "agree on %d kind%s" % (equal, "" if equal == 1 else "s")


TIMED_MODES = ("nocache", "cache", "reference")


def time_rows(runs):
    """Elapsed times of the first run of each mode of each case, and the
    ratios cache/nocache and cache/reference when both runs completed and
    have a time. A run that did not complete gives its outcome instead of
    a time. The other cells say what the directory lacks: "no run" when it
    has no run of the mode, "no outcome" when the run records none, "no
    time" when a completed run records none, as the runs of the fixtures,
    which run without the watchdog."""
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
                cells.append("no run")
            elif r.get("outcome") in (None, "", "-"):
                cells.append("no outcome")
            elif r["outcome"] != "completed":
                cells.append(r["outcome"])
            elif not measured(r):
                cells.append("no time")
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
    """Prints the cells of a statistics file and, with --log, what the log
    of the same invocation shows, each count of the log under a name that
    starts with log_."""
    rows, export_rows, problem = read_statistics(args.stats)
    if problem:
        print("%s: %s; its counters are not read" % (args.stats, problem),
              file=sys.stderr)
    for key, value in statistics_counts(rows, export_rows).items():
        print("%s\t%s" % (key, cell(value)))
    if args.log:
        logged, kinds = log_counts(args.log)
        logged["sources"] = compare_sources(kinds, rows, problem)
        for key, value in logged.items():
            if key != "sources" and not key.startswith("log_"):
                key = "log_" + key
            print("%s\t%s" % (key, cell(value)))
    return 0


def families_command(args):
    print(",".join(family_of_binary(args.cmxs)))
    return 0


# ----- Provenance of a binary ------------------------------------------------

def home_spellings():
    """The spellings of the home directory: the value of HOME without its
    trailing slashes, and its physical path, the longest first. None when
    HOME is not set or is the root."""
    home = os.environ.get("HOME", "")
    spellings = {s.rstrip("/") for s in (home, os.path.realpath(home))
                 if home}
    return sorted((s for s in spellings if s), key=len, reverse=True)


def home_pattern():
    """A pattern of the bytes of a path under the home directory, in any of
    its spellings: the spelling followed by a separator, by a character
    that cannot continue a file name, or by the end. The separator is not
    part of the match, so that the replacement keeps it. None without a
    home directory."""
    spellings = home_spellings()
    if not spellings:
        return None
    return re.compile(b"(?:" + b"|".join(re.escape(s.encode())
                                         for s in spellings)
                      + b")(?![A-Za-z0-9._+-])")


def holds_home(data):
    """Whether the bytes [data] hold the home directory, in any of its
    spellings."""
    pattern = home_pattern()
    return bool(pattern) and pattern.search(data) is not None


def redact_home(data):
    """The bytes [data] with every spelling of the home directory written
    ~, the separator after it kept."""
    pattern = home_pattern()
    return pattern.sub(b"~", data) if pattern else data


def read_maybe_gz(path):
    with open(path, "rb") as f:
        data = f.read()
    if path.endswith(".gz"):
        try:
            return gzip.decompress(data), True
        except (OSError, EOFError, zlib.error):
            pass
    return data, False


def check_symlinks(root, link_root):
    """Check all link targets without descending through directory links."""
    valid = True

    def inside(path):
        return os.path.commonpath((path, link_root)) == link_root

    def fail(error):
        raise error

    for directory, dirs, files in os.walk(root, onerror=fail):
        for name in dirs + files:
            path = os.path.join(directory, name)
            if not os.path.islink(path):
                continue
            target = os.readlink(path)
            if holds_home(os.fsencode(target)):
                problem = "holds the home directory"
            elif os.path.isabs(target) and (
                    not inside(os.path.normpath(target))
                    or not inside(os.path.realpath(target))):
                problem = "is an absolute path outside the output directory"
            else:
                continue
            print("Target of symbolic link %s %s." % (path, problem),
                  file=sys.stderr)
            valid = False
    return valid


def home_command(args):
    """check FILE...: exits with 1 when a file (decompressed when its name
    ends in .gz) holds the home directory, and names it. check-tree DIR:
    the same for every file and symbolic link under DIR. check-links DIR:
    checks just the symbolic links, including their absolute targets.
    redact: copies the standard input to
    the standard output with the home directory written ~. redact-tree DIR
    [--keep PATH]...: rewrites in place every text file under DIR, but the
    kept ones (relative to DIR), with the home directory written ~; a
    compressed file is compressed again without name or date."""
    if args.action == "redact":
        sys.stdout.buffer.write(redact_home(sys.stdin.buffer.read()))
        return 0
    if not home_spellings():
        print("HOME is not set.", file=sys.stderr)
        return 2
    paths = list(args.paths)
    if args.action in ("check-tree", "redact-tree", "check-links"):
        if len(paths) != 1:
            print("Supply one directory.", file=sys.stderr)
            return 2
        root = paths[0]
        link_root = args.link_root or os.path.realpath(root)
        if args.action in ("check-tree", "check-links"):
            if not check_symlinks(root, link_root):
                return 1
            if args.action == "check-links":
                return 0
        kept = {os.path.normpath(os.path.join(root, k)) for k in args.keep}
        paths = []
        for dirpath, _, filenames in os.walk(root):
            for name in sorted(filenames):
                path = os.path.join(dirpath, name)
                if not os.path.islink(path) and \
                   os.path.normpath(path) not in kept:
                    paths.append(path)
    found = []
    for path in paths:
        data, compressed = read_maybe_gz(path)
        if args.action == "redact-tree":
            if b"\0" in data[:8192] or not holds_home(data):
                continue
            data = redact_home(data)
            if compressed:
                data = gzip.compress(data, mtime=0)
            with open(path, "wb") as f:
                f.write(data)
        elif holds_home(data):
            found.append(path)
    for path in found:
        print("%s holds the home directory" % path, file=sys.stderr)
    return 1 if found else 0


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
            data = f.read()
        digest = hashlib.sha256(data).hexdigest()
        if holds_home(data):
            raise ValueError(
                "the patch %s holds the home directory %s: its SHA-256 is "
                "recorded on its bytes, which the public archive keeps; "
                "write the directory as ~ or as a variable"
                % (patch, " or ".join(home_spellings())))
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
SIGNAL = re.compile(r"^Command terminated by signal ([0-9]{1,3})$", re.M)


def read_measure(path):
    """The values written by watchdog.py for the measured invocation, or by
    GNU time in the runs of earlier revisions of this harness. GNU time
    writes status 0 and a line naming the signal when the command was killed
    by a signal: the status is then 128 plus the signal."""
    if not os.path.exists(path):
        return None
    with open_text(path) as f:
        return read_measure_text(f.read())


def read_measure_text(text):
    """The values of the text of a measure (see [read_measure])."""
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


def oom_findings(measure, log_text, dedicated_scope=False):
    """Return whether exhausted memory is established, and the evidence.
    A SIGKILL requires the kernel log to identify this particular victim.
    A rising cgroup counter describes its scope even when dedicated.
    """
    if measure.get("watchdog", "none") != "none":
        return False, ""
    status = decimal(measure.get("status"))
    if measure.get("signal") != "9":
        reported = bool(status and OUT_OF_MEMORY.search(log_text))
        return reported, "log" if reported else ""
    if status != 137:
        return False, ""

    identified = measure.get("kernel_log_oom") == "yes"
    parts = ["kernel log"] if identified else []
    events = measure.get("oom_kill_events", "")
    if (decimal(events) or 0) > 0:
        parts.append("cgroup oom_kill +%s, samples exclusive %s"
                     % (events, measure.get("cgroup_exclusive", "-")))
        if not dedicated_scope:
            parts.append("no dedicated scope")
        elif not identified:
            parts.append("scope oom event, victim not identified")
    return identified, ", ".join(parts)


def oom_evidence(measure, log_text, dedicated_scope=False):
    """The text of the evidence that memory was exhausted, empty when there
    is none (see [oom_findings])."""
    return oom_findings(measure, log_text, dedicated_scope)[1]


def classify_outcome(parse_exit, make_exit, measure, log_text,
                     entry_analysed, timeout_s=None, dedicated_scope=False):
    """The outcome of one run:
    - parse-error: the parsing step failed, Eva did not run;
    - harness-error: the Eva invocation was not measured, its measure has
      no valid status, make failed after a successful invocation, or what
      a completed run needs is not recorded: the exit status of the parse
      step or of make ([parse_exit] or [make_exit] is None), or the entry
      point of the target ([entry_analysed] is None);
    - timeout: the watchdog sent its signal at the wall-time limit; a run
      measured by an earlier revision of this harness, which did not record
      it, is never classified as a timeout;
    - oom: Frama-C or the OCaml runtime reports that memory is exhausted, or
      the out-of-memory killer of the system is reported to have killed it:
      by the kernel log (see [oom_findings]);
    - killed: killed by SIGKILL that the watchdog did not send, with no
      conclusive evidence of the out-of-memory killer: cause unknown;
    - error: any other nonzero exit status or signal, such as 1 (invalid
      user input), 3 (unimplemented feature), 4 (internal error), 125
      (unexpected exception), or 124 when the watchdog did not fire;
    - incomplete: exit status 0 but the analysis of the entry point did
      not end;
    - completed.
    [timeout_s] is not used: the outcome does not depend on the elapsed
    time."""
    if parse_exit is not None and parse_exit != 0:
        return "parse-error"
    if measure is None or decimal(measure.get("status")) is None:
        return "harness-error"
    watchdog = measure.get("watchdog", "none")
    if watchdog in ("term", "kill"):
        return "timeout"
    status = decimal(measure["status"])
    if watchdog != "none" or (measure.get("signal") == "9" and status != 137):
        return "harness-error"
    if oom_findings(measure, log_text, dedicated_scope)[0]:
        return "oom"
    if measure.get("signal") == "9":
        return "killed"
    if status != 0:
        return "error"
    if parse_exit is None or make_exit != 0 or entry_analysed is None:
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


def existing(path):
    """[path], or [path].gz when only the compressed file exists, or None."""
    for candidate in (path, path + ".gz"):
        if os.path.exists(candidate):
            return candidate
    return None


def run_outcome(run, parse_exit, make_exit, dedicated_scope=False,
                entry_point=None, status=None):
    """The outcome of a run and the evidence of exhausted memory, from its
    measure, its log and its records, compressed or not, the statement of
    the runner that the command ran in a scope of its own, and the entry
    point configured for its target. The entry point is analysed when the
    records are one tree, whose root is the analysed call of [entry_point]
    and whose callstacks all end in it; without [entry_point], that is not
    decided, and the run is not completed. [status], when given, is the
    exit status of an invocation that ran without the watchdog, as the
    fixtures do (invocation_outcome_command): it stands for the measure,
    which such a run does not have."""
    measure = read_measure(os.path.join(run, "measure"))
    if status is not None:
        measure = OrderedDict(status=str(status))
    log_text = ""
    log = existing(os.path.join(run, "eva.log"))
    if log:
        with open_text(log) as f:
            log_text = f.read()
    entry_analysed = None if entry_point is None else False
    records = existing(os.path.join(run, "records.jsonl"))
    if records and entry_point is not None:
        rows = load_records(records)
        entry_analysed = (
            entry_point_recorded(rows, entry_point)
            and not entry_point_problems(rows, entry_point)
            and all(r["execution"] == "analysed" for r in rows
                    if r["parent"] is None))
    outcome = classify_outcome(parse_exit, make_exit, measure, log_text,
                               entry_analysed, dedicated_scope=dedicated_scope)
    evidence = oom_evidence(measure, log_text, dedicated_scope) \
        if measure else ""
    return outcome, evidence or "-"


def outcome_command(args):
    print("%s\t%s" % run_outcome(args.run, args.parse_exit, args.make_exit,
                                 args.dedicated_scope, args.entry_point))
    return 0


def invocation_outcome_command(args):
    """The outcome of a run that is one invocation of the analyzer, which
    parses and analyses, without the watchdog and without make: a fixture.
    Its exit status is that of the whole run, so there is no other step
    whose status could be missing; a status of 0 alone does not make the
    run completed, its records must show the analysed entry point."""
    print("%s\t%s" % run_outcome(args.run, 0, 0, False, args.entry_point,
                                 args.exit_status))
    return 0


# ----- Identity of the AST --------------------------------------------------

def load_ast(path):
    """The SHA-256 of an AST listing written by the query module
    (CAMPAIGN_AST_OUT) and its number of statement lines, or (None, None)
    when the file is missing, incomplete or of another format. It must start
    with the line format AST_FORMAT, hold lines global or stmt of five
    fields, and end with done COUNT, COUNT being the number of these lines.
    The digest covers every line but the done line."""
    path = existing(path) if path else None
    if not path:
        return None, None
    with open_text(path) as f:
        text = f.read()
    lines = text.split("\n")
    if lines[-1] != "" or len(lines) < 3:
        return None, None
    lines.pop()
    done = lines.pop().split("\t")
    body = lines[1:]
    if lines[0] != "format\t" + AST_FORMAT or len(done) != 2 or \
       done[0] != "done" or decimal(done[1]) != len(body) or \
       any(l.split("\t", 1)[0] not in ("global", "stmt")
           or len(l.split("\t")) != 5 for l in body):
        return None, None
    data = "".join(l + "\n" for l in lines).encode("utf-8", "surrogateescape")
    return (hashlib.sha256(data).hexdigest(),
            sum(1 for l in body if l.startswith("stmt\t")))


def ast_command(args):
    digest, statements = load_ast(args.listing)
    print("ast_format\t%s\nast_sha256\t%s\nast_statements\t%s"
          % (AST_FORMAT if digest else "-", digest or "-",
             "-" if statements is None else statements))
    return 0


# ----- Preprocessing evidence ---------------------------------------------

# The messages of the parse step run with -kernel-msg-key pp: one command
# per file parsed with preprocessing, before the line that names the file.
PP_COMMAND = re.compile(r'^\s*preprocessing with "(.*)"\s*$')
PP_PARSED = re.compile(r"^\[kernel\] Parsing .* \((with|no) preprocessing\)$")
PP_OUTPUT = re.compile(r"\s-o\s+'([^']*)'(?:\s|$)")
# The random part of the name of a temporary file of Frama-C (six hex
# digits before .i or .dir), once its directory is written ${TMP}.
PP_TEMP_NAME = re.compile(
    rb"(\$\{TMP\}/[^/'\"\s]*?)[0-9a-f]{6}(\.i|\.dir)(?=[/'\"\s]|$)")


def path_pattern(roots):
    """A pattern of the spellings of directories (token, path) as written,
    and physical: the longest first, not followed by a character of a
    name."""
    spellings = {}
    for token, path in roots:
        for spelling in (path.rstrip("/"), os.path.realpath(path)):
            if spelling and spelling != "/":
                spellings.setdefault(spelling.encode(), token.encode())
    if not spellings:
        return None, spellings
    ordered = sorted(spellings, key=len, reverse=True)
    return re.compile(b"(" + b"|".join(re.escape(x) for x in ordered)
                      + rb")(?![A-Za-z0-9._+-])"), spellings


def normalize_paths(data, pattern, spellings):
    """[data] with each spelling of [pattern] written as its token, and the
    random part of the temporary names removed."""
    if pattern is not None:
        data = pattern.sub(lambda m: spellings[m.group(1)], data)
    return PP_TEMP_NAME.sub(rb"\1\2", data)


def preprocessing_evidence(log_path, tmp_dir, source_roots=(), shares=()):
    """The evidence of the preprocessing of a parse step run with
    -kernel-msg-key pp -keep-temp-files and TMPDIR=[tmp_dir]: the commands
    printed in its log, in their order, and the preprocessed files they
    wrote, which Frama-C keeps in [tmp_dir]. Paths are written ${TMP} for
    [tmp_dir], ${SRC} for [source_roots] (the directory of the sources of
    the run) and ${FRAMAC_SHARE} for [shares] (the share directory of the
    binary), and the random part of the temporary names is removed, in the
    commands and in the text alike. Returns the fields of run.tsv
    (pp_files, pp_command_sha256, pp_text_sha256, pp_problem) and the
    commands so written. Without one command per file parsed, every file
    parsed with preprocessing, and each preprocessed file in [tmp_dir], the
    digests are - and pp_problem says why."""
    fields = OrderedDict([("pp_files", "-"), ("pp_command_sha256", "-"),
                          ("pp_text_sha256", "-"), ("pp_problem", "-")])
    path = existing(log_path) if log_path else None
    if not path or not os.path.isdir(tmp_dir):
        fields["pp_problem"] = "no parse log or no temporary directory"
        return fields, []
    with open_text(path) as f:
        log = f.read().split("\n")
    commands = [m.group(1) for m in map(PP_COMMAND.match, log) if m]
    parsed = [m.group(1) for m in map(PP_PARSED.match, log) if m]
    pattern, spellings = path_pattern(
        [("${TMP}", tmp_dir)] + [("${SRC}", r) for r in source_roots]
        + [("${FRAMAC_SHARE}", r) for r in shares])
    tmp = os.path.realpath(tmp_dir)
    problem = None
    if "no" in parsed:
        problem = "a file parsed without preprocessing"
    elif not commands:
        problem = "no preprocessing command in the log"
    elif len(commands) != len(parsed):
        problem = ("%d preprocessing commands for %d files"
                   % (len(commands), len(parsed)))
    texts = []
    for command in [] if problem else commands:
        output = PP_OUTPUT.search(command)
        target = os.path.realpath(output.group(1)) if output else None
        if not target or os.path.dirname(target) != tmp or \
           not os.path.isfile(target):
            problem = "a preprocessed file is not kept in the directory"
            break
        with open(target, "rb") as f:
            texts.append(hashlib.sha256(
                normalize_paths(f.read(), pattern, spellings)).hexdigest())
    if problem:
        fields["pp_problem"] = problem
        return fields, []
    written = [normalize_paths(c.encode("utf-8", "surrogateescape"),
                               pattern, spellings) for c in commands]
    fields["pp_files"] = str(len(commands))
    fields["pp_command_sha256"] = hashlib.sha256(
        b"".join(c + b"\n" for c in written)).hexdigest()
    fields["pp_text_sha256"] = hashlib.sha256(
        "".join(t + "\n" for t in texts).encode()).hexdigest()
    return fields, [c.decode("utf-8", "surrogateescape") for c in written]


def preprocessing_command(args):
    fields, commands = preprocessing_evidence(
        args.log, args.tmp_dir, args.source_root or [], args.share or [])
    if args.commands:
        with open_text(args.commands, "w") as f:
            for command in commands:
                f.write(command + "\n")
    for key, value in fields.items():
        print("%s\t%s" % (key, value))
    return 0


def preprocessing_digest(run):
    """The digests of the preprocessing of a run, from its run.tsv, as one
    value PP_COMMAND_SHA256:PP_TEXT_SHA256, or None."""
    pair = (run.get("pp_command_sha256"), run.get("pp_text_sha256"))
    if all(SHA256.fullmatch(x or "") for x in pair):
        return "%s:%s" % pair
    return None


# The options that make a command run more than one stage, or read more
# options from a file: a parse command that has one does not record the
# preprocessing of its run by itself.
SEQUENCING = ("-then", "-then-last", "-then-on", "-then-replace",
              "-commands-file")
SHELL_WORD = re.compile(
    r"""(?:[-A-Za-z0-9_./,:=+%@~]+|\\[ -~]|'[^'\r\n]*'|"""
    r""""(?:[^"\\`$\r\n]|\\["\\])*")+(?=[ \t]|$)"""
)
CPP_VALUE_OPTIONS = {"-cpp-command", "-cpp-extra-args", "-cpp-extra-args-per-file"}
CPP_SWITCHES = {"-cpp-frama-c-compliant", "-no-cpp-frama-c-compliant"}


def static_command(text):
    """Decode literal shell words, or return None for shell syntax such as
    expansions, pipelines, wildcards, or an unterminated quote."""
    text = text.strip(" \t")
    args = []
    while text:
        match = SHELL_WORD.match(text)
        if match is None:
            return None
        args.extend(shlex.split(match[0]))
        text = text[match.end():].lstrip(" \t")
    return tuple(args) or None


def fixture_preprocessing(text):
    """Decode the archived fixture's extra flags. The only analysis options
    ignored here are the fixture's switches that suppress Eva results."""
    if text == "-":
        return ()
    args = static_command(text or "")
    if args is None:
        return None
    kept = []
    i = 0
    while i < len(args):
        arg = args[i]
        name, equals, _ = arg.partition("=")
        if name in CPP_VALUE_OPTIONS or name == "-eva-no-results-domain":
            if not equals:
                if (i + 1 == len(args)
                        or args[i + 1].startswith(("-cpp-", "-eva-", "-lib-entry"))):
                    return None
                i += 1
            if name in CPP_VALUE_OPTIONS:
                kept.append((arg,) if equals else (arg, args[i]))
        elif arg in CPP_SWITCHES or arg in ("-lib-entry", "-no-lib-entry"):
            kept.append((arg,))
        elif arg != "-eva-no-results":
            return None
        i += 1
    return tuple(kept)


def fixture_preprocessing_command(args):
    options = fixture_preprocessing(args.flags)
    if options is None:
        print("Cannot decode the archived fixture options.", file=sys.stderr)
        return 1
    for group in options:
        for arg in group:
            sys.stdout.buffer.write(arg.encode("utf-8", "surrogateescape") + b"\0")
    return 0


def recorded_preprocessing(run_dir, run):
    """The archived binary provenance and preprocessing command arguments,
    or None when the recorded command cannot be interpreted. Fixtures
    record their source and extra flags in place of a parse log."""
    revision = run.get("revision", "")
    patch = run.get("patch_sha256", "-")
    if not re.fullmatch(r"[0-9a-f]{40}", revision) or (
            patch != "-" and not valid_sha256(patch)):
        return None
    binary = (revision, patch.lower())
    log = existing(os.path.join(run_dir, "parse.log"))
    case, mode = run.get("case", ""), run.get("mode", "")
    if log:
        snapshot = re.compile(
            r"(?:^|(?<=[= ]))~?/[^\s=\"']*?/runs/%s/%s/src(?=[/=\s]|$)"
            % (re.escape(case), re.escape(mode)))
        commands = []
        with open_text(log) as f:
            for line in f:
                if not line.startswith("Command: "):
                    continue
                args = static_command(line[len("Command: "):].rstrip("\n"))
                if (not args or not line.endswith("\n")
                        or any(a.split("=", 1)[0] in SEQUENCING for a in args)
                        or os.path.basename(args[0]) not in ("frama-c", "frama-c-measure")):
                    return None
                commands.append(tuple(snapshot.sub("${SRC}", arg) for arg in args))
        return (binary, tuple(commands)) if commands else None
    fixture = re.fullmatch(r"fixtures/([^/]+)/default", case)
    source = fixture and os.path.join(run_dir, fixture.group(1))
    if source and os.path.isfile(source):
        flags = fixture_preprocessing(run.get("extra_eva_flags"))
        if flags is not None:
            with open(source, "rb") as f:
                digest = hashlib.sha256(f.read()).hexdigest()
            return binary, digest, flags
    return None


# ----- Comparison of two runs -----------------------------------------------

def run_numbering(run_a, run_b, recorded_a=None, recorded_b=None):
    """The evidence that two runs number the statements alike, from their
    run.tsv (see numbering_state). A run of this runner records the SHA-256
    of its AST listing (ast_sha256, - when it could not be listed), the
    format of the listing and the digests of its preprocessing; a listing of
    another format establishes nothing. When both runs have their AST
    listed again after the campaign (ast_source imported) and no digest of
    their preprocessing, equal AST digests and equal [recorded_a] and
    [recorded_b] (recorded_preprocessing) give the numbering recorded
    command. A run recorded before the AST digest existed has no such
    field: the numbering of the two runs is then asserted when they have
    the same case, revision and patch of the analyzer, revision of the case
    studies and extra options, the extra options being the only ones that
    differ between the preprocessing of two modes; otherwise it is not
    established."""
    if "ast_sha256" in run_a and "ast_sha256" in run_b:
        if any(r.get("ast_format") != AST_FORMAT for r in (run_a, run_b)):
            return "not established"
        digest_a, digest_b = run_a["ast_sha256"], run_b["ast_sha256"]
        archived = all(r.get("ast_source") == "imported"
                       and "pp_command_sha256" not in r
                       and "pp_text_sha256" not in r
                       for r in (run_a, run_b))
        if archived and valid_sha256(digest_a) and valid_sha256(digest_b):
            if digest_a.lower() != digest_b.lower():
                return "different"
            if recorded_a is not None and recorded_a == recorded_b:
                return "recorded command"
            return "not established"
        return numbering_state(digest_a, digest_b,
                               pp_a=preprocessing_digest(run_a),
                               pp_b=preprocessing_digest(run_b))
    if any("pp_command_sha256" in r or "pp_text_sha256" in r
           for r in (run_a, run_b)):
        return "not established"
    same = all(run_a.get(k) and run_a.get(k) == run_b.get(k)
               for k in ("case", "revision", "patch_sha256", "oscs_revision",
                         "extra_eva_flags"))
    return numbering_state(run_a.get("ast_sha256"), run_b.get("ast_sha256"),
                           asserted=same)


MANIFESTS = {}


def configured_entry_point(output, run):
    """The entry point configured for the target of a run: the field
    entry_point of its run.tsv; for a run recorded before the field
    existed, the column entry_point of the manifest that the campaign used
    (provenance/manifest.tsv) for its case. None when neither records it:
    it is not read from the command of the run, and it has no default."""
    if run.get("entry_point") not in (None, "", "-"):
        return run["entry_point"]
    manifest = os.path.join(output, "provenance", "manifest.tsv")
    if manifest not in MANIFESTS:
        MANIFESTS[manifest] = {}
        if os.path.exists(manifest):
            MANIFESTS[manifest] = {r.get("case"): r.get("entry_point")
                                   for r in read_manifest(manifest)}
    entry = MANIFESTS[manifest].get(run.get("case"))
    return entry if entry not in (None, "", "-") else None


def snapshot_pattern(case, mode):
    """The directory of the source snapshot of a run, wherever the output
    directory is: written ${SRC} in the alarms."""
    return re.compile(r"^.*/runs/%s/%s/src(?=/|$)"
                      % (re.escape(case), re.escape(mode)))


def compare_runs(output, case, mode_a, mode_b):
    """Compares two runs of a case of a campaign output directory as the
    runner does: alignment of the records, with the evidence of numbering
    and the outcomes of run.tsv, state queries and alarms. Writes
    comparisons/CASE/A-vs-B/. Does nothing when a run is missing."""
    run_a = os.path.join(output, "runs", case, mode_a)
    run_b = os.path.join(output, "runs", case, mode_b)
    if not (os.path.isdir(run_a) and os.path.isdir(run_b)):
        return
    out = os.path.join(output, "comparisons", case,
                       "%s-vs-%s" % (mode_a, mode_b))
    os.makedirs(out, exist_ok=True)
    with open_text(os.path.join(out, "pair.tsv"), "w") as f:
        f.write("case\t%s\nbaseline\t%s\ncandidate\t%s\n"
                % (case, mode_a, mode_b))
    tsv_a = read_kv(os.path.join(run_a, "run.tsv"))
    tsv_b = read_kv(os.path.join(run_b, "run.tsv"))
    numbering = run_numbering(tsv_a, tsv_b,
                              recorded_preprocessing(run_a, tsv_a),
                              recorded_preprocessing(run_b, tsv_b))
    records_a = existing(os.path.join(run_a, "records.jsonl"))
    records_b = existing(os.path.join(run_b, "records.jsonl"))
    if records_a and records_b:
        # Without the entry point of both runs, the alignment has none: the
        # one of a run is not taken for the other.
        entry_a = configured_entry_point(output, tsv_a)
        entry_b = configured_entry_point(output, tsv_b)
        if entry_a is None or entry_b is None:
            entry_a = entry_b = None
        write_alignment(os.path.join(out, "alignment-"), records_a,
                        records_b, numbering,
                        (tsv_a.get("outcome") or None,
                         tsv_b.get("outcome") or None), entry_a, entry_b)
    queries_a = existing(os.path.join(run_a, "queries.tsv"))
    queries_b = existing(os.path.join(run_b, "queries.tsv"))
    if queries_a and queries_b:
        summary, details, unpaired, reach = compare_queries(
            queries_a, queries_b, numbering)
        write_queries(os.path.join(out, "queries-"), summary, details,
                      unpaired, reach)
    alarms_a = os.path.join(run_a, "alarms.csv")
    alarms_b = os.path.join(run_b, "alarms.csv")
    if os.path.exists(alarms_a) and os.path.exists(alarms_b):
        summary, details = compare_alarms(
            alarms_a, alarms_b, [snapshot_pattern(case, mode_a)],
            [snapshot_pattern(case, mode_b)])
        with open_text(os.path.join(out, "alarms-summary.tsv"), "w") as f:
            for key, value in summary.items():
                f.write("%s\t%s\n" % (key, value))
        with open_text(os.path.join(out, "alarms-differences.tsv"), "w") as f:
            for row in details:
                f.write("difference\t" + "\t".join(row) + "\n")


def compare_command(args):
    compare_runs(args.output, args.case, args.a, args.b)
    return 0


def exit_status(text):
    """An exit status recorded in run.tsv, or None when it was not recorded
    or is not a bounded decimal: an absent status is not a success."""
    return decimal(text)


DIGEST_COLUMNS = ("case", "mode", "ast_format", "ast_sha256",
                  "ast_statements", "parse_exit")


def load_ast_digests(path):
    """The rows of a file of AST digests written by tools/export-ast.sh,
    each checked before any run is updated: the rows that are valid, by
    (case, mode), and the reasons of those that are not. A valid row has
    every column of DIGEST_COLUMNS, the listing format AST_FORMAT, a SHA-256
    of 64 hexadecimal digits, a statement count that is a bounded decimal
    and the parse exit 0, ends with a newline, and is the only row of its
    run. Comment lines start with #."""
    valid, invalid = OrderedDict(), OrderedDict()
    with open(path, encoding="utf-8", errors="surrogateescape") as f:
        lines = (line for line in f if not line.startswith("#"))
        first = next(lines, "")
        if not first.endswith("\n"):
            raise TSVError("%s: missing or incomplete header" % path)
        header = first.rstrip("\n").split("\t")
        validate_tsv_header(path, header, DIGEST_COLUMNS)
        for line in lines:
            fields = line.rstrip("\n").split("\t")
            row = dict(zip(header, fields))
            key = (row.get("case", ""), row.get("mode", ""))
            problem = None
            if not line.endswith("\n"):
                problem = "the file does not end with a complete line"
            elif len(fields) != len(header):
                problem = "%d fields instead of %d" % (len(fields), len(header))
            elif not all(key):
                problem = "missing case or mode"
            elif row["ast_format"] != AST_FORMAT:
                problem = "listing format %s" % row["ast_format"]
            elif not valid_sha256(row["ast_sha256"]):
                problem = "invalid SHA-256"
            elif decimal(row["ast_statements"]) is None:
                problem = "invalid statement count"
            elif row["parse_exit"] != "0":
                problem = "parse exit %s" % row["parse_exit"]
            if key in valid or key in invalid:
                valid.pop(key, None)
                problem = "listed twice"
            if problem:
                invalid[key] = problem
            else:
                valid[key] = row
    return valid, invalid


def import_digest(run, valid, invalid):
    """Sets in [run] (its run.tsv) the digest of its AST from the rows of
    load_ast_digests. A run that recorded its digest itself keeps it; the
    digest imported earlier by recompute is replaced. An invalid row sets
    the digest -, so that the numbering of the run is not established.
    Returns the reason of an invalid row of the run, or None."""
    key = (run.get("case"), run.get("mode"))
    if key not in valid and key not in invalid:
        return None
    problem = invalid.get(key)
    if "ast_sha256" in run and run.get("ast_source") != "imported":
        return problem
    if problem:
        run.update(ast_format="-", ast_sha256="-", ast_statements="-")
    else:
        row = valid[key]
        run.update((k, row[k]) for k in ("ast_format", "ast_sha256",
                                         "ast_statements"))
    run["ast_source"] = "imported"
    run["ast_import_problem"] = problem or "-"
    return problem


def recompute_command(args):
    """Recomputes from the raw logs of a campaign output directory what the
    tools derive from them: the records of each run, its outcome (for a
    measured run), the comparisons of every pair already compared, and the
    tables. With --ast-digests, sets the digest of the AST of the runs that
    it lists, re-exported after the campaign by tools/export-ast.sh: every
    row is checked first (load_ast_digests), and the invalid ones are
    reported on the standard error."""
    valid, invalid = OrderedDict(), OrderedDict()
    if args.ast_digests:
        valid, invalid = load_ast_digests(args.ast_digests)
    for dirpath, _, filenames in sorted(os.walk(os.path.join(args.run_dir,
                                                             "runs"))):
        if "run.tsv" not in filenames:
            continue
        run = read_kv(os.path.join(dirpath, "run.tsv"))
        log = existing(os.path.join(dirpath, "eva.log"))
        if log:
            records = os.path.join(dirpath, "records.jsonl")
            if log.endswith(".gz"):
                records += ".gz"
            with open_text(os.path.join(dirpath, "records-problems.log"),
                           "w") as err, contextlib.redirect_stderr(err):
                records_command(argparse.Namespace(log=log, output=records))
        if os.path.exists(os.path.join(dirpath, "measure")):
            run["outcome"], run["oom_evidence"] = run_outcome(
                dirpath, exit_status(run.get("parse_exit")),
                exit_status(run.get("make_exit")),
                run.get("dedicated_scope") == "yes",
                configured_entry_point(args.run_dir, run))
        problem = import_digest(run, valid, invalid)
        if problem:
            sys.stderr.write("ast-digests: %s %s: %s\n"
                             % (run.get("case"), run.get("mode"), problem))
        with open_text(os.path.join(dirpath, "run.tsv"), "w") as f:
            for key, value in run.items():
                f.write("%s\t%s\n" % (key, value))
    for _, pair in comparison_pairs(args.run_dir)[0]:
        compare_runs(args.run_dir, pair["case"], pair["baseline"],
                     pair["candidate"])
    return tables_command(args)


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


def cell(value):
    if value is None or value == "":
        return "-"
    if value is True or value is False:
        return "True" if value else "False"
    return value


# The summaries of a comparison, as this tool writes them: each field in
# its order, with the check of its value. A table reads a summary only when
# the file holds exactly these fields with valid values (read_summary):
# a field of a file cut, edited or written by another revision is not
# evidence of a result.
def _count(value):
    return decimal(value) is not None


def _flag(value):
    return value in ("True", "False")


def _text(value):
    return value != ""


def _status(value):
    return value == "complete" or value.startswith("incomplete: ")


ALIGNMENT_SUMMARY = (
    [(k, _count) for k in (
        "records_a", "records_b", "inferred_a", "inferred_b", "aligned",
        "aligned_with_inferred", "aligned_same_dispositions",
        "aligned_other_dispositions", "hit_a_analysed_b", "analysed_a_hit_b",
        "nested_under_hit_a", "nested_under_hit_b", "unmatched_a",
        "unmatched_b", "undecided_groups", "undecided_records_a",
        "undecided_records_b")]
    + [("interrupted_a", _flag), ("interrupted_b", _flag),
       ("problems_a", _count), ("problems_b", _count),
       ("statement_numbers_a", ("all", "none", "some").__contains__),
       ("statement_numbers_b", ("all", "none", "some").__contains__),
       ("numbering", NUMBERINGS.__contains__), ("entry_point", _text),
       ("entry_point_a", _flag), ("entry_point_b", _flag),
       ("outcome_a", _text), ("outcome_b", _text), ("accounted", _flag),
       ("complete", _flag), ("verdict", _text)])
QUERIES_SUMMARY = (
    [("queries", _count), ("numbering", NUMBERINGS.__contains__)]
    + [(k, _count) for k in (
        "unpaired", "answered_a", "answered_b", "answered_both", "equal",
        "wider", "narrower", "incomparable", "undecided", "top_a", "top_b",
        "garbled_a", "garbled_b")]
    + [("unavailable_%s_%s" % (side, reason), _count)
       for side in ("a", "b") for reason in UNAVAILABLE_REASONS + ("other",)]
    + [("reached_a", _count), ("reached_b", _count),
       ("reached_a_only", lambda v: v == "-" or _count(v)),
       ("reached_b_only", lambda v: v == "-" or _count(v)),
       ("complete_a", _status), ("complete_b", _status),
       ("comparison", _status)])
ALARMS_SUMMARY = [(k, _count) for k in (
    "properties_a", "properties_b", "keys_a", "keys_b", "duplicate_keys_a",
    "duplicate_keys_b", "same_status", "other_status", "a_only", "b_only")]
# For each summary: its fields, and a check that its verdict does not say
# more than its other fields.
SUMMARIES = {
    "alignment": (ALIGNMENT_SUMMARY, lambda s: (
        (s["complete"] == "True") == (s["verdict"] == "complete"))),
    "queries": (QUERIES_SUMMARY, lambda s: s["comparison"] != "complete" or (
        s["complete_a"] == s["complete_b"] == "complete"
        and s["numbering"] == "same")),
    "alarms": (ALARMS_SUMMARY, lambda s: True),
}


def read_summary(path, name):
    """The summary [name] (alignment, queries or alarms) of a comparison,
    or {} when the file is missing or is not a summary of this tool: every
    field of SUMMARIES[name], once, in its order, on a complete line, with a
    valid value, and a verdict that its other fields allow."""
    fields, consistent = SUMMARIES[name]
    if not os.path.exists(path):
        return {}
    with open_text(path) as f:
        lines = f.read().split("\n")
    if lines.pop() != "" or len(lines) != len(fields):
        return {}
    summary = OrderedDict()
    for line, (key, valid) in zip(lines, fields):
        found, separator, value = line.partition("\t")
        if found != key or not separator or not valid(value):
            return {}
        summary[key] = value
    return summary if consistent(summary) else {}


def read_pair(root, dirpath):
    """The case and the two modes of a comparison directory, from its
    pair.tsv, or None when the file does not give them or names another
    directory than comparisons/CASE/A-vs-B."""
    pair = read_kv(os.path.join(dirpath, "pair.tsv"))
    if not all(pair.get(k) for k in ("case", "baseline", "candidate")):
        return None
    named = os.path.join(pair["case"], "%s-vs-%s" % (pair["baseline"],
                                                    pair["candidate"]))
    if os.path.relpath(dirpath, os.path.join(root, "comparisons")) != named:
        return None
    return pair


def comparison_pairs(root):
    """The comparison directories of an output directory with their pairs
    (read_pair), sorted, and the directories left out, relative to [root]:
    those whose pair.tsv is not valid, which are named on the standard
    error too."""
    comparisons, left_out = [], []
    for dirpath, _, filenames in os.walk(os.path.join(root, "comparisons")):
        if "pair.tsv" not in filenames:
            continue
        pair = read_pair(root, dirpath)
        if pair is None:
            print("%s: pair.tsv does not name this comparison; left out"
                  % dirpath, file=sys.stderr)
            left_out.append(os.path.relpath(dirpath, root))
        else:
            comparisons.append((dirpath, pair))
    comparisons.sort(key=lambda c: (c[1]["case"], c[1]["baseline"],
                                    c[1]["candidate"]))
    return comparisons, left_out


NESTED_HIT_CHECK = ("PASS nested-hit: two runs of the same binary align "
                    "completely")


def tables_command(args):
    root = args.run_dir
    runs_dir = os.path.join(root, "runs")
    runs, left_out = [], []
    for dirpath, _, filenames in os.walk(runs_dir):
        if "run.tsv" not in filenames:
            continue
        run = read_kv(os.path.join(dirpath, "run.tsv"))
        named = os.path.join(run.get("case", ""), run.get("mode", ""))
        if os.path.relpath(dirpath, runs_dir) != named:
            # The files of a run are read from runs/CASE/MODE: a run.tsv
            # that names another run would give its cells to that one.
            print("%s: run.tsv does not name this run; left out" % dirpath,
                  file=sys.stderr)
            left_out.append(os.path.relpath(dirpath, root))
            continue
        runs.append(run)
    runs.sort(key=lambda r: (r["case"], r["mode"]))
    by_run = {(r["case"], r["mode"]): r for r in runs}
    recorded = {}
    if args.recorded_set_a:
        for row in read_header_tsv(args.recorded_set_a, ("target", "in_A"),
                                   comments=True):
            target = row["target"]
            if not target or target in recorded or row["in_A"] not in ("True", "False"):
                raise TSVError("%s: invalid or repeated set A entry %r"
                               % (args.recorded_set_a, target))
            recorded[target] = row["in_A"]
    out_dir = os.path.join(root, "tables")
    os.makedirs(out_dir, exist_ok=True)
    md = io.StringIO()
    md.write("# Result tables\n\nProduced by `campaign.py tables` from "
             "`%s`. A cell `-` means that the source of its column does "
             "not give the value; it is never a zero. Each table names its "
             "source.\n\n" % os.path.basename(os.path.abspath(root)))
    comparisons, unnamed = comparison_pairs(root)
    left_out += unnamed
    if left_out:
        md.write("Left out of every table, because the `run.tsv` or the "
                 "`pair.tsv` of the directory does not name it: %s.\n\n"
                 % ", ".join("`%s`" % d for d in sorted(left_out)))

    # Outcomes, time and memory.
    keys = ["case", "mode", "outcome", "exit", "signal", "watchdog",
            "oom_evidence", "elapsed_s", "user_s", "maxrss_kib", "timeout_s"]
    header = keys[:-1] + ["limit_s"]
    rows = [[cell(r.get(k)) for k in keys] for r in runs]
    write_tsv(os.path.join(out_dir, "outcomes.tsv"), header, rows)
    md.write("## Outcomes, time and memory per invocation\n\nFrom the "
             "`run.tsv` of each run. `watchdog` is the last signal sent at "
             "the wall-time limit (`none` when it did not fire); "
             "`oom_evidence` the evidence that memory was exhausted.\n\n")
    md.write(markdown_table(header, rows) + "\n")

    # Counters of the statistics file, and dispositions counted in the log:
    # two sources, each in its own tables.
    activity_header = [
        "case", "mode", "export_rows", "hits", "misses", "stored", "refused",
        "refused_by_reason", "allocation_and_release_rows",
        "allocation_and_release", "in_set_a", "recorded_in_set_a", "agrees"]
    collector_keys = [
        "collector_would_store", "collector_refused",
        "collector_refused_by_reason", "producer_stored", "producer_refused",
        "producer_refused_by_reason", "supplied_hits", "supplied_rejected",
        "supplied_refused", "supplied_rejected_by_reason",
        "supplied_refused_by_reason"]
    activity_rows, collector_rows, function_rows, log_rows = [], [], [], []
    for r in runs:
        run_dir = os.path.join(runs_dir, r["case"], r["mode"])
        name = [r["case"], r["mode"]]
        stats = os.path.join(run_dir, "eva-stats.csv")
        counters, export_rows, problem = read_statistics(stats)
        if problem and os.path.exists(stats):
            print("%s: %s; its counters are not read" % (stats, problem),
                  file=sys.stderr)
        c = statistics_counts(counters, export_rows)
        function_rows.extend(name + [cell(x) for x in row]
                             for row in function_counts(counters))
        rec = recorded.get(r["case"].rsplit("/", 1)[0])
        agrees = None
        if rec and c["in_set_a"] is not None:
            agrees = "yes" if rec == cell(c["in_set_a"]) else "NO"
        activity_rows.append(name + [cell(c[k]) for k in (
            "export_rows", "hits", "misses", "stored", "refused",
            "refused_by_reason", "allocation_and_release_rows",
            "allocation_and_release", "in_set_a")] + [cell(rec),
                                                       cell(agrees)])
        collector_rows.append(name + [cell(c[k]) for k in collector_keys])
        logged, kinds = log_counts(existing(os.path.join(run_dir,
                                                         "eva.log")))
        logged["sources"] = compare_sources(kinds, counters, problem)
        log_rows.append(name + [cell(logged[k]) for k in LOG_COLUMNS])
    write_tsv(os.path.join(out_dir, "activity.tsv"), activity_header,
              activity_rows)
    md.write("## Counters of the statistics file: cache activity and set "
             "A\n\nSource: the rows of `eva-stats.csv`, which holds the "
             "export of the last analysis of the invocation that ended. A "
             "number is the sum of the rows of its counter. `-` means that "
             "the file "
             "has no row of that counter, or is not a complete export "
             "(`export_rows`, the number of its rows, is then `-` too). The "
             "analyzer writes a row for a counter only once it has "
             "incremented it: a cell is 0 only when a row holds 0, and no "
             "value is taken from the options of the run, from its log or "
             "from another row. `hits`, `misses`, `stored` and `refused` "
             "are the `memexec-*` rows. `allocation_and_release` sums the "
             "rows of the allocation and release builtins, and "
             "`allocation_and_release_rows` counts them: its 0 means that "
             "there is no such row among the `export_rows` rows of this "
             "file. `in_set_a` is `False` when that sum is positive, "
             "`True` when rows give the sum 0, and `-` without such a row. "
             "`recorded_in_set_a` is the membership recorded by the "
             "earlier measurement; `agrees` compares the two when "
             "`in_set_a` is not `-`.\n\n")
    md.write(markdown_table(activity_header, activity_rows) + "\n")
    header = ["case", "mode"] + collector_keys
    write_tsv(os.path.join(out_dir, "collector.tsv"), header,
              collector_rows)
    md.write("## Counters of the statistics file: collector, producer and "
             "supplied entries\n\nSame source and same reading as the "
             "previous table: the rows `collector-*` (verdicts of the body "
             "access collector), `cache-produced` and "
             "`cache-production-refused-*` (the producer), and "
             "`cache-hits`, `cache-rejected-*` and `cache-refused-*` "
             "(entries supplied by a test module).\n\n")
    md.write(markdown_table(header, collector_rows) + "\n")

    # Counters per function, in a file of its own.
    write_tsv(os.path.join(out_dir, "functions.tsv"),
              ["case", "mode", "function", "hits", "misses", "stored",
               "refused", "collector_would_store", "collector_refused"],
              function_rows)
    md.write("The `memexec-*` and `collector-*` rows of each function are "
             "in `functions.tsv`, read in the same way: `-` where the "
             "function has no row of the counter.\n\n")

    header = ["case", "mode"] + LOG_COLUMNS
    write_tsv(os.path.join(out_dir, "log.tsv"), header, log_rows)
    md.write("## Dispositions counted in the Eva log (log-derived)\n\n"
             "Source: the `[eva:cache]` messages of `eva.log`, one "
             "disposition line per call, counted by the words of their "
             "fields. These are counts of lines of the log, not counters "
             "of the statistics file: the two sources are never added, and "
             "neither stands for the other. `analysis_starts` counts the "
             "lines `[eva] Analyzing ... application starting at ...`. A "
             "count of 0, or `none` in a list by reason, means that there "
             "is no such line among the `disposition_lines` disposition "
             "lines of this log. The counts by kind are `-` unless the log "
             "has exactly one analysis start, at least one disposition "
             "line, and no cache message of a form the tool does not "
             "know; `log_note` then says why. The columns of the collector "
             "and of the producer are `-` when no disposition line has "
             "that field: the analyzer prints the producer field only "
             "under the message category `cache-producer`, and the kinds "
             "of a field that the log does not print are not compared. "
             "`lookup_rejected` counts the "
             "rejected candidates, the other columns count lines. `sources` "
             "compares each kind that has a counter with the rows of the "
             "statistics file: `agree on N kind(s)` when N kinds have the "
             "same number in both, `disagree:` followed by each kind whose "
             "two numbers differ or that the log shows and no row "
             "counts.\n\n")
    md.write(markdown_table(header, log_rows) + "\n")

    # Times of the modes.
    header = ["case", "nocache_s", "cache_s", "reference_s",
              "cache_over_nocache", "cache_over_reference"]
    rows = time_rows(runs)
    write_tsv(os.path.join(out_dir, "times.tsv"), header, rows)
    md.write("## Elapsed time per mode\n\nFrom the `run.tsv` of the first "
             "run of each mode: its elapsed time, or its outcome when it "
             "did not complete. `no run` means that the directory has no "
             "run of the mode, `no outcome` and `no time` that the run "
             "records none. A ratio is given only when both runs completed "
             "and have a time.\n\n")
    md.write(markdown_table(header, rows) + "\n")

    # Comparisons.
    def completed(pair):
        """Whether both runs of a pair completed, or None when the outcome
        of one is not recorded."""
        outcomes = [by_run.get((pair["case"], pair[k]), {}).get("outcome")
                    for k in ("baseline", "candidate")]
        if any(o in (None, "", "-") for o in outcomes):
            return None
        return all(o == "completed" for o in outcomes)

    align_keys = ["records_a", "records_b", "inferred_a", "inferred_b",
                  "aligned", "aligned_other_dispositions", "hit_a_analysed_b",
                  "analysed_a_hit_b", "nested_under_hit_a",
                  "nested_under_hit_b", "unmatched_a", "unmatched_b",
                  "undecided_groups", "problems_a", "problems_b",
                  "numbering", "accounted", "complete", "verdict"]
    query_keys = (["queries", "numbering", "unpaired", "answered_both",
                   "equal", "wider", "narrower", "incomparable", "undecided",
                   "top_a", "top_b"]
                  + ["unavailable_%s_%s" % (side, reason)
                     for reason in UNAVAILABLE_REASONS + ("other",)
                     for side in ("a", "b")]
                  + ["reached_a_only", "reached_b_only", "complete_a",
                     "complete_b", "comparison"])
    alarm_keys = ["properties_a", "properties_b", "duplicate_keys_a",
                  "duplicate_keys_b", "same_status", "other_status",
                  "a_only", "b_only"]
    alignment_results = {}
    for title, name, keys in (
            ("Alignment of the per-call records", "alignment", align_keys),
            ("State queries", "queries", query_keys),
            ("Alarms and property statuses", "alarms", alarm_keys)):
        header = ["case", "A", "B", "both_completed"] + keys
        rows = []
        compared = both = 0
        for dirpath, pair in comparisons:
            path = os.path.join(dirpath, name + "-summary.tsv")
            values = read_summary(path, name)
            if not values and os.path.exists(path):
                print("%s: not a valid summary; its fields are not read"
                      % path, file=sys.stderr)
            done = completed(pair)
            if name == "alignment":
                key = (pair["case"], pair["baseline"], pair["candidate"])
                alignment_results[key] = values
            if values:
                compared += 1
                both += done is True
            rows.append([pair["case"], pair["baseline"], pair["candidate"],
                         cell(done)]
                        + [cell(values.get(k)) for k in keys])
        write_tsv(os.path.join(out_dir, name + ".tsv"), header, rows)
        md.write("## %s\n\nRun A is the baseline, run B the candidate. "
                 "Pairs: %d, with a valid summary: %d, of which both runs "
                 "completed: %d. A pair without a valid summary has `-` in "
                 "every column of the comparison; `both_completed` is `-` "
                 "when the outcome of a run is not recorded.\n\n"
                 % (title, len(comparisons), compared, both))
        md.write(markdown_table(header, rows) + "\n")
    # The checks of the fixtures and of the outcome demonstration, which
    # pilot.sh writes next to the runs. They are copied as they were
    # recorded: the tables do not run them again.
    revision_path = os.path.join(root, "provenance", "campaign-revision.txt")
    revision = "unavailable"
    if os.path.isfile(revision_path):
        with open_text(revision_path) as f:
            first = f.readline().split()
        if first and re.fullmatch(r"[0-9a-f]{7,40}", first[0]):
            revision = first[0]
    sections = []
    for name, title, what in (
            ("fixtures.txt", "Checks on the constructed cases",
             "Checks of `fixtures/run-fixtures.sh`"),
            ("outcome-demo.txt", "Outcome classes of the runner",
             "Constructed runs of `tools/outcome-demo.sh`, caching "
             "disabled,")):
        path = os.path.join(args.run_dir, name)
        if not os.path.exists(path):
            continue
        with open_text(path) as f:
            checks = f.read()
        intro = ("%s as recorded when the campaign ran (harness revision "
                 "`%s`). `tables` copies these lines and does not check "
                 "them again.\n\n" % (what, revision))
        if name == "fixtures.txt" and NESTED_HIT_CHECK in checks.splitlines():
            key = ("fixtures/nested-hit.c/default", "cache", "cache.2")
            nested_hit = alignment_results.get(key)
            valid = [s for s in alignment_results.values() if s]
            count = sum(s["complete"] == "True" for s in valid)
            if not nested_hit:
                intro += ("Current alignment unavailable: this directory "
                          "has no valid alignment summary of the two "
                          "memexec runs of `nested-hit.c`.\n\n")
            elif nested_hit["complete"] == "False":
                intro += (
                    "The alignment result of the recorded check is "
                    "superseded. Current result: %d of %d alignments with "
                    "a valid summary are complete. The alignment of the "
                    "two memexec runs of `nested-hit.c` in this directory "
                    "has numbering `%s`, `complete=False` and the verdict "
                    "`%s`.\n\n"
                    % (count, len(valid), nested_hit["numbering"],
                       nested_hit["verdict"]))
            else:
                intro += ("Current result: the alignment of the two "
                          "memexec runs of `nested-hit.c` in this "
                          "directory is `complete=True`.\n\n")
        sections.append("## %s\n\n%s```\n%s```\n" % (title, intro, checks))
    md.write("\n".join(sections))
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
    return list(read_header_tsv(path, MANIFEST_HEADER, comments=True))


BINARIES_COLUMNS = ("role", "checkout", "revision", "patch_sha256", "patch",
                    "frama_c_sha256", "eva_cmxs_sha256", "counter_families",
                    "version")


def binaries_get_command(args):
    rows = {}
    for row in read_header_tsv(args.binaries, BINARIES_COLUMNS):
        role = row["role"]
        if not role or role in rows:
            raise TSVError("%s: empty or repeated binary role %r"
                           % (args.binaries, role))
        rows[role] = row
    if args.role is not None:
        if args.role not in rows:
            raise TSVError("%s: missing binary role %r" % (args.binaries, args.role))
        rows = {args.role: rows[args.role]}
    for row in rows.values():
        print("\t".join(row[field] for field in args.fields))
    return 0


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
    p.add_argument("--ast-a", help="SHA-256 of the AST of run A")
    p.add_argument("--ast-b", help="SHA-256 of the AST of run B")
    p.add_argument("--pp-a", help="digests of the preprocessing of run A, "
                   "PP_COMMAND_SHA256:PP_TEXT_SHA256")
    p.add_argument("--pp-b", help="digests of the preprocessing of run B")
    p.add_argument("--assert-numbering", action="store_true",
                   help="for runs recorded before the AST digest: assert "
                   "that a run without digest numbers the statements as "
                   "the other; nothing of the two programs is compared")
    p.add_argument("--outcome-a", help="outcome of run A")
    p.add_argument("--outcome-b", help="outcome of run B")
    p.add_argument("--entry-point",
                   help="the entry point configured for the target")
    p.set_defaults(func=align_command)
    p = sub.add_parser("queries")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("output", nargs="?")
    p.add_argument("--ast-a", help="SHA-256 of the AST of run A")
    p.add_argument("--ast-b", help="SHA-256 of the AST of run B")
    p.add_argument("--pp-a", help="digests of the preprocessing of run A, "
                   "PP_COMMAND_SHA256:PP_TEXT_SHA256")
    p.add_argument("--pp-b", help="digests of the preprocessing of run B")
    p.add_argument("--assert-numbering", action="store_true",
                   help="as for align")
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
    p.add_argument("stats", help="statistics file of an Eva invocation")
    p.add_argument("--log", help="Eva log of the same invocation: its "
                   "dispositions are counted too, under their own names")
    p.set_defaults(func=counts_command)
    p = sub.add_parser("families")
    p.add_argument("cmxs", help="the compiled Eva plugin of a binary")
    p.set_defaults(func=families_command)
    p = sub.add_parser("provenance")
    p.add_argument("checkout")
    p.add_argument("role")
    p.add_argument("patches", help="directory that receives ROLE.patch")
    p.set_defaults(func=provenance_command)
    p = sub.add_parser("home")
    p.add_argument("action",
                   choices=("check", "check-tree", "check-links", "redact",
                            "redact-tree"))
    p.add_argument("paths", nargs="*")
    p.add_argument("--keep", action="append", default=[],
                   help="a file of the tree, relative to it, left as it is")
    p.add_argument("--link-root", help="original root for checking a staged copy")
    p.set_defaults(func=home_command)
    p = sub.add_parser("measure")
    p.add_argument("measure")
    p.set_defaults(func=measure_command)
    p = sub.add_parser("outcome")
    p.add_argument("run")
    p.add_argument("parse_exit", type=int)
    p.add_argument("make_exit", type=int)
    p.add_argument("timeout", type=float)
    p.add_argument("--dedicated-scope", action="store_true",
                   help="the runner started the watchdog in a scope of its "
                   "own")
    p.add_argument("--entry-point",
                   help="the entry point configured for the target; without "
                   "it, no run is completed")
    p.set_defaults(func=outcome_command)

    p = sub.add_parser("invocation-outcome")
    p.add_argument("run")
    p.add_argument("exit_status", type=int,
                   help="the exit status of the one invocation of the run")
    p.add_argument("--entry-point", required=True,
                   help="the entry point configured for the target")
    p.set_defaults(func=invocation_outcome_command)
    p = sub.add_parser("tables")
    p.add_argument("run_dir")
    p.add_argument("--recorded-set-a")
    p.set_defaults(func=tables_command)
    p = sub.add_parser("ast")
    p.add_argument("listing", help="AST listing written by the query module")
    p.set_defaults(func=ast_command)
    p = sub.add_parser("preprocessing")
    p.add_argument("log", help="log of a parse step run with "
                   "-kernel-msg-key pp -keep-temp-files")
    p.add_argument("tmp_dir", help="the TMPDIR of that parse step")
    p.add_argument("--source-root", action="append",
                   help="directory of the sources of the run, written ${SRC}")
    p.add_argument("--share", action="append",
                   help="share directory of the binary, written "
                   "${FRAMAC_SHARE}")
    p.add_argument("--commands", help="file to write the commands to, with "
                   "the paths so written")
    p.set_defaults(func=preprocessing_command)
    p = sub.add_parser("compare")
    p.add_argument("output", help="campaign output directory")
    p.add_argument("case")
    p.add_argument("a", help="mode of the baseline run")
    p.add_argument("b", help="mode of the candidate run")
    p.set_defaults(func=compare_command)
    p = sub.add_parser("fixture-preprocessing")
    p.add_argument("flags")
    p.set_defaults(func=fixture_preprocessing_command)
    p = sub.add_parser("recompute")
    p.add_argument("run_dir", help="campaign output directory")
    p.add_argument("--ast-digests",
                   help="digests of the ASTs re-exported after the campaign")
    p.add_argument("--recorded-set-a")
    p.set_defaults(func=recompute_command)
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
    p = sub.add_parser("binaries-get")
    p.add_argument("binaries")
    p.add_argument("fields", nargs="+", choices=BINARIES_COLUMNS)
    p.add_argument("--role")
    p.set_defaults(func=binaries_get_command)
    args = parser.parse_args(argv)
    if getattr(args, "trees", None) is not None and \
       isinstance(args.trees, str):
        trees = {}
        with open(args.trees) as f:
            for line in f:
                directory, _, tree = line.strip().partition("\t")
                trees[directory] = tree
        args.trees = trees
    try:
        return args.func(args)
    except (TSVError, FileNotFoundError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
