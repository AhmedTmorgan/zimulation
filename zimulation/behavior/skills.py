"""
Skills: runs of acts stored as procedures because they work.

Contract section 9. No skill list exists beforehand. A skill forms when an
agent's own acts are seen, again and again, to turn one perceived state
into another; it is then stored, refined with practice, and forgotten with
disuse. Nothing here knows what any act does or what any sequence is for.

## What the agent has to go on

A state is what the agent perceives of its situation: a multiset of
(place, kind) tokens -- "something of my kind 3 is in my hand", "something
of my kind 5 lies here". Kinds are the agent's own categories
(cognition.concepts); places are whatever the caller distinguishes. A step
is one act -- a primitive, or a skill already stored -- applied to things
of given kinds, with given settings.

## How a skill forms

Working memory holds the last few acts (working_memory_items; Cowan 2001).
Each time an act changes the perceived state, every run of recent acts
ending with it is a possible explanation of that change. A routine is such
a run performed from one kind of situation -- the tokens, before its first
act, that concern the kinds it acts on. Each time the same run is performed
from the same kind of situation, every change it has been credited with
gains an attempt, and a success if the change recurs. Changes are also
split into their single parts, so that "things of kind 7 appear" can prove
reliable even when what accompanied it varies.

A routine becomes a stored skill when some change it is credited with has
been attempted enough, has followed reliably, involves at least two acts
(one act alone is a fact about that act, which causal learning records),
and is not redundant: if leaving out any one act, from the same kind of
situation, has produced the same change at least as reliably, the longer
run carried a step that did nothing. When the evidence to show that
exists, the useless step is kept out. When it does not, the step stays in
-- a superstitious habit, formed the way superstitions form -- and it is
left for the observer to find. If the evidence arrives later, the shorter
procedure replaces the longer and records what it replaced.

## Procedures within procedures

A stored skill can be performed as one act, and then it takes one place in
working memory. Runs that include it can be stored in turn, so procedures
longer than working memory are built as hierarchies of short ones
(production compilation; Newell & Rosenbloom 1981, Taatgen & Anderson
2002).

## Refinement and forgetting

A skill remembers the settings -- how long, how hard, how far -- of the
performances that produced its change, and proposes new settings near
them. Settings that fail stop being proposed, so a procedure grows more
reliable with practice without anyone knowing the right values.
Performing the same run again is practice whether or not it was invoked as
a whole. When the store is full, the least recently practised procedure
gives way -- not the oldest, which would let a flood of trivial handling
routines push out one that matters. Unused skills fade with a half-life far longer than episodic memory's (Arthur et
al. 1998) and are then gone.

## Measured (six seeds; an adult acting at random among a granite cobble,
## a hardwood stick and a supply of flint cores; 2000 acts each)

Every agent stored a stone-breaking procedure, the first between acts 41
and 186. What it stored is expressed in its own kinds, and those are
coarse: by touch a granite cobble and a flint core feel alike -- heavy,
hard, blunt -- and in five seeds of six they fell into one kind. The
typical procedure is therefore "grasp something heavy and hard, strike it
on something heavy and hard, and small pieces appear"; the best of them
succeeded in every performance (19 to 40) in five seeds and in 24 of 25 in
the sixth. It works here only because a core is always present. Where
granite abounded and flint was rare the same procedure would mostly fail
-- an over-general procedure of the kind people form. In the one seed
where granite had a kind of its own, the procedure was hammerstone on
flint. Steps that did nothing survived where nothing showed them useless
(grasp, release, grasp, strike). Each agent also stored 77 to 138
procedures in all, most of them trivial handling routines -- picking up
two things, putting one down -- which are real chunks, not errors.

The first run of this measurement reported success on every seed for a
degenerate reason: the harness filed things without learning from them,
every kind stayed at its first member, and cobble, core and flake shared
one kind. The check was then tightened to require a kind made mostly of
broken-off pieces.

## Provenance

Every skill records who formed it, when, from which performances, which
longer procedure it replaced, and -- for one learned by watching another,
in a later phase -- from whom it came.
"""

from __future__ import annotations

import math
from collections import Counter

from ..core.parameters import REGISTRY as R
from ..core.scheduler import DAY

_EMPTY = (0, 0.0, 0.0)


def _add(stats, v):
    """Welford update of (n, mean, sum of squared deviations)."""
    n, mean, m2 = stats
    n += 1
    d = v - mean
    mean += d / n
    return (n, mean, m2 + d * (v - mean))


