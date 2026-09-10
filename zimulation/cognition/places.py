"""
Places: where this agent has perceived things of each of its kinds.

The agent does not know the map. It knows where it has seen or felt things,
when, and how many -- and it forgets, at the pace of episodic memory. Asked
where to find something of a kind, it answers from that memory, which may
be stale (the patch was dug out since it was last seen) or wrong (what it
saw it misfiled). A place last seen empty of a kind is not offered for that
kind until it is seen full again.

This is the what-where-when of episodic memory (Tulving 1972; Clayton &
Dickinson 1998) in its barest form, and the only map an agent has.
"""

from __future__ import annotations

import math

from ..core.parameters import REGISTRY as R
from ..core.scheduler import DAY


class Places:
    """One agent's memory of where each of its kinds was found."""

    __slots__ = ("owner", "seen")

    def __init__(self, owner):
        self.owner = owner
        self.seen = {}

    def note(self, kind, xy, count, time):
        """At time, `count` things of `kind` were perceived at place xy
        (zero means it was seen empty of them)."""
        self.seen.setdefault(kind, {})[xy] = (count, time)

    def strength(self, time_seen, now):
        half = R.get("memory_half_life_days") * DAY
        return 0.5 ** (max(0.0, now - time_seen) / half)

    def where(self, kind, here, now):
        """Places remembered to hold things of `kind`, nearest first; ties
        go to the more recently seen."""
        floor = R.get("forget_threshold")
        found = []
        for xy, (count, t) in self.seen.get(kind, {}).items():
            if count <= 0 or self.strength(t, now) < floor:
                continue
            d = math.hypot(xy[0] - here[0], xy[1] - here[1])
            found.append((d, -t, xy))
        found.sort()
        return [xy for _, _, xy in found]

    def forget(self, now):
        """Drop places faded past recall. Returns how many were dropped."""
        floor = R.get("forget_threshold")
        gone = 0
        for kind in list(self.seen):
            spots = self.seen[kind]
            for xy in [xy for xy, (_, t) in spots.items()
                       if self.strength(t, now) < floor]:
                del spots[xy]
                gone += 1
            if not spots:
                del self.seen[kind]
        return gone
