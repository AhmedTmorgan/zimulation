"""
Deterministic randomness.

The contract requires that

    version + scenario + parameters + seed  ->  identical event ledger

byte for byte. That is easy to state and easy to lose. It is lost the
moment two parts of the model draw from one shared generator, because then
adding a single draw anywhere shifts every subsequent draw everywhere, and
a change to a detector or a report can silently rewrite history.

So there is no global generator here. Randomness is drawn from *named
streams*, derived from the seed by hashing. Streams are independent: a new
draw in `combustion` cannot move `metabolism`, and code added tomorrow
cannot perturb a run recorded today as long as it uses its own stream.

Streams can be split per entity, so agent 41's decisions come from a
stream that nothing else touches. This is what makes counterfactual replay
possible: rerun from a snapshot with one mechanism changed, and every
untouched stream produces exactly what it produced before, so the
difference in outcome is attributable to the intervention and nothing
else.

Derivation is SHA-256 over UTF-8, not Python's `hash()`, which is salted
per process and would make runs irreproducible across invocations.
"""

from __future__ import annotations

import hashlib
import random
import struct


def derive_seed(root_seed, *parts):
    """
    A stable 64-bit seed for (root_seed, *parts).

    Deterministic across processes, platforms and Python versions: the
    inputs are rendered as text and hashed, so nothing depends on memory
    layout or hash randomisation.
    """
    blob = "\x1f".join([str(root_seed)] + [str(p) for p in parts])
    digest = hashlib.sha256(blob.encode("utf-8")).digest()
    return struct.unpack("<Q", digest[:8])[0]


class Stream:
    """
    One named source of randomness.

    Wraps `random.Random`, whose Mersenne Twister is specified exactly and
    reproduces across platforms. Draw counts are tracked so a run can be
    audited: a stream that suddenly draws twice as often has changed
    behaviour even if its outputs still look plausible.
    """

    __slots__ = ("name", "seed", "_r", "draws")

    def __init__(self, name, seed):
        self.name = name
        self.seed = seed
        self._r = random.Random(seed)
        self.draws = 0

    def random(self):
        self.draws += 1
        return self._r.random()

    def uniform(self, a, b):
        self.draws += 1
        return self._r.uniform(a, b)

    def gauss(self, mu, sigma):
        self.draws += 1
        return self._r.gauss(mu, sigma)

    def expovariate(self, lambd):
        """Waiting time until the next event of a Poisson process."""
        self.draws += 1
        return self._r.expovariate(lambd)

    def randrange(self, n):
        self.draws += 1
        return self._r.randrange(n)

    def choice(self, seq):
        self.draws += 1
        return self._r.choice(seq)

    def sample(self, population, k):
        self.draws += 1
        return self._r.sample(population, k)

    def shuffle(self, seq):
        self.draws += 1
        self._r.shuffle(seq)

    def state(self):
        return self._r.getstate()

    def restore(self, state):
        self._r.setstate(state)

    def __repr__(self):
        return f"<Stream {self.name!r} draws={self.draws}>"


class Streams:
    """
    The set of named streams for one run.

    Ask for a stream by name; it is created on first use and is thereafter
    stable. Names should describe the mechanism, not the caller, so that
    moving code between modules does not change history.
    """

    __slots__ = ("root", "_streams")

    def __init__(self, root_seed):
        self.root = root_seed
        self._streams = {}

    def get(self, name):
        s = self._streams.get(name)
        if s is None:
            s = Stream(name, derive_seed(self.root, name))
            self._streams[name] = s
        return s

    def entity(self, name, entity_id):
        """
        A stream private to one entity. Agent 41's stream is unaffected by
        how many other agents exist or in what order they were created.
        """
        key = f"{name}#{entity_id}"
        s = self._streams.get(key)
        if s is None:
            s = Stream(key, derive_seed(self.root, name, entity_id))
            self._streams[key] = s
        return s

    def names(self):
        return sorted(self._streams)

    def draw_counts(self):
        """Audit: how often each stream was used."""
        return {k: v.draws for k, v in sorted(self._streams.items())}

    def snapshot(self):
        return {k: (v.seed, v.draws, v.state()) for k, v in self._streams.items()}

    def restore(self, snap):
        self._streams = {}
        for k, (seed, draws, state) in snap.items():
            s = Stream(k, seed)
            s.restore(state)
            s.draws = draws
            self._streams[k] = s
