"""
Planning, verified: bounded look-ahead over the agent's own experience.

The toy world states its rules openly so each claim about the planner can
be checked in isolation; the last test uses the real physics and asks
whether an agent can pursue a goal with what it learned by babbling, better
than acting at random.

    python -m tests.v2.test_planning
"""

from __future__ import annotations

import contextlib
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.behavior.params  # noqa: F401  (declares on import)
import zimulation.biology.params  # noqa: F401
import zimulation.cognition.params  # noqa: F401
import zimulation.world.params  # noqa: F401
from tests.v2.babble import Babbler
from zimulation.behavior import skills as SK
from zimulation.cognition import planning as PL
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.rng import Streams

G_A, S_AB = ("grasp", ("A",)), ("strike", ("A", "B"))
G_C, S_CD = ("grasp", ("C",)), ("strike", ("C", "D"))
G_X, S_XB = ("grasp", ("X",)), ("strike", ("X", "B"))
T_A = ("touch", ("A",))
WANT_C = PL.Goal({("near", "C")})
WANT_E = PL.Goal({("near", "E")})


class Toy:
    """
    Rules in plain sight. grasp moves a thing from near to held; release
    moves it back; a held A struck on a B turns the B into a C; a held C
    struck on a D turns the D into an E; a held X struck on a B turns it
    into a C seven times in ten. touch changes nothing.
    """

    RULES = {("A", "B"): ("B", "C", 1.0), ("C", "D"): ("D", "E", 1.0),
             ("X", "B"): ("B", "C", 0.7)}

    def __init__(self, near, rng):
        self.state = Counter({("near", k): n for k, n in near.items()})
        self.rng = rng

    def do(self, key):
        act, roles = key
        st = self.state.copy()
        if act == "grasp":
            if st[("near", roles[0])] < 1:
                return None
            st[("near", roles[0])] -= 1
            st[("held", roles[0])] += 1
        elif act == "strike":
            x, y = roles
            if st[("held", x)] < 1 or st[("near", y)] < 1:
                return None
            rule = self.RULES.get((x, y))
            if rule is not None and self.rng.random() < rule[2]:
                st[("near", rule[0])] -= 1
                st[("near", rule[1])] += 1
        self.state = +st
        return self.state


def _learn(runs, near, seed=0):
    sk, t, rng = SK.Skills(1), 0, Streams(seed).get("toy")
    for steps in runs:
        toy = Toy(near, rng)
        sk.begin(toy.state)
        for key in steps:
            after = toy.do(key)
            if after is None:
                break
            t += 1
            sk.record(SK.Step(*key), after, t, trace_id=t)
    return sk


def _expand(sk, key):
    skill = sk._by_id.get(key[0])
    if skill is None:
        return [key]
    return [k for inner in skill.steps for k in _expand(sk, inner)]


def _execute(sk, plan, near, seed=0):
    toy = Toy(near, Streams(seed).get("exec"))
    for key in plan.steps:
        for k in _expand(sk, key):
            toy.do(k)
    return toy


@contextlib.contextmanager
def _setting(name, value):
    old = R.get(name)
    R.set(name, value)
    try:
        yield
    finally:
        R.set(name, old)


def _start(**near):
    return Counter({("near", k): n for k, n in near.items()})


# ---------------------------------------------------------------- basics
def test_with_no_experience_there_is_no_plan():
    plan, d = PL.plan(WANT_C, _start(A=1, B=1), SK.Skills(1).operators,
                      Streams(1).get("p"))
    assert plan is None and d.stopped == "exhausted" and not d.alternatives


def test_plans_come_from_experience_and_work():
    sk = _learn([[G_A, S_AB]] * 4, {"A": 1, "B": 1})
    plan, d = PL.plan(WANT_C, _start(A=1, B=1), sk.operators,
                      Streams(1).get("p"))
    assert plan is not None, d.stopped
    assert WANT_C.met(_execute(sk, plan, {"A": 1, "B": 1}).state)


