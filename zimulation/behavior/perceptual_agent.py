"""
Perceptually grounded open-ended agent.

The earlier integration remembered a Python object's identity forever after
one encounter.  That is useful software bookkeeping and bad cognition: it
gives the mind a perfect pointer through changes in appearance, movement,
damage and time.  This agent deliberately does not use object identity for
categorisation.  Every encounter is classified again from what the body can
currently sense.

Nearby things are classified visually.  Held things are classified through
handling, because grasping supplies persistent tactile access.  An explicit
touch also contributes its tactile percept.  Thus a lump may first belong to
a coarse visual category and later be reclassified when hardness, edge or
wetness becomes available.  Category continuity is learned, not guaranteed
by the host language.

This is still not a full object-file model.  It is the stricter baseline:
there is no persistent individual-object identity in cognition at all.  A
later identity tracker may infer continuity from spatiotemporal and feature
evidence, but it must remain uncertain and must never key on ``id(thing)``
or on a ground-truth object id.
"""

from __future__ import annotations

from ..biology.development import sensory_acuity
from ..cognition import perception as PC
from ..core.parameters import REGISTRY as R
from .open_agent import Agent as _OpenAgent


class Agent(_OpenAgent):
    """Open-ended agent whose categories are rebuilt from current percepts."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._terrain = None

    def turn(self, terrain, time):
        # Terrain is retained only so that a same-cell visual percept can go
        # through the ordinary visibility path.  No global query is made.
        self._terrain = terrain
        return super().turn(terrain, time)

    def _percept(self, thing, time, touching):
        a = self.actor
        return PC.sense_thing(
            thing, a.cell, a.cell, self._terrain, time,
            sensory_acuity(a.body.age_years), a.body.impairment,
            self.see, touching=touching)

    def _learn_kind(self, percept, thing, time):
        c = self.concepts.learn(percept.features, {}, time, trace_id=time)

        # ``labels`` is observer-facing audit material retained only for the
        # existing validation helpers.  Cognition never reads it in this
        # class.  Keep a bounded sample instead of a permanent object table.
        key = len(self.labels)
        self.labels[key] = (thing, c.id)
        cap = int(R.get("concept_example_cap")) * max(1, len(self.concepts.items))
        while len(self.labels) > cap:
            self.labels.pop(next(iter(self.labels)))
        return c.id

    def kind(self, thing, time):
        """Classify from current sensation; never from host-object identity."""
        touching = thing in self.actor.held
        p = self._percept(thing, time, touching)
        if p is None:
            # A thing supplied here is physically in reach.  Failing to see
            # it must not grant hidden knowledge; use only an undifferentiated
            # presence cue until another sense supplies more.
            p = PC.Percept(time, PC.TOUCH, None, {"presence": 1.0},
                           self.actor.here)
        return self._learn_kind(p, thing, time)

    def _act(self, act, targets, terrain, time):
        done = super()._act(act, targets, terrain, time)
        if act == "touch" and done.done:
            p = done.outcome.get("percept")
            if p is not None:
                self._learn_kind(p, targets[0], time)
        return done
