"""
The ground-truth barrier.

In Zimulation 1 the barrier was a convention: memory traces carried a
`truth` field, and a test checked that no decision path read it. That
worked, but it was a promise enforced by grep. It caught one real leak
(`speech._vision` reading `strongest_false`), which is exactly why it
should not have been a promise.

Here the barrier is structural. Ground truth lives behind an accessor that
knows who is asking. Causal code -- anything that can change what an agent
does -- cannot get an answer at all. The observer can, and every access is
recorded, so a reviewer can see precisely what the analysis looked at.

The rule, stated once:

    The observer may know the true state of the universe.
    Agents may not.
    Nothing an agent does may depend, however indirectly, on a fact no
    agent could have obtained through perception, inference, testimony,
    or a physical record.

This module cannot make that true by itself. It makes violations loud.
"""

from __future__ import annotations

import threading

#: Import paths that are permitted to read ground truth. Everything under
#: the observer package analyses history after the fact and never feeds
#: back into it; experiment drivers set worlds up before agents exist.
_OBSERVER_PREFIXES = ("zimulation.observer.", "experiments.", "tests.")


class TruthLeak(Exception):
    """Raised when causal code tries to read a ground-truth field."""


class _Context(threading.local):
    def __init__(self):
        self.causal_depth = 0
        self.reads = []


_CTX = _Context()


class causal:
    """
    Marks a region of execution as causal: inside it, ground truth is
    unreadable.

    Every agent decision, perception update and world tick runs inside one
    of these. The engine opens it once per step; nothing below needs to
    know about it.

        with causal():
            agent.decide(...)      # any GroundTruth read in here raises
    """

    def __enter__(self):
        _CTX.causal_depth += 1
        return self

    def __exit__(self, *exc):
        _CTX.causal_depth -= 1
        return False


def in_causal_context():
    return _CTX.causal_depth > 0


class GroundTruth:
    """
    A value only the observer may see.

    Wrap any field whose knowledge an agent has not earned: the real cause
    of an event, the real efficacy of a plant, whether a memory matches
    what happened, the true population, the mechanism behind the weather.

        real_cause = GroundTruth("ignition_source", "lightning")
        real_cause.value            # raises inside causal code
        real_cause.reveal("emergence.fire_stages")  # observer, recorded
    """

    __slots__ = ("_name", "_value")

    def __init__(self, name, value):
        self._name = name
        self._value = value

    @property
    def value(self):
        if in_causal_context():
            raise TruthLeak(
                f"causal code read ground truth {self._name!r}. Agents may "
                f"only know what they perceived, were told, inferred, or "
                f"read from a physical record.")
        _CTX.reads.append((self._name, None))
        return self._value

    def reveal(self, reader):
        """
        Observer read, attributed. `reader` names the analysis asking, so
        the audit shows which detector saw which truth.
        """
        if in_causal_context():
            raise TruthLeak(
                f"{reader}: cannot reveal ground truth {self._name!r} from "
                f"inside causal code")
        if not any(reader.startswith(p) or reader.startswith(p.rstrip("."))
                   for p in _OBSERVER_PREFIXES):
            raise TruthLeak(
                f"{reader!r} is not an observer module; ground truth "
                f"{self._name!r} refused")
        _CTX.reads.append((self._name, reader))
        return self._value

    def __repr__(self):
        return f"<GroundTruth {self._name!r} (hidden)>"

    # Deliberately unhelpful: no __str__, __eq__, __bool__, __iter__.
    # A ground-truth value must not leak through formatting or comparison.
    def __eq__(self, other):
        raise TruthLeak(
            f"comparing ground truth {self._name!r} would leak it; "
            f"use .reveal() from an observer module")

    __hash__ = None

    def __bool__(self):
        raise TruthLeak(
            f"testing truthiness of ground truth {self._name!r} would leak it")


def audit():
    """Every ground-truth access so far, in order: (field, reader)."""
    return list(_CTX.reads)


def clear_audit():
    _CTX.reads.clear()
