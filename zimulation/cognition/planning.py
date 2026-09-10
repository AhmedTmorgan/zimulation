"""
Planning: looking a few acts ahead with the only map an agent has -- its
own experience.

Contract sections 12, 15, 26 and 43. An agent is not a utility-maximising
point. It plans the way people do under limits: it imagines acts it has
seen change things before, from situations like the present one, predicts
what each would change, and looks for a short run of them that would bring
about what it wants. It looks only a few acts ahead (a planning horizon),
examines only so many imagined situations (a computation budget), and
stops at the first plan it judges good enough -- satisficing (Simon 1956)
-- rather than at the best one that exists. Which options occur to it
first is not fixed: the order is drawn from its own stream, so two agents
with the same knowledge may settle on different plans.

## What it plans with

The transition model is the agent's own record of what its acts did
(behavior.skills.operators): single acts it has seen change things from a
like situation, and stored procedures, each with the change that reliably
followed and how reliably. Acts never tried are not imagined, and changes
seen too seldom are not relied on. An agent's plans can be only as good as
its experience -- and a stored procedure carrying a superstitious step is
planned with, step and all. Practised as one unit, it is also found before
any longer composition of single acts, which is one reason such habits
persist.

## What it records

Section 26 asks why an agent chooses harm when it believes a better
alternative exists. That can only be asked of an agent whose alternatives
and predictions are on record. Every decision therefore returns what was
considered: each first act that occurred to the agent, the best predicted
chance of meeting the goal through it, which was chosen, how many imagined
situations were examined, and whether the search stopped because a plan
was good enough, because the budget or the horizon ran out, or because
experience offered nothing more. Every number in it is the agent's own
prediction; nothing here reads the world.

## Measured (eight seeds; an adult after 2000 random acts among a granite
## cobble, a hardwood stick and flint cores)

The goal set was in the agent's own terms: that things of its kind of
broken-off pieces lie before it, starting from a scene that does not
already show them. In two seeds of eight its kinds could not tell pieces
from cores, and the goal could not be posed. In the other six, over 27
trials, plans met the goal 14 times (52%) against 7 (26%) for the same
number of random acts from the same scene. Its predictions were calibrated:
plans given a mean chance of 0.66 succeeded 64% of the time. Demanding
more (aspiration 0.8) raised success only to 58% and made the agent
overconfident -- predicted 0.81, realised 0.71 -- because choosing the
plans that look best also chooses those whose estimates happen to run
high: the optimiser's curse (Smith & Winkler 2006), which nothing here
was written to produce.

## Following a plan

A plan carries the situation it predicts after each step. When what is
perceived departs from what was predicted the plan is off track, and it is
for the caller to plan again -- revision after evidence, one of section
43's measures.
"""

from __future__ import annotations

from collections import Counter

from ..core.parameters import REGISTRY as R


class Goal:
    """What the agent wants to perceive: some tokens present, some absent."""

    __slots__ = ("wanted", "unwanted", "origin")

    def __init__(self, wanted=(), unwanted=(), origin=None):
        self.wanted = frozenset(wanted)
        self.unwanted = frozenset(unwanted)
        self.origin = origin

    def met(self, state):
        return (all(state.get(t, 0) > 0 for t in self.wanted)
                and not any(state.get(t, 0) > 0 for t in self.unwanted))


def apply(state, change):
    """The situation an expected change would lead to."""
    up, down = change
    out = Counter(state)
    for t in down:
        out[t] -= 1
    for t in up:
        out[t] += 1
    return +out


def _frozen(state):
    return frozenset(state.items())


class Plan:
    """A run of steps, the situation predicted after each, and the chance
    the agent gives it of meeting the goal."""

    __slots__ = ("goal", "steps", "states", "chance")

    def __init__(self, goal, steps, states, chance):
        self.goal = goal
        self.steps = steps
        self.states = states
        self.chance = chance

    def on_track(self, index, observed):
        """Whether what is perceived after step `index` shows the changes
        the plan predicted for that step."""
        before, after = self.states[index], self.states[index + 1]
        seen = Counter(observed)
        for t, n in after.items():
            if n > before.get(t, 0) and seen.get(t, 0) < 1:
                return False
        for t in before:
            if after.get(t, 0) == 0 and seen.get(t, 0) > 0:
                return False
        return True


class Decision:
    """What one planning episode considered, predicted and chose."""

    __slots__ = ("goal", "time", "alternatives", "chosen", "chance",
                 "examined", "stopped")

    def __init__(self, goal, time, alternatives, chosen, chance, examined,
                 stopped):
        self.goal = goal
        self.time = time
        self.alternatives = alternatives
        self.chosen = chosen
        self.chance = chance
        self.examined = examined
        self.stopped = stopped


def plan(goal, state, operators, stream, time=0):
    """
    Search for a short run of steps predicted to meet the goal.

    `operators(state)` gives the agent's expectations for a situation as
    (step, change, chance) triples. The search is breadth-first to the
    horizon, examines at most the budget of imagined situations, takes
    options in an order drawn from the stream, and stops at the first plan
    whose predicted chance reaches the aspiration; failing that it returns
    the best it found. Returns (Plan or None, Decision).
    """
    horizon = int(R.get("planning_horizon_steps"))
    budget = int(R.get("planning_budget_nodes"))
    aspire = R.get("plan_aspiration")
    start = +Counter(state)
    if goal.met(start):
        return (Plan(goal, [], [start], 1.0),
                Decision(goal, time, {}, None, 1.0, 0, "already met"))
    alternatives, best, examined = {}, None, 0
    stopped = "exhausted"
    seen = {_frozen(start)}
    frontier = [([], [start], 1.0)]
    for _ in range(horizon):
        nxt = []
        for steps, states, chance in frontier:
            options = list(operators(states[-1]))
            stream.shuffle(options)
            for step, change, p in options:
                if examined >= budget:
                    stopped = "budget"
                    break
                examined += 1
                after = apply(states[-1], change)
                path, trail, c = steps + [step], states + [after], chance * p
                alternatives.setdefault(path[0], 0.0)
                if goal.met(after):
                    alternatives[path[0]] = max(alternatives[path[0]], c)
                    if best is None or c > best.chance:
                        best = Plan(goal, path, trail, c)
                    if c >= aspire:
                        stopped = "satisfied"
                        break
                    continue
                k = _frozen(after)
                if k not in seen:
                    seen.add(k)
                    nxt.append((path, trail, c))
            if stopped in ("budget", "satisfied"):
                break
        if stopped in ("budget", "satisfied") or not nxt:
            break
        frontier = nxt
    else:
        stopped = "horizon"
    chosen = best.steps[0] if best is not None else None
    return best, Decision(goal, time, alternatives, chosen,
                          best.chance if best is not None else 0.0,
                          examined, stopped)
