"""
Belief.

Contract section 17 separates five things that are easy to run together:
the world, what was perceived, what is remembered, what is believed, and
how confident the believer is. This module is the last two.

A belief is an estimate with a precision. Confidence is derived from
precision, never set directly, and it is bounded below certainty so that
no evidence is ever strictly unrevisable. An agent can therefore hold, as
a matter of structure rather than vocabulary, "I think it is about this,
and I am not sure" -- which section 17 requires without handing anyone
the words.

## Updating

Evidence moves an estimate by a precision-weighted average, and how much
weight a datum carries depends on where it came from. Seeing counts in
full. Being told counts for `testimony_trust`, a hypothesis parameter the
experiment varies rather than assumes. Inference, imitation, records and
reconstructed recollections each have their own weight.

Surprise matters in the other direction. A datum far from what a belief
expects cuts its precision, so contradiction lowers confidence instead of
being averaged away.

## What emerges without being written

**Persistence.** A belief built on much evidence moves little for one
contradicting datum. That is belief perseverance (Ross, Lepper & Hubbard
1975) arising from arithmetic: nothing marks any belief as stubborn.

**Error propagation.** A false thing heard from a trusted source moves a
belief almost as much as a true thing seen, because belief does not know
which is which. Only the observer does.

Every update is recorded in `provenance`: source, the trace it came from,
its weight and when. Section 6 asks that any belief be traceable to what
produced it; this is where that is kept.
"""

from __future__ import annotations

from ..core.parameters import REGISTRY as R
from .memory import (IMITATED, INFERRED, OBSERVED, RECONSTRUCTED, RECORD,
                     TOLD)


def source_weight(source):
    """How much a datum from this kind of source counts."""
    if source == OBSERVED:
        return 1.0
    return R.get({
        INFERRED: "inference_weight",
        TOLD: "testimony_trust",
        RECONSTRUCTED: "reconstruction_weight",
        IMITATED: "imitation_weight",
        RECORD: "record_weight",
    }[source])


class Belief:
    """An estimate of something, with a precision and a history."""

    __slots__ = ("key", "estimate", "precision", "provenance", "formed",
                 "revised")

    def __init__(self, key, estimate, formed):
        self.key = key
        self.estimate = estimate
        self.precision = R.get("belief_prior_precision")
        self.provenance = []
        self.formed = formed
        self.revised = formed

    @property
    def confidence(self):
        """Derived from precision; bounded below certainty."""
        return min(R.get("confidence_ceiling"),
                   self.precision / (self.precision + 1.0))

    def expected_spread(self):
        return 1.0 / max(R.get("division_epsilon"), self.precision) ** 0.5

    def __repr__(self):
        return (f"<Belief {self.key} ~{self.estimate:.3f} "
                f"conf={self.confidence:.2f}>")


def update(belief, value, source, time, trace_id=None, reliability=1.0):
    """
    Revise a belief in light of one datum. Returns how far it moved.

    `reliability` is the evidence's own quality -- a glimpse in fading
    light counts less than a long look -- and multiplies the source weight.
    """
    w = source_weight(source) * max(0.0, reliability)
    if w <= 0.0:
        return 0.0

    gap = abs(value - belief.estimate)
    surprise = min(1.0, gap / (R.get("surprise_scale_sd")
                               * belief.expected_spread()))
    # Contradiction costs confidence before the new estimate is formed.
    belief.precision *= 1.0 - R.get("surprise_discount") * surprise

    before = belief.estimate
    belief.estimate = ((belief.precision * belief.estimate + w * value)
                       / (belief.precision + w))
    belief.precision += w
    belief.revised = time

    belief.provenance.append((source, trace_id, w, time))
    cap = int(R.get("belief_provenance_cap"))
    if len(belief.provenance) > cap:
        del belief.provenance[:len(belief.provenance) - cap]
    return abs(belief.estimate - before)


class Beliefs:
    """One agent's beliefs, keyed by whatever the agent's own categories
    are. The keys are built by the agent's concepts, not supplied by us."""

    __slots__ = ("_by_key",)

    def __init__(self):
        self._by_key = {}

    def get(self, key):
        return self._by_key.get(key)

    def observe(self, key, value, source, time, trace_id=None,
                reliability=1.0):
        """Form a belief if none exists, otherwise revise it."""
        b = self._by_key.get(key)
        if b is None:
            b = Belief(key, value, time)
            self._by_key[key] = b
            b.provenance.append((source, trace_id,
                                 source_weight(source) * reliability, time))
            return b, 0.0
        return b, update(b, value, source, time, trace_id, reliability)

    def __len__(self):
        return len(self._by_key)

    def all(self):
        return list(self._by_key.values())
