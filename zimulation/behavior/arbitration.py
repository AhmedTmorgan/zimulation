"""
Arbitration: what an agent does next, and why.

Each turn the agent feels its body, takes in what is within reach, and
settles on one act. The order in which it considers things is the whole of
its will at this stage, and each step is a condition, not a conclusion:

1. Sleep comes when sleepiness is the most urgent drive. This is the body's
   own regulation of sleep (Borbely 1982), not a choice it has learned.
2. A bout already under way goes on: an exploratory bout until it has run
   its course or the act fails, a bout of a remedy while the drive behind
   it still leads.
3. If the agent has learned a remedy for its most urgent drive
   (cognition.goals) and a thing of that kind is within reach, it does the
   act. If none is within reach, it plans with its own experience to make
   one appear (cognition.planning over behavior.skills), and failing that
   walks toward the nearest place it remembers finding one
   (cognition.places).
4. Otherwise it explores: an act chosen at random among those its body
   can do to what is within reach, or a step to a neighbouring place. A
   newly tried act is repeated a few times unless it fails, as infants
   repeat actions (the circular reactions of Piaget 1952). Nothing biases
   exploration toward eating when hungry or drinking when thirsty; any such
   prior would have to be declared and tested.

Which remedy to use, and whether to use one at all rather than explore, is
decided by sampling each known remedy's relief from what is known of it and
setting it against an act not yet tried (Thompson 1933); people explore
both at random and toward uncertainty (Wilson et al. 2014). The first
version always used its best-known remedy and so never tried anything
else: with water taken for a hunger remedy, agents drank six thousand
times in five days and never ate, while the counterfactual agent, exploring
blindly, learned both what quiets thirst and what quiets hunger.

## Measured (eight lone adults beside water at 20 degrees, five days each)

With no innate prior, five of eight learners lived (three died of thirst).
Three learned that eating a kind of thing the observer knows to be tubers
quiets hunger, three that drinking from standing water quiets thirst, and
they held 2.5 false remedies each -- superstitions such as grasping bark
for thirst. Agents identical but never using what they learned lived six
of eight: over five days, using what was learned did not improve survival,
though learners kept more fat (7.6 kg against 6.5). With the declared
mouthing prior at 0.5 all lived, learners and counterfactuals alike, and
fewer learned what quiets thirst (one of eight): an agent that drinks often
is seldom thirsty, and learns nothing about thirst from drinking. What
keeps a lone, naive agent alive in this world is an innate consummatory
tendency, not learning. That is a result, and the lever is left for
experiments.

Everything the agent does passes through the primitives and the physics;
everything it learns comes from its own perception -- its kinds are the
categories it forms from what it touches. It does not read the world, not
even a thing's true mass: something is available if it is still within
reach. Setting `learning=False` gives the counterfactual agent, identical
except that it never uses what it has learned.
"""

from __future__ import annotations

from collections import Counter

from ..biology.development import sensory_acuity
from ..cognition import concepts as K
from ..cognition import goals as GO
from ..cognition import perception as PC
from ..cognition import places as PL
from ..cognition import planning as PN
from ..core.parameters import REGISTRY as R
from . import primitives as PR
from . import skills as SK


class Bout:
    """A run of one act on the same targets, and what the body felt when
    it began."""

    __slots__ = ("act", "kind", "targets", "before", "left", "drive",
                 "remedy")

    def __init__(self, act, kind, targets, before, left, drive, remedy):
        self.act = act
        self.kind = kind
        self.targets = targets
        self.before = before
        self.left = left
        self.drive = drive
        self.remedy = remedy