def test_every_decision_records_its_alternatives():
    """
    Section 26 needs the alternatives and the agent's own predictions on
    record. A satisficing agent may stop at the first good-enough option,
    so the record shows how little it considered -- and an alternative
    never considered cannot have been subjectively avoidable. Demanding
    more, it considers every first step, and the one chosen is the best.
    """
    sk = _learn([[G_A, S_AB]] * 4, {"A": 1, "B": 1})
    start = _start(A=1, B=1)
    plan, d = PL.plan(WANT_C, start, sk.operators, Streams(2).get("p"),
                      time=7)
    assert d.time == 7 and d.examined >= len(d.alternatives) >= 1
    assert d.chosen in d.alternatives
    assert abs(d.alternatives[d.chosen] - plan.chance) < 1e-12
    assert all(0.0 <= v <= 1.0 for v in d.alternatives.values())
    with _setting("plan_aspiration", 0.99):
        plan, d = PL.plan(WANT_C, start, sk.operators, Streams(2).get("p"))
    assert len(d.alternatives) >= 2, d.alternatives
    assert d.alternatives[d.chosen] == max(d.alternatives.values())
    assert d.stopped in ("budget", "horizon", "exhausted"), d.stopped


def test_a_plan_knows_when_it_is_off_track():
    sk = _learn([[G_A, S_AB]] * 4, {"A": 1, "B": 1})
    plan, _ = PL.plan(WANT_C, _start(A=1, B=1), sk.operators,
                      Streams(1).get("p"))
    last = len(plan.steps) - 1
    assert plan.on_track(last, plan.states[-1])
    assert not plan.on_track(last, plan.states[last]), \
        "a situation without the predicted change counted as on track"


# ------------------------------------------------------------ the limits
def _chain():
    return _learn([[G_A, S_AB]] * 4 + [[G_C, S_CD]] * 4,
                  {"A": 1, "B": 1, "C": 1, "D": 1})


def test_a_short_horizon_misses_what_a_longer_one_finds():
    """Section 15: a short planning horizon is one source of avoidable
    failure. Reaching E needs two procedures in a row."""
    sk, start = _chain(), _start(A=1, B=1, D=1)
    with _setting("planning_horizon_steps", 1):
        short, d_short = PL.plan(WANT_E, start, sk.operators,
                                 Streams(3).get("p"))
    with _setting("planning_horizon_steps", 2):
        longer, _ = PL.plan(WANT_E, start, sk.operators, Streams(3).get("p"))
    assert short is None and d_short.stopped == "horizon"
    assert longer is not None


def test_limited_computation_can_miss_a_plan():
    """
    With several familiar things to hand, the first look ahead already
    offers more options than a small budget of imagined situations allows,
    so the two-procedure route to E is never reached. A larger budget
    always finds it. (The registry refuses budgets below its declared
    range, so the smallest allowed is used.)
    """
    distract = [[("grasp", (k,))] for k in "FGHJ" for _ in range(4)]
    near = {k: 1 for k in "ABCDFGHJ"}
    sk = _learn([[G_A, S_AB]] * 4 + [[G_C, S_CD]] * 4 + distract, near)
    start = _start(A=1, B=1, D=1, F=1, G=1, H=1, J=1)
    found, stops = {}, {}
    for budget in (5, 200):
        with _setting("planning_budget_nodes", budget):
            results = [PL.plan(WANT_E, start, sk.operators,
                               Streams(s).get("p")) for s in range(20)]
        found[budget] = sum(plan is not None for plan, _ in results)
        stops[budget] = {d.stopped for _, d in results}
    assert found[5] < found[200] == 20, found
    assert stops[5] == {"budget"}, stops


