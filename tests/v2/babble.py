"""
A shared test harness: an adult among stones and a stick, acting at random.

Used by the skill and planning tests. It chooses acts at random -- motor
babbling -- performs them with the real primitives on the real physics,
lets the agent perceive each new thing by touch and learn its own kinds
(cognition.concepts), and feeds every act and its perceived result to the
agent's skill store. It keeps the scene going: a fresh flint core when none
is left, small pieces carried off before the next act.

`perform` binds a planned step to actual things of the named kinds -- the
scaffolding a motor system would provide. The observer-side helpers at the
end read ground truth, which the agent never does.

An earlier version of this loop filed things without learning from them, so
every kind stayed at its first member, and a flake, a core and a cobble all
fell into one kind; the skill test passed for that degenerate reason.
"""

from __future__ import annotations

from collections import Counter

import zimulation.behavior.params  # noqa: F401  (declares on import)
import zimulation.biology.params  # noqa: F401
import zimulation.cognition.params  # noqa: F401
import zimulation.world.params  # noqa: F401
from zimulation.behavior import primitives as PR
from zimulation.behavior import skills as SK
from zimulation.biology import genetics as G
from zimulation.biology import physiology as P
from zimulation.cognition import concepts as K
from zimulation.cognition import perception as PC
from zimulation.core.rng import Streams
from zimulation.core.scheduler import YEAR
from zimulation.world import objects as O
from zimulation.world.materials_data import MATERIALS
from zimulation.world.space import Terrain


class Babbler:
    """One agent, its scene, its kinds and its skill store."""

    def __init__(self, seed):
        terr = Terrain(6, Streams(1).get("t"))
        self.a = PR.Actor(1, P.Body(mass_kg=60.0, age_s=27.0 * YEAR),
                          G.founder(Streams(1).get("g")), terr.at(2, 2))
        self.see, self.rng, self.knap = (Streams(seed).get(n)
                                         for n in ("see", "babble", "k"))
        self.concepts = K.Concepts(1)
        self.labels = {}
        self.sk = SK.Skills(1)
        self.t = 0
        self.first = None
        self.lay("granite", 0.8, 0.12)
        self.lay("hardwood", 0.4, 0.6)
        self.sk.begin(self.state())

    # ------------------------------------------------------------- scene
    def lay(self, name, mass, length):
        self.a.cell.things.append(O.Thing(None, MATERIALS[name], mass, length,
                                          position=self.a.here))

    def restock(self):
        """A fresh core when none is left; small pieces carried off."""
        a, changed = self.a, False
        if not any(th.material.name == "flint" and th.mass_kg >= 0.3
                   for th in a.held + a.cell.things):
            self.lay("flint", 0.6, 0.12)
            changed = True
        for th in [th for th in a.cell.things
                   if th.material.name == "flint" and th.mass_kg < 0.3]:
            a.cell.things.remove(th)
            changed = True
        if changed:
            self.sk.begin(self.state())
        return changed

    def fresh(self):
        """Hands emptied, pieces gone, a core present; working memory clear."""
        for th in list(self.a.held):
            PR.release(self.a, th)
        self.restock()
        self.sk.begin(self.state())

    # ------------------------------------------------------------ the agent
    def kind(self, th):
        if id(th) not in self.labels:
            f = PC.sense_thing(th, self.a.cell, self.a.cell, None, self.t,
                               1.0, 0.0, self.see, touching=True).features
            self.labels[id(th)] = (th, self.concepts.learn(f, {}, self.t).id)
        return self.labels[id(th)][1]

    def state(self):
        st = Counter()
        for th in self.a.held:
            st[("held", self.kind(th))] += 1
        for th in self.a.cell.things:
            st[("near", self.kind(th))] += 1
        return st

    def do(self, act, things):
        """Perform one primitive on these things and let the agent record
        it. Returns the Act."""
        roles = [self.kind(th) for th in things]
        a = self.a
        if act == "grasp":
            done = PR.grasp(a, things[0])
        elif act == "release":
            done = PR.release(a, things[0])
        else:
            done = PR.strike(a, things[0], things[1], self.knap)
        if done.done:
            self.sk.record(SK.Step(act, roles), self.state(), self.t,
                           trace_id=self.t)
        return done

    def random_act(self):
        a = self.a
        choice = self.rng.choice(("grasp", "release", "strike"))
        if choice == "grasp" and a.cell.things:
            self.do("grasp", [self.rng.choice(a.cell.things)])
        elif choice == "release" and a.held:
            self.do("release", [self.rng.choice(a.held)])
        elif choice == "strike" and a.held:
            x = self.rng.choice(a.held)
            others = [o for o in a.held + a.cell.things if o is not x]
            if others:
                self.do("strike", [x, self.rng.choice(others)])

    def babble(self, acts):
        for _ in range(acts):
            self.t += 1
            self.restock()
            self.random_act()
            if self.first is None and self.knapping():
                self.first = self.t
        return self

    def perform(self, key):
        """
        Carry out a planned step -- a primitive on kinds, or a stored skill
        -- by finding things of those kinds where the act needs them.
        Returns False if nothing suitable is at hand or the act fails.
        """
        act, roles = key
        skill = self.sk._by_id.get(act)
        if skill is not None:
            return all(self.perform(k) for k in skill.steps)
        a = self.a

        def find(kind, places, exclude=None):
            for th in places:
                if th is not exclude and self.kind(th) == kind:
                    return th
            return None

        if act == "grasp":
            things = [find(roles[0], a.cell.things)]
        elif act == "release":
            things = [find(roles[0], a.held)]
        else:
            x = find(roles[0], a.held)
            things = [x, find(roles[1], a.held + a.cell.things, exclude=x)]
        if any(th is None for th in things):
            return False
        self.t += 1
        return self.do(act, things).done

    # ------------------------------------------------------------ observer
    def piece_kinds(self):
        """The agent's own kinds that, as only the observer can see, consist
        mostly of pieces broken off flint, sharp ones among them."""
        members = {}
        for th, lab in self.labels.values():
            if th.mass_kg > 0.0:
                members.setdefault(lab, []).append(th)
        out = set()
        for lab, things in members.items():
            pieces = [th for th in things
                      if th.material.name == "flint" and th.mass_kg < 0.3]
            if (2 * len(pieces) > len(things)
                    and any(th.cutting_power > 0.2 for th in pieces)):
                out.add(lab)
        return out

    def knapping(self):
        """Stored procedures that include a blow and reliably make things of
        such a kind appear."""
        sharp = {("near", k) for k in self.piece_kinds()}
        return [s for s in self.sk.items
                if any(act == "strike" for act, _ in s.steps)
                and any(c.effect[0] & sharp for c in self.sk.effects(s))]