class Agent:
    """One organism: a body that acts, and a mind that learns from it."""

    __slots__ = ("id", "actor", "see", "sense", "choose", "knap", "concepts",
                 "skills", "goals", "places", "labels", "bout", "acts",
                 "learning", "news", "trusted")

    def __init__(self, agent_id, actor, streams, learning=True):
        self.id = agent_id
        self.actor = actor
        self.see = streams.entity("see", agent_id)
        self.sense = streams.entity("sense", agent_id)
        self.choose = streams.entity("choose", agent_id)
        self.knap = streams.entity("knap", agent_id)
        self.concepts = K.Concepts(agent_id)
        self.skills = SK.Skills(agent_id)
        self.goals = GO.Goals(agent_id)
        self.places = PL.Places(agent_id)
        self.labels = {}
        self.bout = None
        self.acts = 0
        self.learning = learning
        self.news = []
        self.trusted = set()

    # ------------------------------------------------------------ perceiving
    def kind(self, thing, time):
        """The agent's own kind for a thing, learned from touching it the
        first time; after that it remembers which thing it filed where."""
        entry = self.labels.get(id(thing))
        if entry is None or entry[0] is not thing:
            a = self.actor
            f = PC.sense_thing(thing, a.cell, a.cell, None, time,
                               sensory_acuity(a.body.age_years),
                               a.body.impairment, self.see,
                               touching=True).features
            entry = (thing, self.concepts.learn(f, {}, time).id)
            self.labels[id(thing)] = entry
        return entry[1]

    def reach(self):
        return list(self.actor.held) + list(self.actor.cell.things)

    def state(self, time):
        st = Counter()
        for th in self.actor.held:
            st[("held", self.kind(th, time))] += 1
        for th in self.actor.cell.things:
            st[("near", self.kind(th, time))] += 1
        return st

    def feel(self, time):
        return PC.sense_body(self.actor.body, time, self.sense).features

    def survey(self, time):
        """Note what is here, and that what was remembered here is gone."""
        here = self.actor.here
        counts = Counter(self.kind(th, time) for th in self.actor.cell.things)
        for kind, n in counts.items():
            self.places.note(kind, here, n, time)
        for kind, spots in list(self.places.seen.items()):
            if kind not in counts and spots.get(here, (0, 0))[0] > 0:
                self.places.note(kind, here, 0, time)

    # ---------------------------------------------------------------- acting
    def _act(self, act, targets, terrain, time):
        a = self.actor
        if act == "grasp":
            done = PR.grasp(a, targets[0])
        elif act == "release":
            done = PR.release(a, targets[0])
        elif act == "consume":
            done = PR.consume(a, targets[0])
        elif act == "touch":
            done = PR.touch(a, targets[0], self.see, time)
        elif act == "strike":
            done = PR.strike(a, targets[0], targets[1], self.knap)
        elif act == "move":
            done = PR.move(a, terrain, targets[0])
        else:
            done = PR.rest(a, R.get("turn_min_s"))
        if not done.done:
            return done
        self.acts += 1
        if act == "move":
            self.skills.begin(self.state(time))
        elif act != "rest":
            roles = [self.kind(t, time) for t in targets]
            for sk in self.skills.record(SK.Step(act, roles), self.state(time),
                                         time, trace_id=time):
                self.news.append(("skill", sk.id))
        return done

    def _perform(self, key, terrain, time):
        """Carry out a planned step on things of the named kinds, a stored
        skill step by step. Returns an Act covering it all, or None."""
        act, roles = key
        skill = self.skills._by_id.get(act)
        if skill is not None:
            spent = energy = 0.0
            for inner in skill.steps:
                done = self._perform(inner, terrain, time)
                if done is None:
                    return None
                spent += done.duration_s
                energy += done.energy_j
            return PR.Act(act, spent, energy, {"performed": True})
        a = self.actor

        def find(kind, places, skip=None):
            for th in places:
                if th is not skip and self.kind(th, time) == kind:
                    return th
            return None

        if act == "grasp":
            targets = [find(roles[0], a.cell.things)]
        elif act == "release":
            targets = [find(roles[0], a.held)]
        elif act == "strike":
            x = find(roles[0], a.held)
            targets = [x, find(roles[1], self.reach(), skip=x)]
        else:
            targets = [find(roles[0], self.reach())]
        if any(t is None for t in targets):
            return None
        done = self._act(act, targets, terrain, time)
        return done if done.done else None

    # ------------------------------------------------------------------ bouts
    def _close(self, signals, time):
        b, self.bout = self.bout, None
        if b is None or b.kind is None:
            return
        self.goals.record_bout(b.act, b.kind, b.before, signals,
                               trace_id=time)
        for drive in GO.SIGNALS:
            for act, kind, mean, _ in self.goals.remedies(drive):
                if (drive, act, kind) not in self.trusted:
                    self.trusted.add((drive, act, kind))
                    self.news.append(("remedy", drive, act, kind, mean))

    def _start(self, act, kind, targets, signals, left, drive, remedy,
               terrain, time):
        self.bout = Bout(act, kind, targets, signals, left, drive, remedy)
        done = self._act(act, targets, terrain, time)
        if not done.done:
            self.bout = None
        else:
            self.bout.left -= 1
        return done

    def _continue(self, terrain, time):
        b = self.bout
        if b.act == "move":
            here = self.actor.cell
            targets = [self.choose.choice(terrain.neighbours(here.x, here.y))]
        else:
            within = self.reach()
            if any(t not in within for t in b.targets):
                return None
            targets = b.targets
        done = self._act(b.act, targets, terrain, time)
        if not done.done:
            return None
        b.left -= 1
        return done

    # ---------------------------------------------------------------- choosing
    def _at_hand(self, kind, act, time):
        pool = (self.actor.cell.things if act == "grasp" else
                self.actor.held if act == "release" else self.reach())
        for th in pool:
            if self.kind(th, time) == kind:
                return th
        return None

    def _weigh(self, drive, remedies):
        """
        Choose between known remedies and exploring by sampling each one's
        relief from what is known of it (Thompson 1933). Exploring stands
        for an act not yet tried, whose effect is known only to lie
        somewhere near nothing. Returns the remedy drawn best, or None to
        explore.
        """
        sig = GO.SIGNALS[drive]
        best, pick = self.choose.gauss(0.0, R.get("relief_prior_sd")), None
        for act, kind, _, _ in remedies:
            mean, se, _ = self.goals.reliefs[(act, kind)].change(sig)
            draw = self.choose.gauss(mean, se) if se > 0.0 else mean
            if draw < best:
                best, pick = draw, (act, kind)
        return pick

    def _pursue(self, drive, signals, terrain, time):
        remedies = [r for r in self.goals.remedies(drive) if r[0] != "strike"]
        if not remedies:
            return None
        pick = self._weigh(drive, remedies)
        if pick is None:
            return None
        act, kind = pick
        target = self._at_hand(kind, act, time)
        if target is not None:
            done = self._start(act, kind, [target], signals,
                               int(R.get("remedy_bout_max_acts")), drive,
                               True, terrain, time)
            if done.done:
                return done
        a = self.actor
        for act, kind in [pick]:
            goal = PN.Goal({("near", kind)}, origin=(drive, act, kind))
            plan, decision = PN.plan(goal, self.state(time),
                                     self.skills.operators, self.choose, time)
            if plan is not None and plan.steps:
                self.news.append(("decision", decision))
                done = self._perform(plan.steps[0], terrain, time)
                if done is not None:
                    return done
            spots = self.places.where(kind, a.here, time)
            if spots:
                done = PR.approach(a, terrain, terrain.at(*spots[0]))
                if done.done:
                    self.acts += 1
                    self.skills.begin(self.state(time))
                    return done
        return None

    def _explore(self, signals, terrain, time, drive=None):
        a, s = self.actor, self.choose
        near, held = list(a.cell.things), list(a.held)
        reach = held + near
        options = ["move", "rest"]
        if near:
            options.append("grasp")
        if held:
            options.append("release")
        if reach:
            options += ["consume", "touch"]
        if held and len(reach) >= 2:
            options.append("strike")
        # An innate mouthing tendency, declared and off in the baseline: it
        # says nothing about what to put in the mouth, only that hunger and
        # thirst make putting things there likelier (consummatory_bias).
        bias = R.get("consummatory_bias")
        if (bias > 0.0 and reach and drive in ("hunger", "thirst")
                and s.random() < bias):
            act = "consume"
        else:
            act = s.choice(sorted(options))
        kind = None
        if act == "move":
            targets = [s.choice(terrain.neighbours(a.cell.x, a.cell.y))]
        elif act == "rest":
            targets = []
        elif act == "grasp":
            targets = [s.choice(near)]
        elif act == "release":
            targets = [s.choice(held)]
        elif act == "strike":
            x = s.choice(held)
            targets = [x, s.choice([t for t in reach if t is not x])]
        else:
            targets = [s.choice(reach)]
        if targets and act != "move":
            kinds = tuple(self.kind(t, time) for t in targets)
            kind = kinds[0] if len(kinds) == 1 else kinds
        return self._start(act, kind, targets, signals,
                           int(R.get("explore_bout_acts")), None, False,
                           terrain, time)

    def turn(self, terrain, time):
        """
        Feel, look, decide and act once. Returns (seconds the turn took,
        whether the body slept through it).
        """
        least = R.get("turn_min_s")
        self.skills.sync(self.state(time))
        self.survey(time)
        signals = self.feel(time)
        drive, _ = self.goals.most_urgent(signals)
        if drive == "rest":
            self._close(signals, time)
            return R.get("sleep_turn_s"), True
        b = self.bout
        if b is not None and b.left > 0 and (not b.remedy or b.drive == drive):
            done = self._continue(terrain, time)
            if done is not None:
                return max(done.duration_s, least), False
        self._close(signals, time)
        done = None
        if self.learning and drive in GO.SIGNALS:
            done = self._pursue(drive, signals, terrain, time)
        if done is None:
            done = self._explore(signals, terrain, time, drive)
        return max(done.duration_s if done is not None else 0.0, least), False
