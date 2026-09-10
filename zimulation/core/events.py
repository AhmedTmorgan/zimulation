"""
The event ledger.

Everything that happens is an event, and the ledger is the only record of
what a run did. Reports are derived from it; detectors read it; nothing
writes history except by appending here.

Two properties matter more than convenience:

**It is append-only and hash-chained.** Each event carries the hash of the
one before it, so the ledger cannot be edited after the fact without the
chain breaking. Determinism is then checkable by comparing one number: two
runs with the same seed must end with the same head hash.

**It records what was perceived, not only what occurred.** An event stores
the true physical consequence *and* the list of agents who could perceive
it, separately. That separation is the whole reason cultural history can
diverge from ground truth later: an event with no perceivers happened and
nobody knows it.

Fields follow the contract, section 53. `causal_parents` is what makes
provenance traceable: any belief, artifact or claim can be walked back
through the events that produced it.
"""

from __future__ import annotations

import hashlib
import json

#: Ledger schema version. A change here invalidates comparison with runs
#: recorded under an older schema, so it is part of the reproducibility
#: metadata every result carries.
SCHEMA_VERSION = 1

GENESIS = "0" * 16


class Event:
    """
    One thing that happened.

    `physical` holds what the world did -- true regardless of who saw it.
    `perceived_by` holds who could have known. Nothing else may connect
    the two: an agent's knowledge of an event must arrive through
    perception, testimony, inference or a physical record, never by
    reading this object.
    """

    __slots__ = ("event_id", "time", "kind", "location", "participants",
                 "objects", "primitives", "physical", "perceived_by",
                 "causal_parents", "stream", "pre_hash", "post_hash")

    def __init__(self, event_id, time, kind, location=None, participants=(),
                 objects=(), primitives=(), physical=None, perceived_by=(),
                 causal_parents=(), stream=""):
        self.event_id = event_id
        self.time = time
        self.kind = kind
        self.location = location
        self.participants = tuple(participants)
        self.objects = tuple(objects)
        self.primitives = tuple(primitives)
        self.physical = physical or {}
        self.perceived_by = tuple(perceived_by)
        self.causal_parents = tuple(causal_parents)
        self.stream = stream
        self.pre_hash = GENESIS
        self.post_hash = GENESIS

    def content(self):
        """The part of the event that determines its hash."""
        return {
            "id": self.event_id,
            "t": round(float(self.time), 9),
            "kind": self.kind,
            "loc": self.location,
            "who": list(self.participants),
            "obj": list(self.objects),
            "prim": list(self.primitives),
            "phys": _canon(self.physical),
            "saw": list(self.perceived_by),
            "from": list(self.causal_parents),
            "stream": self.stream,
        }

    def compute_hash(self, previous):
        blob = json.dumps({"prev": previous, "e": self.content()},
                          sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    def as_dict(self):
        d = self.content()
        d["pre_hash"] = self.pre_hash
        d["post_hash"] = self.post_hash
        return d

    def __repr__(self):
        return (f"<Event {self.event_id} t={self.time:.3f} {self.kind} "
                f"who={self.participants}>")


def _canon(obj):
    """Round floats so that irrelevant precision cannot break a hash."""
    if isinstance(obj, float):
        return round(obj, 9)
    if isinstance(obj, dict):
        return {k: _canon(v) for k, v in sorted(obj.items())}
    if isinstance(obj, (list, tuple)):
        return [_canon(v) for v in obj]
    return obj


class Ledger:
    """
    Append-only, hash-chained record of a run.

    `head` is the fingerprint of the entire history. Determinism tests
    compare heads; a mismatch localises to the first differing event.
    """

    __slots__ = ("events", "head", "_next_id", "_by_kind")

    def __init__(self):
        self.events = []
        self.head = GENESIS
        self._next_id = 1
        self._by_kind = {}

    def append(self, time, kind, **fields):
        e = Event(self._next_id, time, kind, **fields)
        self._next_id += 1
        e.pre_hash = self.head
        e.post_hash = e.compute_hash(self.head)
        self.head = e.post_hash
        self.events.append(e)
        self._by_kind.setdefault(kind, []).append(e)
        return e

    def of_kind(self, kind):
        return list(self._by_kind.get(kind, ()))

    def kinds(self):
        return {k: len(v) for k, v in sorted(self._by_kind.items())}

    def since(self, time):
        return [e for e in self.events if e.time >= time]

    def verify(self):
        """
        Recompute the chain. Returns the id of the first tampered event,
        or None if the ledger is intact.
        """
        prev = GENESIS
        for e in self.events:
            if e.pre_hash != prev:
                return e.event_id
            if e.compute_hash(prev) != e.post_hash:
                return e.event_id
            prev = e.post_hash
        return None

    def trace(self, event_id, depth=64):
        """
        Walk an event back through its causal parents.

        This is provenance made concrete: given a belief, an artifact or a
        historical claim, recover the chain of events that produced it.
        """
        index = {e.event_id: e for e in self.events}
        out, frontier, seen = [], [event_id], set()
        while frontier and len(out) < depth:
            eid = frontier.pop(0)
            if eid in seen or eid not in index:
                continue
            seen.add(eid)
            e = index[eid]
            out.append(e)
            frontier.extend(e.causal_parents)
        return out

    def __len__(self):
        return len(self.events)
