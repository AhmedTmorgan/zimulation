"""
Causal inference: learning what makes what happen.

Contract section 18 asks that an agent be able to arrive at four different
conclusions about two things A and B, and to tell them apart:

    A predicts B              they go together
    A may cause B             making A happen makes B more likely
    A does not reliably       making A happen changes nothing
      cause B
    A and B share a cause     they go together, but making A happen
                              changes nothing -- something else drives both

The difference between the first and the second is the difference between
superstition and knowledge, and it rests on one distinction.

## Watching versus doing

When an agent sees A and then B, that is an *observation*. Observations
can only ever show that things go together, because whatever brought A
about may also have brought B. When an agent *itself* does A and then sees
B, that is an *intervention* -- the agent's own action cuts A loose from
whatever else might have caused it (Pearl 2000, the do-operator). Only
interventions can support "A may cause B".

This is not a rule imposed on the agent. It is what the arithmetic below
does with the two kinds of trial, which are kept in separate tables.
Children behave this way with remarkably little data (Gopnik et al. 2004),
which is some reason to think a mind can come by it without being taught.

## Where superstition comes from

To say an intervention *worked*, an agent needs something to compare it
with: how often B happens when it does not act. An agent that never
withholds its action has no such comparison, and falls back on its prior
-- which, set low, means it assumes B does not happen on its own. Then
every outcome that would have happened anyway is credited to the action.

That is the whole mechanism behind a remedy that "works" on an illness
that would have passed regardless, and nothing here writes it. It falls
out of missing controls (Skinner 1948; Langer 1975, the illusion of
control). Give the same agent a handful of trials in which it withheld the
action and watched, and the illusion dissolves -- also without anything
here writing that. The control group is the whole of the difference.

Measured over 200 seeds: without controls, every agent credits a
self-limiting outcome to its own action. With twenty control trials, 90%
correctly judge it ineffective. The remaining errors are the honest false
positives of a finite learner -- at thirty trials each, an action that does
nothing is still judged to work 7% of the time, and a hidden common cause
is taken for a real one 12% of the time.

## Speed against accuracy

`causal_evidence_threshold` is a hypothesis parameter. Over 400 agents per
setting, in a world where the action does nothing, the share fooled into
"may cause" falls from about 28% at two trials each to 11% at twenty and
5% at forty; where the action really works, the share that gets it right
rises from 73% at one trial to 96% at five and 100% from ten on. Quick
learners are often wrong and careful ones slow. Which trade-off a
population ends up with, and whether culture can shift it, is a question
the experiment asks (contract H9).

The curve is not smooth, and that is left in deliberately: ten trials fool
more agents than five. The agent judges by the size of the difference in
rates and takes no account of how many trials produced it, so the number of
chance successes needed to cross its line rises in whole steps -- two extra
at five trials and still two at ten, then four at twenty -- while the luck
available grows smoothly with the trials. Between steps, more evidence
means more room for a lucky run. That is the belief in the law of small
numbers (Tversky & Kahneman 1971).

A mind that weighed a difference against its sample size would not show
the sawtooth. But that weighing is statistics, and building it into every
agent would hand them the achievement H9 asks whether they can reach. If
it appears, it has to arrive as something a culture works out.

## What the agent cannot know

The real mechanism linking A and B is the observer's. An agent's verdict
is a belief about a cause; the observer compares it against the sealed
truth to count superstitions, missed causes and correctly exposed
confounds. Nothing in this module can open that truth.

Counts fade with the same half-life as episodic memory, since that is what
they are learned from -- so a world that changes can change a mind.
"""

from __future__ import annotations

from ..core.parameters import REGISTRY as R
from .memory import _halving

UNKNOWN = "unknown"
PREDICTS = "predicts"
MAY_CAUSE = "may_cause"
NOT_RELIABLE = "not_reliable"
SHARED_CAUSE = "shared_cause"


def precedes(t_cause, t_effect):
    """
    Whether an outcome follows a candidate cause closely enough to be
    linked to it. Causes precede effects (Hume); an outcome before its
    supposed cause, or long after it, is not evidence about it.
    """
    dt = t_effect - t_cause
    return 0 < dt <= R.get("causal_window_s")


class Contingency:
    """
    Everything one agent has seen about whether A goes with B.

    Two separate tables. Observational: trials where A was or was not
    *seen*. Interventional: trials where the agent *did* A, and control
    trials where it deliberately did not and watched anyway. Counts are
    real-valued because they fade.
    """

    __slots__ = ("cause", "effect",
                 "seen_a_b", "seen_a_nb", "seen_na_b", "seen_na_nb",
                 "did_b", "did_nb", "held_b", "held_nb", "last_t")

    def __init__(self, cause, effect):
        self.cause = cause
        self.effect = effect
        self.seen_a_b = self.seen_a_nb = 0.0
        self.seen_na_b = self.seen_na_nb = 0.0
        self.did_b = self.did_nb = 0.0
        self.held_b = self.held_nb = 0.0
        self.last_t = 0

    # -------------------------------------------------------------- sizes
    @property
    def n_seen_a(self):
        return self.seen_a_b + self.seen_a_nb

    @property
    def n_seen_na(self):
        return self.seen_na_b + self.seen_na_nb

    @property
    def n_did(self):
        return self.did_b + self.did_nb

    @property
    def n_held(self):
        return self.held_b + self.held_nb


