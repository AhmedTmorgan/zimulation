"""
Skills, verified: procedures formed from the agent's own acts.

Most tests use a toy world whose rules the test states openly, so each
claim about the learning mechanism can be checked in isolation. The last
tests use the real physics, the real perception and the agent's own
categories, driven by an act-at-random loop -- motor babbling -- and ask
whether a procedure for breaking stone into sharp pieces is found without
ever being given.

    python -m tests.v2.test_skills
"""

from __future__ import annotations

import ast
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
from zimulation.behavior import primitives as PR
from zimulation.behavior import skills as SK
from zimulation.biology import genetics as G
from zimulation.biology import physiology as P
from zimulation.cognition import concepts as K
from zimulation.cognition import perception as PC
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.rng import Streams
from zimulation.core.scheduler import DAY, YEAR
from zimulation.world import objects as O
from zimulation.world.materials_data import MATERIALS
from zimulation.world.space import Terrain

GRASP_A = SK.Step("grasp", ["A"])
STRIKE_AB = SK.Step("strike", ["A", "B"])
TOUCH_A = SK.Step("touch", ["A"])


class Toy:
    """
    A small world with its rules in plain sight. Things of kinds A, B, C
    lie near or are held. grasp moves one from near to held; release moves
    it back; striking a held A on a B turns that B into a C -- with
    probability p, or only when the force setting lies in a range. touch
    changes nothing.
    """

    def __init__(self, near, p=1.0, force_range=None, seed=0, held=()):
        self.state = Counter({("near", k): n for k, n in near.items()})
        for k in held:
            self.state[("held", k)] += 1
        self.p = p
        self.force_range = force_range
        self.rng = Streams(seed).get("toy")

    def do(self, step):
        st = self.state.copy()
        act, roles = step.act, step.roles
        if act == "grasp":
            if st[("near", roles[0])] < 1:
                return None
            st[("near", roles[0])] -= 1
            st[("held", roles[0])] += 1
        elif act == "release":
            if st[("held", roles[0])] < 1:
                return None
            st[("held", roles[0])] -= 1
            st[("near", roles[0])] += 1
        elif act == "strike":
            x, y = roles
            if st[("held", x)] < 1 or st[("near", y)] < 1:
                return None
            works = self.rng.random() < self.p
            if self.force_range is not None:
                lo, hi = self.force_range
                works = lo <= step.params.get("force", -1.0) <= hi
            if (x, y) == ("A", "B") and works:
                st[("near", "B")] -= 1
                st[("near", "C")] += 1
        self.state = +st
        return self.state


def _run(sk, toy, steps, t):
    sk.begin(toy.state)
    made = []
    for step in steps:
        after = toy.do(step)
        if after is None:
            break
        t += 1
        made += sk.record(step, after, t, trace_id=t)
    return made, t


def _trained(reps=4):
    sk, t = SK.Skills(1), 0
    for _ in range(reps):
        _, t = _run(sk, Toy({"A": 1, "B": 1}), [GRASP_A, STRIKE_AB], t)
    return sk, t


# ------------------------------------------------------------ formation
def test_no_skill_exists_beforehand_and_none_is_named():
    """Section 9: no skill list. The module does not even know what acts
    exist."""
    assert SK.Skills(1).items == []
    tree = ast.parse((ROOT / "zimulation" / "behavior" / "skills.py")
                     .read_text(encoding="utf-8"))
    acts = set(PR.PRIMITIVES)
    hits = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
            and isinstance(n.value, str) and n.value in acts]
    hits += [n.id for n in ast.walk(tree)
             if isinstance(n, ast.Name) and n.id in acts]
    assert not hits, f"skills.py names acts: {hits}"


def test_a_reliable_sequence_becomes_a_skill():
    sk, _ = _trained()
    assert len(sk.items) == 1, sk.items
    s = sk.items[0]
    assert s.steps == (("grasp", ("A",)), ("strike", ("A", "B")))
    assert any(("near", "C") in c.effect[0] for c in sk.effects(s))


def test_an_unreliable_sequence_does_not():
    sk, t = SK.Skills(1), 0
    for i in range(20):
        _, t = _run(sk, Toy({"A": 1, "B": 1}, p=0.15, seed=i),
                    [GRASP_A, STRIKE_AB], t)
    assert not sk.items, f"an unreliable run was stored: {sk.items}"


def test_a_useless_step_is_kept_out_when_the_evidence_shows_it():
    """Sometimes grasp-then-strike, sometimes grasp-touch-strike: the
    touch is seen to add nothing, and is not stored."""
    sk, t = SK.Skills(1), 0
    for i in range(12):
        steps = [GRASP_A, TOUCH_A, STRIKE_AB] if i % 2 else [GRASP_A,
                                                            STRIKE_AB]
        _, t = _run(sk, Toy({"A": 1, "B": 1}), steps, t)
    assert sk.items, "nothing was stored"
    for s in sk.items:
        assert ("touch", ("A",)) not in s.steps, f"useless step kept: {s}"


