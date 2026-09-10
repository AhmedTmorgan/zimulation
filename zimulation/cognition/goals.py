"""
Goals: what the body wants, and what the agent has learned relieves it.

Contract section 13: primitive motivational systems -- hunger, thirst,
temperature regulation, pain avoidance, rest, curiosity -- and nothing like
a good drive, an evil drive, a religious drive or a war drive. The drives
here are read off the signals the body produces (perception.sense_body).
The agent does not know it needs water; it feels thirst.

What relieves a drive is not given either. The agent learns it from what
followed its own acts: after bouts of consuming something of its kind 4 the
thirst it felt fell; after chewing something of kind 2, it did not. This is
instrumental learning of act and outcome, conditional on the kind of thing
acted on (Dickinson & Balleine 1994).

## Urgency

Each bodily drive is as urgent as the signal behind it. Curiosity is the
exception: it has no bodily signal and stands at a declared baseline -- a
pull toward the unknown that wins only when nothing else presses (Berlyne
1960; Oudeyer & Kaplan 2007 on intrinsic motivation).

## Learning what helps

For every act on every kind of thing, the agent keeps how each bodily
signal changed over a bout of that act. A remedy for a drive is an act on a
kind whose mean change in the drive's signal stays below zero by a declared
number of standard errors, after a declared least number of bouts. One
lucky coincidence is not taken for a cure, and a cure tried once is not yet
trusted. Across many acts and kinds the rule still admits occasional false
remedies -- the test measures how often -- and those are left for the agent
to discover wrong, or not.

## Provenance

Each record keeps the bouts it rests on. Nothing here is told what any
kind is or what any act is for.
"""

from __future__ import annotations

import math

from ..core.parameters import REGISTRY as R

#: Each bodily drive and the interoceptive signal it reads.
SIGNALS = {"hunger": "hunger", "thirst": "thirst", "cold": "cold",
           "heat": "heat", "pain": "pain", "rest": "sleepiness"}
#: The one drive with no bodily signal.
CURIOSITY = "curiosity"


class Relief:
    """What bouts of one act on one kind of thing did to each signal."""

    __slots__ = ("act", "kind", "stats", "examples")

    def __init__(self, act, kind):
        self.act = act
        self.kind = kind
        self.stats = {}
        self.examples = []

    def change(self, signal):
        """(mean change, standard error, bouts), or None until two bouts."""
        n, mean, m2 = self.stats.get(signal, (0, 0.0, 0.0))
        if n < 2:
            return None
        return mean, math.sqrt(m2 / (n - 1) / n), n


class Goals:
    """One agent's drives, and what it has learned relieves them."""

    __slots__ = ("owner", "reliefs")

    def __init__(self, owner):
        self.owner = owner
        self.reliefs = {}

    # ------------------------------------------------------------ urgency
    def urgencies(self, signals):
        """How pressing each drive is, given what the body reports."""
        out = {drive: max(0.0, min(1.0, signals.get(sig, 0.0)))
               for drive, sig in SIGNALS.items()}
        out[CURIOSITY] = R.get("curiosity_baseline")
        return out

    def most_urgent(self, signals):
        u = self.urgencies(signals)
        drive = max(sorted(u), key=u.__getitem__)
        return drive, u[drive]

    # ----------------------------------------------------------- learning
    def record_bout(self, act, kind, before, after, trace_id=None):
        """
        One bout of an act on a thing of a kind: the bodily signals felt
        before it began and after it ended.
        """
        key = (act, kind)
        r = self.reliefs.get(key)
        if r is None:
            r = self.reliefs[key] = Relief(act, kind)
        for sig in sorted(set(before) & set(after)):
            n, mean, m2 = r.stats.get(sig, (0, 0.0, 0.0))
            d = after[sig] - before[sig]
            n += 1
            delta = d - mean
            mean += delta / n
            r.stats[sig] = (n, mean, m2 + delta * (d - mean))
        r.examples.append(trace_id)
        del r.examples[:-int(R.get("relief_example_cap"))]
        return r

    def remedies(self, drive):
        """
        Acts on kinds that have reliably lowered this drive's signal, the
        most relieving first: (act, kind, mean change, upper bound).
        """
        sig = SIGNALS.get(drive)
        if sig is None:
            return []
        z = R.get("relief_confidence_z")
        need = R.get("relief_min_bouts")
        out = []
        for (act, kind), r in self.reliefs.items():
            ch = r.change(sig)
            if ch is None:
                continue
            mean, se, n = ch
            if n >= need and mean + z * se < 0.0:
                out.append((act, kind, mean, mean + z * se))
        out.sort(key=lambda x: (x[2], repr(x[0]), repr(x[1])))
        return out