class Step:
    """One act as the agent remembers it: what it did, to things of which
    kinds, with which settings."""

    __slots__ = ("act", "roles", "params")

    def __init__(self, act, roles=(), params=None):
        self.act = act
        self.roles = tuple(roles)
        self.params = dict(params or {})

    @property
    def key(self):
        return (self.act, self.roles)

    def __repr__(self):
        return f"<Step {self.act} {self.roles}>"


# ------------------------------------------------------------- states
def _present(state):
    return frozenset(t for t, n in state.items() if n > 0)


def _about(tokens, kinds):
    """The tokens that concern things of the given kinds. A token is a
    (place, kind) pair."""
    return frozenset(t for t in tokens if t[1] in kinds)


def _change(before, after):
    """What appeared and what vanished between two perceived states."""
    up = frozenset(t for t, n in after.items() if n > before.get(t, 0))
    down = frozenset(t for t, n in before.items() if n > after.get(t, 0))
    return up, down


def _within(effect, change):
    return effect[0] <= change[0] and effect[1] <= change[1]


def _effects(change):
    """The whole change, and each of its parts on its own."""
    up, down = change
    out = [change]
    for t in sorted(up, key=repr):
        out.append((frozenset((t,)), frozenset()))
    for t in sorted(down, key=repr):
        out.append((frozenset(), frozenset((t,))))
    return [e for i, e in enumerate(out) if e not in out[:i]]


def _subsequence(short, long):
    it = iter(long)
    return len(short) < len(long) and all(
        any(x == y for y in it) for x in short)


def _kinds(steps):
    return {r for _, roles in steps for r in roles}


# ------------------------------------------------------------ records
class Candidate:
    """One change a routine might be credited with, and how often it
    followed."""

    __slots__ = ("effect", "attempts", "successes", "settings", "examples",
                 "serial")

    def __init__(self, effect, n_steps, serial):
        self.effect = effect
        self.attempts = 0
        self.successes = 0
        self.settings = [{} for _ in range(n_steps)]
        self.examples = []
        self.serial = serial

    @property
    def reliability(self):
        """Successes over attempts, with one imagined success and one
        imagined failure (Laplace's rule of succession)."""
        return (self.successes + 1) / (self.attempts + 2)


class Routine:
    """A run of acts performed from one kind of situation."""

    __slots__ = ("pre", "steps", "cands", "skill", "last_time", "serial")

    def __init__(self, pre, steps, time, serial):
        self.pre = pre
        self.steps = steps
        self.cands = {}
        self.skill = None
        self.last_time = time
        self.serial = serial


class Skill:
    """A stored procedure, and where it came from."""

    __slots__ = ("id", "creator", "origin_time", "basis", "strength",
                 "practice", "last_used", "replaced", "received_from")

    def __init__(self, sid, creator, time, basis):
        self.id = sid
        self.creator = creator
        self.origin_time = time
        self.basis = basis
        self.strength = 1.0
        self.practice = 0
        self.last_used = time
        self.replaced = ()
        self.received_from = None

    @property
    def steps(self):
        return self.basis.steps

    @property
    def pre(self):
        return self.basis.pre

    @property
    def roles(self):
        out = []
        for _, roles in self.basis.steps:
            for r in roles:
                if r not in out:
                    out.append(r)
        return tuple(out)

    def __repr__(self):
        return f"<Skill {self.id} {len(self.steps)} steps>"


