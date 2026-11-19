#!/usr/bin/env python3
"""Runs a command under a wall-time watchdog and measures it.

Usage: watchdog.py MEASURE TIMEOUT_S KILL_AFTER_S MEMORY_LIMIT -- COMMAND...

The command runs in a session of its own. When it is still running
TIMEOUT_S seconds after its start, the watchdog sends SIGTERM to its
process group, and SIGKILL KILL_AFTER_S seconds later if it is still
running. MEMORY_LIMIT is an address-space limit in bytes, or - for none.

The watchdog writes to MEASURE one KEY<TAB>VALUE line per value:
  elapsed_s, user_s, sys_s, maxrss_kib  wall time, CPU times and peak
      resident memory of the command (from wait4)
  exit        exit status of the command, or - when a signal ended it
  signal      the signal that ended the command, or -
  core_dumped yes or no
  status      exit status, or 128 + signal
  watchdog    none, term or kill: the last signal sent by the watchdog
  watchdog_term_s, watchdog_kill_s   when it sent them, or -
  oom_kill_events  the increase of the counter oom_kill of the memory
      events of the cgroup of the watchdog during the run, or unreadable
  kernel_log_oom   when the command was ended by SIGKILL that the watchdog
      did not send: yes if the kernel log reports that the out-of-memory
      killer killed it, no if it does not, unreadable when the log cannot
      be read; - otherwise
  cgroup_exclusive  yes if every sample of the processes of that cgroup,
      taken at the start and then every half second, lists only the
      watchdog and the processes of the session of the command; no if a
      sample lists another process; unreadable when the list cannot be
      read. This is evidence only: a sample does not show that the command
      was in the cgroup, nor that no other process ran in it between two
      samples. A positive oom_kill_events names the command only when the
      watchdog runs in a scope created for it, which the runner states with
      --dedicated-scope.
It exits with the status of the command. Only the Python standard library is
used.
"""

import os
import resource
import signal as signals
import subprocess
import sys
import time


def cgroup_events():
    """The memory events file of the cgroup of this process, if readable."""
    try:
        with open("/proc/self/cgroup") as f:
            for line in f:
                hierarchy, _, path = line.rstrip("\n").split(":", 2)
                if hierarchy == "0":
                    events = "/sys/fs/cgroup" + path + "/memory.events"
                    if os.access(events, os.R_OK):
                        return events
    except OSError:
        pass
    return None


def cgroup_procs(events):
    """The file that lists the processes of the cgroup whose memory events
    are [events], or None."""
    if events is None:
        return None
    procs = os.path.join(os.path.dirname(events), "cgroup.procs")
    return procs if os.access(procs, os.R_OK) else None


def foreign_processes(procs, session):
    """Whether the cgroup listed in [procs] holds a process other than this
    one and those of [session]: True, False, or None when unreadable."""
    try:
        with open(procs) as f:
            pids = [int(line) for line in f if line.strip()]
    except (OSError, ValueError):
        return None
    for pid in pids:
        if pid == os.getpid():
            continue
        try:
            if os.getsid(pid) == session:
                continue
        except ProcessLookupError:
            continue
        except OSError:
            return True
        return True
    return False


def oom_kills(events):
    if events is None:
        return None
    try:
        with open(events) as f:
            for line in f:
                key, _, value = line.partition(" ")
                if key == "oom_kill":
                    return int(value)
    except (OSError, ValueError):
        pass
    return None


def kernel_log_oom(pid):
    """Whether the kernel log reports that the out-of-memory killer killed
    the process [pid]: yes, no, or unreadable."""
    try:
        log = subprocess.run(["dmesg"], capture_output=True, text=True,
                             timeout=30)
    except (OSError, subprocess.SubprocessError):
        return "unreadable"
    if log.returncode != 0:
        return "unreadable"
    needle = "Killed process %d " % pid
    return "yes" if any(needle in line for line in log.stdout.splitlines()) \
        else "no"


def main(argv):
    if len(argv) < 6 or argv[4] != "--":
        print(__doc__, file=sys.stderr)
        return 2
    measure, timeout_s, kill_after_s, memory_limit = argv[0:4]
    command = argv[5:]
    timeout_s, kill_after_s = float(timeout_s), float(kill_after_s)

    def limit():
        if memory_limit != "-":
            size = int(memory_limit)
            resource.setrlimit(resource.RLIMIT_AS, (size, size))

    events = cgroup_events()
    kills_before = oom_kills(events)
    start = time.monotonic()
    child = subprocess.Popen(command, preexec_fn=limit,
                             start_new_session=True)

    def forward(signum, _frame):
        try:
            os.killpg(child.pid, signum)
        except ProcessLookupError:
            pass

    for signum in (signals.SIGTERM, signals.SIGINT, signals.SIGHUP):
        signals.signal(signum, forward)
    procs = cgroup_procs(events)
    exclusive = "unreadable" if procs is None else "yes"

    def sample(exclusive):
        if exclusive != "yes":
            return exclusive
        foreign = foreign_processes(procs, child.pid)
        return "unreadable" if foreign is None else "no" if foreign else "yes"

    # A first sample before the command can end, then one every half second.
    exclusive, sampled = sample(exclusive), 0.0
    watchdog, term_s, kill_s = "none", None, None
    while True:
        pid, status, usage = os.wait4(child.pid, os.WNOHANG)
        if pid == child.pid:
            break
        now = time.monotonic() - start
        if now >= sampled + 0.5:
            exclusive, sampled = sample(exclusive), now
        if watchdog == "none" and now >= timeout_s:
            watchdog, term_s = "term", now
            try:
                os.killpg(child.pid, signals.SIGTERM)
            except ProcessLookupError:
                pass
        elif watchdog == "term" and now >= term_s + kill_after_s:
            watchdog, kill_s = "kill", now
            try:
                os.killpg(child.pid, signals.SIGKILL)
            except ProcessLookupError:
                pass
        time.sleep(0.02)
    elapsed = time.monotonic() - start
    kills_after = oom_kills(events)
    if os.WIFSIGNALED(status):
        signal, exit_code = os.WTERMSIG(status), None
        code = 128 + signal
    else:
        signal, exit_code = None, os.WEXITSTATUS(status)
        code = exit_code
    if kills_before is None or kills_after is None:
        oom_events = "unreadable"
    else:
        oom_events = str(kills_after - kills_before)
    kernel = "-"
    if signal == 9 and watchdog != "kill":
        kernel = kernel_log_oom(child.pid)

    def fmt(x):
        return "-" if x is None else "%.2f" % x

    with open(measure, "w") as f:
        for key, value in (
                ("elapsed_s", "%.2f" % elapsed),
                ("user_s", "%.2f" % usage.ru_utime),
                ("sys_s", "%.2f" % usage.ru_stime),
                ("maxrss_kib", str(usage.ru_maxrss)),
                ("exit", "-" if exit_code is None else str(exit_code)),
                ("signal", "-" if signal is None else str(signal)),
                ("core_dumped", "yes" if os.WCOREDUMP(status) else "no"),
                ("status", str(code)),
                ("watchdog", watchdog),
                ("watchdog_term_s", fmt(term_s)),
                ("watchdog_kill_s", fmt(kill_s)),
                ("oom_kill_events", oom_events),
                ("kernel_log_oom", kernel),
                ("cgroup_exclusive", exclusive)):
            f.write("%s\t%s\n" % (key, value))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
