"""
Multi-scale time.

Zimulation 1 advanced in fixed one-year steps. That is far too coarse for
what V2 needs to observe: a hand striking a stone, a signal emitted and
answered, a burn tended through a night, a deception told and believed.
All of those resolve in seconds to hours, and a year-step model cannot
represent them at all -- it can only assert their outcomes, which is
exactly the failure the contract forbids.

But simulating every second for ten thousand years is not possible either.

So time here is *event-driven*: the clock jumps to whenever the next thing
is due. A metabolism update scheduled for tomorrow and a stone-strike due
in two seconds coexist in one queue; nothing is simulated in between,
because by construction nothing happens in between.

## Determinism under an event queue

This is the part that is easy to get wrong, and getting it wrong destroys
reproducibility in a way that is very hard to notice.

Two events scheduled for the same instant must run in a defined order, or
the outcome depends on heap internals and floating-point tie-breaking.
Every task therefore carries a monotonically increasing sequence number,
and ties are broken by (time, priority, sequence). Sequence numbers are
issued in scheduling order, so the order of execution is fully determined
by the order of scheduling -- which is itself determined by the seed.

Times are stored as integers (ticks) rather than floats. Floating-point
addition is not associative, so accumulating a float clock would make
`t += dt` produce different values depending on the order of unrelated
operations. Integer ticks cannot drift.

## Scales

The contract lists seconds to generations. Rather than hard-code bands,
the scheduler takes a tick resolution and lets each process choose its own
period. `SECOND`, `MINUTE`, `HOUR`, `DAY`, `YEAR` are conveniences, not
constraints, and a process may reschedule itself adaptively -- fast while
something is burning, slow while nothing is.
"""

from __future__ import annotations

import heapq

#: One tick is one second of simulated time. Integer arithmetic throughout;
#: see the note on float drift above.
SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
#: 365 days. Orbital detail is a matter for the world model, not the clock.
YEAR = 365 * DAY

#: Lower runs first when two tasks fall on the same tick. Physical
#: consequences resolve before anyone perceives them, and perception
#: resolves before anyone acts on it -- otherwise an agent could act on an
#: event in the same instant it occurred, which no body can do.
PRIORITY_PHYSICS = 0
PRIORITY_PERCEPTION = 1
PRIORITY_COGNITION = 2
PRIORITY_ACTION = 3
PRIORITY_BOOKKEEPING = 9


class Task:
    __slots__ = ("time", "priority", "seq", "fn", "label", "cancelled")

    def __init__(self, time, priority, seq, fn, label):
        self.time = time
        self.priority = priority
        self.seq = seq
        self.fn = fn
        self.label = label
        self.cancelled = False

    def key(self):
        return (self.time, self.priority, self.seq)

    def __lt__(self, other):
        return self.key() < other.key()

    def __repr__(self):
        return f"<Task {self.label} t={self.time} p={self.priority}>"


class Scheduler:
    """
    A deterministic priority queue over integer time.

    Usage is deliberately plain: schedule a callable at a tick, run until a
    horizon. A callable may schedule more work, including itself, which is
    how recurring processes are expressed without a fixed global step.
    """

    __slots__ = ("now", "_heap", "_seq", "_ran", "_horizon")

    def __init__(self, start=0):
        self.now = int(start)
        self._heap = []
        self._seq = 0
        self._ran = 0
        self._horizon = None

    def at(self, time, fn, priority=PRIORITY_ACTION, label=""):
        """Schedule `fn` for an absolute tick."""
        t = int(time)
        if t < self.now:
            raise ValueError(
                f"cannot schedule {label or fn!r} at {t}, which is before "
                f"now ({self.now}); the past is not writable")
        self._seq += 1
        task = Task(t, priority, self._seq, fn, label or getattr(fn, "__name__", "?"))
        heapq.heappush(self._heap, task)
        return task

    def after(self, delay, fn, priority=PRIORITY_ACTION, label=""):
        """Schedule `fn` a number of ticks from now."""
        return self.at(self.now + int(delay), fn, priority, label)

    def every(self, period, fn, priority=PRIORITY_BOOKKEEPING, label="",
              first=None):
        """
        A recurring process.

        Reschedules from its *scheduled* time rather than from completion,
        so periods cannot drift and the sequence of ticks is identical on
        every run.
        """
        period = int(period)
        if period <= 0:
            raise ValueError("period must be positive")
        state = {}

        def tick():
            fn()
            state["task"] = self.at(state["due"] + period, tick, priority,
                                    label or "every")
            state["due"] = state["due"] + period

        start = self.now + period if first is None else int(first)
        state["due"] = start
        state["task"] = self.at(start, tick, priority, label or "every")
        return state

    def run_until(self, horizon):
        """
        Advance to `horizon`, running everything due before it.

        Returns the number of tasks executed. The clock lands exactly on
        the horizon whether or not anything was scheduled there, so runs of
        equal length are comparable.
        """
        horizon = int(horizon)
        self._horizon = horizon
        while self._heap and self._heap[0].time <= horizon:
            task = heapq.heappop(self._heap)
            if task.cancelled:
                continue
            self.now = task.time
            self._ran += 1
            task.fn()
        self.now = horizon
        return self._ran

    def next_time(self):
        for t in self._heap:
            if not t.cancelled:
                return min(x.time for x in self._heap if not x.cancelled)
        return None

    def pending(self):
        return sum(1 for t in self._heap if not t.cancelled)

    def executed(self):
        return self._ran


def cancel(task):
    """
    Cancel without touching the heap.

    Removing from a heap is O(n) and would make behaviour depend on queue
    contents; marking is O(1) and leaves ordering untouched.
    """
    task.cancelled = True