# ------------------------------------------------------------- the store
class Skills:
    """One agent's procedures, and the runs of acts it is still judging."""

    __slots__ = ("owner", "items", "_seq", "_serial", "_routines", "_by_id",
                 "_buffer", "_state")

    def __init__(self, owner):
        self.owner = owner
        self.items = []
        self._seq = 0
        self._serial = 0
        self._routines = {}
        self._by_id = {}
        self._buffer = []
        self._state = Counter()

    def begin(self, state):
        """Take in the situation afresh -- after something happened that
        the agent did not do -- and clear working memory."""
        self._state = +Counter(state)
        self._buffer = []

    def sync(self, state):
        """Take in the situation only if something the agent did not do
        has changed it -- regrowth, weather, another's hand -- so that the
        change is not credited to the agent's own recent acts."""
        fresh = +Counter(state)
        if fresh != self._state:
            self.begin(fresh)

    # ---------------------------------------------------------- learning
    def record(self, step, state_after, time, trace_id=None, settings=None):
        """
        One act has been performed and its result perceived. Credit every
        run of recent acts ending with it, store any routine that has
        earned it, and return the skills newly stored. For a skill
        performed as a whole, `settings` gives the settings each of its
        steps used.
        """
        after = +Counter(state_after)
        skill = self._by_id.get(step.act)
        if skill is not None:
            self._performed(skill, self._state, after, time, trace_id,
                            settings)
        self._buffer.append((self._state, step))
        del self._buffer[:-max(1, int(R.get("working_memory_items")))]
        made, touched = [], []
        for i in range(len(self._buffer)):
            before = self._buffer[i][0]
            run = [s for _, s in self._buffer[i:]]
            routine, new = self._consider(before, run, after, time,
                                          trace_id)
            made += new
            if routine is not None:
                touched.append(routine)
        self._retire(touched)
        self._state = after
        self._tidy()
        return made

    def _tally(self, cand, change, run, trace_id):
        cand.attempts += 1
        if not _within(cand.effect, change):
            return
        cand.successes += 1
        for stats, s in zip(cand.settings, run):
            for name, v in s.params.items():
                stats[name] = _add(stats.get(name, _EMPTY), v)
        cand.examples.append(trace_id)
        del cand.examples[:-int(R.get("skill_example_cap"))]

    def _consider(self, before, run, after, time, trace_id):
        steps = tuple(s.key for s in run)
        pre = _about(_present(before), _kinds(steps))
        change = _change(before, after)
        routine = self._routines.get((pre, steps))
        if routine is None:
            if not (change[0] or change[1]):
                return None, []
            self._serial += 1
            routine = Routine(pre, steps, time, self._serial)
            self._routines[(pre, steps)] = routine
        routine.last_time = time
        for cand in routine.cands.values():
            self._tally(cand, change, run, trace_id)
        if routine.skill is not None:
            routine.skill.practice += 1
            routine.skill.last_used = time
            routine.skill.strength = 1.0
        if change[0] or change[1]:
            for effect in _effects(change):
                if effect not in routine.cands:
                    self._serial += 1
                    cand = Candidate(effect, len(steps), self._serial)
                    routine.cands[effect] = cand
                    self._tally(cand, change, run, trace_id)
        if routine.skill is None and self._qualifying(routine):
            return routine, [self._store(routine, time)]
        return routine, []

    def _redundant(self, routine, cand):
        need = R.get("skill_min_repetitions")
        for i in range(len(routine.steps)):
            shorter = routine.steps[:i] + routine.steps[i + 1:]
            pre = _about(routine.pre, _kinds(shorter))
            other = self._routines.get((pre, shorter))
            rival = None if other is None else other.cands.get(cand.effect)
            if (rival is not None and rival.attempts >= need
                    and rival.reliability >= cand.reliability):
                return True
        return False

    def _qualifying(self, routine):
        """The changes this routine reliably produces, of which no shorter
        run from the same situation has proved as capable."""
        if len(routine.steps) < 2:
            return []
        need = R.get("skill_min_repetitions")
        floor = R.get("skill_min_reliability")
        return [c for c in routine.cands.values()
                if c.attempts >= need and c.reliability >= floor
                and not self._redundant(routine, c)]

    def _store(self, routine, time):
        self._seq += 1
        sk = Skill(("skill", self.owner, self._seq), self.owner, time,
                   routine)
        routine.skill = sk
        if len(self.items) >= int(R.get("skill_capacity")):
            self._drop(min(self.items, key=lambda s: (
                s.strength, s.last_used, s.origin_time)))
        self.items.append(sk)
        self._by_id[sk.id] = sk
        return sk

    def _superseded(self, routine):
        """Whether everything this routine reliably does, a shorter run
        from the same situation has been shown to do at least as well."""
        need = R.get("skill_min_repetitions")
        floor = R.get("skill_min_reliability")
        able = [c for c in routine.cands.values()
                if c.attempts >= need and c.reliability >= floor]
        return bool(able) and all(self._redundant(routine, c) for c in able)

    def _retire(self, touched):
        """
        Drop stored procedures that a shorter run, now shown at least as
        reliable from the same situation, has made redundant. Evidence can
        arrive after a procedure was stored -- the first version checked
        only at the moment of storing, so a habit stored early outlived
        the evidence against it -- so this is checked whenever a shorter
        run is performed. The shorter procedure, if stored, records what
        it replaced. A procedure that has merely become unreliable is not
        dropped here; it fades with disuse.
        """
        for old in list(self.items):
            shorter = [r for r in touched if _subsequence(r.steps, old.steps)]
            if not shorter or not self._superseded(old.basis):
                continue
            heir = next((r.skill for r in shorter if r.skill is not None),
                        None)
            if heir is not None:
                heir.replaced += (old.id,) + old.replaced
            self._drop(old)

    def _drop(self, sk):
        self.items.remove(sk)
        del self._by_id[sk.id]
        sk.basis.skill = None

    def _performed(self, skill, before, after, time, trace_id, settings):
        skill.practice += 1
        skill.last_used = time
        skill.strength = 1.0
        used = settings or [{} for _ in skill.steps]
        run = [Step(a, r, p) for (a, r), p in zip(skill.steps, used)]
        change = _change(before, after)
        for cand in skill.basis.cands.values():
            self._tally(cand, change, run, trace_id)

    def _tidy(self):
        """Forget the least recently seen runs once too many are tracked;
        runs that are stored skills are kept."""
        cap = int(R.get("skill_routine_capacity"))
        if len(self._routines) <= cap:
            return
        spare = sorted((r for r in self._routines.values() if r.skill is None),
                       key=lambda r: (r.last_time, r.serial))
        for r in spare[:max(1, len(self._routines) // 4)]:
            del self._routines[(r.pre, r.steps)]

    # ---------------------------------------------------------- forgetting
    def decay(self, dt_s):
        """Unused procedures fade; those below the threshold are gone.
        Returns how many were forgotten."""
        f = 0.5 ** (dt_s / (R.get("skill_half_life_days") * DAY))
        for s in self.items:
            s.strength *= f
        floor = R.get("skill_forget_threshold")
        gone = [s for s in self.items if s.strength < floor]
        for s in gone:
            self._drop(s)
        return len(gone)

    # ----------------------------------------------------------------- use
    def effects(self, skill):
        """What this procedure reliably does, most reliable first."""
        return sorted(self._qualifying(skill.basis),
                      key=lambda c: (-c.reliability, c.serial))

    def _expectation(self, routine):
        """What a run reliably changes: every part of its change that has
        followed it reliably, and the chance of the least reliable part."""
        need = R.get("skill_min_repetitions")
        floor = R.get("skill_min_reliability")
        sure = [c for c in routine.cands.values()
                if c.attempts >= need and c.reliability >= floor]
        if not sure:
            return None
        up = frozenset().union(*(c.effect[0] for c in sure))
        down = frozenset().union(*(c.effect[1] for c in sure))
        return (up, down), min(c.reliability for c in sure)

    def operators(self, state):
        """
        What this agent expects it could do from here and what each would
        change: single acts it has seen change things from a situation like
        this one, and stored procedures whose starting situation is present.
        Each comes as (step, change, chance). Its own experience is all it
        has: acts never tried, and changes seen too seldom, are absent.
        """
        here = _present(Counter(state))
        out = []
        for routine in self._routines.values():
            if len(routine.steps) == 1 and routine.pre <= here:
                exp = self._expectation(routine)
                if exp is not None:
                    out.append((routine.steps[0], exp[0], exp[1]))
        for s in self.items:
            if s.pre <= here:
                exp = self._expectation(s.basis)
                if exp is not None:
                    out.append(((s.id, s.roles), exp[0], exp[1]))
        return out

    def applicable(self, state):
        """The procedures whose starting situation is present now."""
        here = _present(Counter(state))
        return [s for s in self.items if s.pre <= here]

    def propose(self, skill, stream):
        """
        Steps to perform the procedure, with settings drawn near those of
        its successful performances -- spread by how much they varied, so
        a procedure still being learned keeps exploring.
        """
        best = self.effects(skill)
        cand = best[0] if best else None
        out = []
        for i, (act, roles) in enumerate(skill.steps):
            params = {}
            if cand is not None:
                for name, (n, mean, m2) in cand.settings[i].items():
                    sd = math.sqrt(m2 / (n - 1)) if n > 1 else 0.0
                    params[name] = (stream.gauss(mean, sd) if sd > 0.0
                                    else mean)
            out.append(Step(act, roles, params))
        return out
