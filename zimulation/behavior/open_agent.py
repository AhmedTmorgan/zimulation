"""
Open-ended agent integration.

The existing arbitration machinery already provides drives, learned
remedies, planning, categories and skill chunking. This module extends it
only where the physical repertoire had outrun the actions the agent could
actually explore. It deliberately reuses the existing Agent rather than
rebuilding cognition.

Rubbing, separating and combining are offered as blind sensorimotor
experiments. Their success is still decided exclusively by world physics.
The agent receives no hint that rubbing can produce heat, that a sharp edge
can separate matter, or that a flexible strand can hold two objects.
"""

from __future__ import annotations

from ..core.parameters import REGISTRY as R
from ..world import contact as CT
from . import affordances as AF
from . import primitives as PR
from . import skills as SK
from .arbitration import Agent as _Agent


_DISCOVERY_ACTS = frozenset(("rub", "separate", "combine"))


class Agent(_Agent):
    """The V2 agent with the full presently-supported discovery repertoire."""

    def _act(self, act, targets, terrain, time):
        if act not in _DISCOVERY_ACTS:
            return super()._act(act, targets, terrain, time)

        a = self.actor
        if act == "rub":
            if not CT.rubbing_contact_exists(targets[0], targets[1]):
                return PR.Act("rub", 0, 0.0, {"refused": "no contact area"})
            done = PR.rub(a, targets[0], targets[1], R.get("turn_min_s"),
                          self.knap, now=time)
        elif act == "separate":
            done = PR.separate(a, targets[0], targets[1], self.knap)
        else:
            done = PR.combine(a, targets[0], targets[1])

        if not done.done:
            return done
        self.acts += 1
        roles = [self.kind(t, time) for t in targets]
        for sk in self.skills.record(SK.Step(act, roles), self.state(time),
                                     time, trace_id=time):
            self.news.append(("skill", sk.id))
        return done

    def _perform(self, key, terrain, time):
        """Reproduce learned two-object discovery acts as well as old acts."""
        act, roles = key
        if act not in _DISCOVERY_ACTS:
            return super()._perform(key, terrain, time)

        def find(kind, places, skip=None):
            for th in places:
                if th is not skip and self.kind(th, time) == kind:
                    return th
            return None

        if len(roles) != 2:
            return None
        if act in ("rub", "separate"):
            first = find(roles[0], self.actor.held)
        else:
            first = find(roles[0], self.reach())
        second = find(roles[1], self.reach(), skip=first)
        if first is None or second is None:
            return None
        done = self._act(act, [first, second], terrain, time)
        return done if done.done else None

    def _pursue(self, drive, signals, terrain, time):
        """
        Until multi-object remedy planning exists, do not mis-handle a
        two-object act as if it had one target. Such acts remain available
        through exploration and learned procedures.
        """
        hidden = []
        for key in list(self.goals.reliefs):
            if key[0] in _DISCOVERY_ACTS:
                hidden.append((key, self.goals.reliefs.pop(key)))
        try:
            return super()._pursue(drive, signals, terrain, time)
        finally:
            for key, value in hidden:
                self.goals.reliefs[key] = value

    def _explore(self, signals, terrain, time, drive=None):
        """Choose blindly among the physical affordances present here."""
        offered = AF.available(self.actor, terrain)
        # The primitive layer is deliberately broader than this integration
        # stage. Throwing and dragging are already real physics, but their
        # destination-bearing roles need a spatial skill representation
        # before they should enter learned action sequences.
        allowed = {
            name: targets for name, targets in offered.items()
            if name in {"move", "rest", "grasp", "release", "consume",
                        "touch", "strike", "rub", "separate", "combine"}
        }

        bias = R.get("consummatory_bias")
        if (bias > 0.0 and "consume" in allowed
                and drive in ("hunger", "thirst")
                and self.choose.random() < bias):
            act = "consume"
        else:
            act = self.choose.choice(sorted(allowed))

        targets = list(self.choose.choice(allowed[act]))
        kind = None
        if targets and act != "move":
            kinds = tuple(self.kind(t, time) for t in targets)
            kind = kinds[0] if len(kinds) == 1 else kinds
        return self._start(act, kind, targets, signals,
                           int(R.get("explore_bout_acts")), None, False,
                           terrain, time)