def _rate(hits, n):
    """A smoothed rate: evidence pulled toward the prior by pseudo-counts."""
    k = R.get("contingency_prior_count")
    return (hits + k * R.get("baseline_prior_rate")) / (n + k)


def _baseline(c):
    """
    How often B happens when the agent does not act -- the comparison an
    intervention is judged against.

    Its own control trials if it has any; failing that, what it has seen
    happen without A; failing that, nothing but its prior. That last case
    is where superstition lives.
    """
    if c.n_held > 0.0:
        return _rate(c.held_b, c.n_held)
    if c.n_seen_na > 0.0:
        return _rate(c.seen_na_b, c.n_seen_na)
    return R.get("baseline_prior_rate")


def observed_difference(c):
    """Delta-P from watching (Allan 1980): P(B|A) - P(B|not A)."""
    rest = (_rate(c.seen_na_b, c.n_seen_na) if c.n_seen_na > 0.0
            else R.get("baseline_prior_rate"))
    return _rate(c.seen_a_b, c.n_seen_a) - rest


def intervened_difference(c):
    """Delta-P from doing: P(B|do A) - baseline."""
    return _rate(c.did_b, c.n_did) - _baseline(c)


def causal_power(c):
    """
    Generative causal power (Cheng 1997): how much of the room left for B
    to happen is filled by doing A. Undefined when B always happens anyway.
    """
    base = _baseline(c)
    room = 1.0 - base
    if room <= R.get("division_epsilon"):
        return 0.0
    return intervened_difference(c) / room


def verdict(c):
    """
    What this agent now concludes about A and B, and on how much.

    Returns (label, difference, support). Interventions outrank
    observations: once the agent has acted often enough, what it saw
    happen when it acted decides, and a correlation that vanishes under
    intervention is recognised as driven by something else.
    """
    need = R.get("causal_evidence_threshold")
    delta = R.get("causal_delta_threshold")

    if c.n_did >= need:
        d = intervened_difference(c)
        if d > delta:
            return MAY_CAUSE, d, c.n_did
        if c.n_seen_a >= need and observed_difference(c) > delta:
            return SHARED_CAUSE, d, c.n_did
        return NOT_RELIABLE, d, c.n_did

    if c.n_seen_a >= need:
        d = observed_difference(c)
        if d > delta:
            return PREDICTS, d, c.n_seen_a
    return UNKNOWN, 0.0, c.n_did + c.n_seen_a


def certainty(c):
    """How settled the verdict is, from the weight of evidence; below one."""
    n = c.n_did + c.n_seen_a + c.n_held + c.n_seen_na
    return n / (n + R.get("contingency_prior_count"))


class CausalModel:
    """
    One agent's knowledge of what goes with what, and what makes what.

    Keys are opaque: whatever categories the agent itself has formed. This
    module supplies the capacity to relate two things, never the things.
    """

    __slots__ = ("_tables",)

    def __init__(self):
        self._tables = {}

    def _get(self, cause, effect):
        key = (cause, effect)
        c = self._tables.get(key)
        if c is None:
            c = Contingency(cause, effect)
            self._tables[key] = c
        return c

    def observe(self, cause, effect, cause_seen, effect_seen, time,
                weight=1.0):
        """A trial by watching: was A seen, and did B follow?"""
        c = self._get(cause, effect)
        if cause_seen:
            if effect_seen:
                c.seen_a_b += weight
            else:
                c.seen_a_nb += weight
        elif effect_seen:
            c.seen_na_b += weight
        else:
            c.seen_na_nb += weight
        c.last_t = time
        return c

    def intervene(self, cause, effect, acted, effect_seen, time,
                  weight=1.0):
        """
        A trial by doing. `acted` is True when the agent performed A, and
        False for a control -- when it deliberately held back and watched.
        """
        c = self._get(cause, effect)
        if acted:
            if effect_seen:
                c.did_b += weight
            else:
                c.did_nb += weight
        elif effect_seen:
            c.held_b += weight
        else:
            c.held_nb += weight
        c.last_t = time
        return c

    def decay(self, dt_s):
        """Evidence fades at the rate of the memories it came from."""
        f = _halving(dt_s, R.get("memory_half_life_days"))
        for c in self._tables.values():
            c.seen_a_b *= f
            c.seen_a_nb *= f
            c.seen_na_b *= f
            c.seen_na_nb *= f
            c.did_b *= f
            c.did_nb *= f
            c.held_b *= f
            c.held_nb *= f

    def verdict(self, cause, effect):
        c = self._tables.get((cause, effect))
        if c is None:
            return UNKNOWN, 0.0, 0.0
        return verdict(c)

    def table(self, cause, effect):
        return self._tables.get((cause, effect))

    def all(self):
        return list(self._tables.values())