def test_the_agent_satisfices_rather_than_maximising():
    """
    Two routes to C: A on B, which always works, and X on B, which works
    seven times in ten. Content with a good-enough plan, the agent takes
    whichever occurs to it first and sometimes settles for the worse
    route; demanding more, it searches on and takes the better one.
    """
    sk = _learn([[G_A, S_AB]] * 6 + [[G_X, S_XB]] * 12,
                {"A": 1, "B": 1, "X": 1})
    start = _start(A=1, B=1, X=1)
    chances = {}
    for aspiration in (0.6, 0.99):
        with _setting("plan_aspiration", aspiration):
            chances[aspiration] = [
                PL.plan(WANT_C, start, sk.operators, Streams(s).get("p"))[0]
                .chance for s in range(20)]
    easy, hard = chances[0.6], chances[0.99]
    assert min(easy) < max(hard), "never settled for the worse route"
    assert sum(easy) < sum(hard)
    assert len(set(round(c, 12) for c in hard)) == 1, \
        "a demanding search did not always find the best route"


def test_a_stored_habit_is_planned_with_useless_step_and_all():
    """Only grasp-touch-strike was ever practised. The habit is stored
    with its useless touch, and the plan uses it as one unit."""
    sk = _learn([[G_A, T_A, S_AB]] * 5, {"A": 1, "B": 1})
    plan, _ = PL.plan(WANT_C, _start(A=1, B=1), sk.operators,
                      Streams(1).get("p"))
    steps = [k for key in plan.steps for k in _expand(sk, key)]
    assert T_A in steps, f"the habit's touch vanished from the plan: {steps}"


def test_planning_is_deterministic():
    sk, start = _chain(), _start(A=1, B=1, D=1)

    def run():
        plan, d = PL.plan(WANT_E, start, sk.operators, Streams(9).get("p"))
        return plan.steps, plan.chance, d.examined, sorted(
            d.alternatives.items(), key=repr)
    assert run() == run()


# ---------------------------------------------------- real physics, a goal
def test_an_agent_pursues_a_goal_with_what_it_learned():
    """
    After babbling, the agent is set a goal in its own terms: that things
    of its kind of broken-off pieces lie before it. The kind must be one a
    fresh scene -- hands empty, pieces gone, a core and a cobble present --
    does not already show. Where the agent's kinds cannot tell pieces from
    cores the question cannot be asked, and the seed is set aside. From a
    fresh scene the agent plans with what it learned and acts; each trial
    is matched by the same number of random acts from the same scene. The
    first version of this test let the goal be met before anything was
    done in over half its trials, and passed at exactly its threshold.
    """
    horizon = int(R.get("planning_horizon_steps"))
    planned = tried = random_hits = 0
    for seed in range(8):
        b = Babbler(seed).babble(2000)
        b.fresh()
        shown = {kind for _, kind in b.state()}
        pieces = sorted(k for k in b.piece_kinds() if k not in shown)
        if not pieces:
            continue
        target = max(pieces, key=lambda k: sum(
            1 for _, lab in b.labels.values() if lab == k))
        goal = PL.Goal({("near", target)})
        stream = Streams(seed).get("plan")
        lengths = []
        for _ in range(5):
            b.fresh()
            if goal.met(b.state()):
                continue
            plan, _ = PL.plan(goal, b.state(), b.sk.operators, stream, b.t)
            tried += 1
            if plan is None:
                lengths.append(horizon)
                continue
            lengths.append(len([k for key in plan.steps
                                for k in _expand(b.sk, key)]))
            if all(b.perform(key) for key in plan.steps):
                planned += goal.met(b.state())
        for n in lengths:
            b.fresh()
            for _ in range(n):
                b.t += 1
                b.random_act()
            random_hits += goal.met(b.state())
    assert tried >= 15, f"only {tried} informative trials"
    assert planned > random_hits, (planned, random_hits, tried)


def _run_all():
    ok = fail = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  PASS  {name}")
            ok += 1
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            fail += 1
        except Exception as e:
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
            fail += 1
    print(f"\n{ok} passed, {fail} failed")
    return fail


if __name__ == "__main__":
    sys.exit(1 if _run_all() else 0)