def test_without_the_evidence_the_useless_step_survives_then_goes():
    """
    Always grasp-touch-strike: nothing shows the touch is useless, so it
    is stored with it -- a superstitious habit. Once grasp-then-strike is
    also seen to work, the shorter procedure replaces it and records what
    it replaced.
    """
    sk, t = SK.Skills(1), 0
    for _ in range(5):
        _, t = _run(sk, Toy({"A": 1, "B": 1}), [GRASP_A, TOUCH_A, STRIKE_AB],
                    t)
    habit = [s for s in sk.items if ("touch", ("A",)) in s.steps]
    assert habit, "with no evidence against it the habit should form"
    for _ in range(5):
        _, t = _run(sk, Toy({"A": 1, "B": 1}), [GRASP_A, STRIKE_AB], t)
    assert habit[0] not in sk.items, "the habit outlived the evidence"
    lean = [s for s in sk.items if s.steps == (("grasp", ("A",)),
                                               ("strike", ("A", "B")))]
    assert lean and habit[0].id in lean[0].replaced


def test_procedures_nest_within_procedures():
    """A stored skill performed as one act takes one place in working
    memory, and runs that include it can be stored in turn."""
    sk, t = _trained()
    base = sk.items[0]
    practised = base.practice
    for _ in range(4):
        toy = Toy({"A": 1, "B": 1})
        sk.begin(toy.state)
        for step in sk.propose(base, Streams(1).get("p")):
            toy.do(step)
        t += 1
        sk.record(SK.Step(base.id, base.roles), toy.state, t,
                  settings=[{}, {}])
        after = toy.do(SK.Step("grasp", ["C"]))
        t += 1
        sk.record(SK.Step("grasp", ["C"]), after, t)
    nested = [s for s in sk.items if any(a == base.id for a, _ in s.steps)]
    assert nested, "no procedure was built on a procedure"
    assert base.practice == practised + 4, "a performance went uncounted"


# ----------------------------------------------------- refinement, decay
def test_settings_converge_on_what_works():
    """Strikes work only above a force the agent is never told. Random
    settings succeed 80% of the time; the stored procedure's own
    proposals, drawn near its past successes, do better."""
    sk, t = SK.Skills(1), 0
    rng = Streams(3).get("force")
    for _ in range(12):
        strike = SK.Step("strike", ["A", "B"], {"force": rng.uniform(0.0, 0.5)})
        _, t = _run(sk, Toy({"A": 1, "B": 1}, force_range=(0.1, 1.0)),
                    [GRASP_A, strike], t)
    assert sk.items, "nothing was stored"
    s, prop, hits = sk.items[0], Streams(4).get("propose"), 0
    for _ in range(200):
        toy = Toy({"A": 1, "B": 1}, force_range=(0.1, 1.0))
        for step in sk.propose(s, prop):
            toy.do(step)
        hits += toy.state[("near", "C")] > 0
    assert hits >= 180, f"proposals worked {hits}/200 times"


def test_unused_skills_fade_and_practised_ones_stay():
    hl = R.get("skill_half_life_days") * DAY
    idle, _ = _trained()
    idle.decay(5 * hl)
    assert not idle.items, "a skill survived five half-lives unused"
    kept, t = _trained()
    s = kept.items[0]
    for _ in range(10):
        kept.decay(0.5 * hl)
        toy = Toy({"A": 1, "B": 1})
        kept.begin(toy.state)
        for step in kept.propose(s, Streams(2).get("p")):
            toy.do(step)
        t += 1
        kept.record(SK.Step(s.id, s.roles), toy.state, t, settings=[{}, {}])
    assert s in kept.items, "a practised skill was forgotten"


def test_every_skill_records_where_it_came_from():
    sk, _ = _trained()
    s = sk.items[0]
    assert s.creator == 1 and s.origin_time > 0
    assert s.id[0] == "skill" and isinstance(s.id[2], int)
    assert all(c.examples for c in sk.effects(s))
    assert s.received_from is None and s.replaced == ()


# ------------------------------------------------- real physics, babbling
def _babble(acts, seed):
    """Babble with the shared harness (tests/v2/babble.py). Returns the
    skills, the stone-breaking ones, and the act at which the first of
    those was stored."""
    b = Babbler(seed).babble(acts)
    return b.sk, b.knapping(), b.first


def test_breaking_stone_into_sharp_pieces_is_found_not_given():
    """
    Real physics, perception and categories; acts chosen at random. The
    agent ends with a stored procedure that includes a blow and whose
    effect is the appearance of things of a kind of its own which, as the
    observer and only the observer can see, consists mostly of pieces
    broken off flint, sharp ones among them.
    """
    for seed in range(3):
        sk, knapping, first = _babble(2000, seed)
        assert knapping, (f"seed {seed}: {len(sk.items)} skills, none "
                          f"makes sharp things appear")
        assert all(len(s.steps) >= 2 for s in sk.items)


def test_skills_are_deterministic():
    def run():
        sk, knapping, first = _babble(600, 5)
        return first, [(s.id, s.steps) for s in sk.items]
    assert run() == run()


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
