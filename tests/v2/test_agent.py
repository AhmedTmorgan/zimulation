"""
The living agent, verified: an organism in a world, told nothing.

These tests run whole organisms in the engine -- body, senses, kinds,
skills, drives, places, planning -- in a warm scenario (20 degrees) where a
naked body can survive the nights. At 45 degrees in spring the first nights
kill, and that is tested too. The observer scores what the agents learned
by reading ground truth the agents never see.

    python -m tests.v2.test_agent
"""

from __future__ import annotations

import ast
import contextlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.behavior.params  # noqa: F401  (declares on import)
import zimulation.biology.params  # noqa: F401
import zimulation.cognition.params  # noqa: F401
import zimulation.world.params  # noqa: F401
from zimulation.cognition import goals as GO
from zimulation.core.engine import Engine
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.scheduler import DAY
from zimulation.world.materials_data import MATERIALS

WATER, TUBER = MATERIALS["water"], MATERIALS["tuber"]
SEEDS = range(8)
_RUNS = {}


@contextlib.contextmanager
def _setting(**values):
    old = {k: R.get(k) for k in values}
    for k, v in values.items():
        R.set(k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            R.set(k, v)


def _shore(e):
    """A water cell -- a pool within reach -- with the most land around."""
    t = e.terrain
    cells = [c for c in t.all_cells() if c.water_fraction > 0.0]
    return max(cells, key=lambda c: (sum(n.water_fraction == 0.0 for n in
                                         t.neighbours(c.x, c.y)), -c.x, -c.y))


def _mostly(agent, kind, material):
    """Observer only: whether the agent's kind is mostly of this material."""
    things = [th for th, k in agent.labels.values() if k == kind]
    return bool(things) and 2 * sum(th.material is material
                                    for th in things) > len(things)


def _population(learning, bias):
    """Eight lone adults beside water at 20 degrees for five days."""
    key = (learning, bias)
    if key not in _RUNS:
        runs = []
        with _setting(map_centre_latitude_degrees=20.0,
                      consummatory_bias=bias):
            for seed in SEEDS:
                e = Engine(seed, 16)
                a = e.add(_shore(e), 25.0, learning=learning)
                e.run(5 * DAY)
                runs.append((e, a))
        _RUNS[key] = runs
    return _RUNS[key]


# ------------------------------------------------------------- integrity
def test_the_agent_never_reads_the_world():
    """What the agent knows arrives through its senses. Its decision code
    touches no true property of anything -- not even a thing's mass."""
    tree = ast.parse((ROOT / "zimulation" / "behavior" / "arbitration.py")
                     .read_text(encoding="utf-8"))
    hidden = {"material", "mass_kg", "temperature_k", "moisture",
              "cutting_power", "burning", "integrity", "edge_quality",
              "nutritive_energy", "toxicity", "fat_kg", "water_kg",
              "core_temperature_k", "damage"}
    touched = {n.attr for n in ast.walk(tree)
               if isinstance(n, ast.Attribute)} & hidden
    assert not touched, f"arbitration reads the world: {sorted(touched)}"
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert "observer" not in (node.module or ""), node.module


def test_the_engine_is_deterministic():
    def run():
        with _setting(map_centre_latitude_degrees=20.0):
            e = Engine(3, 12)
            a = e.add(_shore(e), 25.0)
            e.run(DAY)
        return e.ledger.head, a.acts, a.actor.body.fat_kg
    assert run() == run()


def test_death_comes_from_physics_and_is_recorded():
    """At 45 degrees in spring the nights fall to a few degrees; a naked
    body cannot keep its core warm, and the record says what killed it."""
    e = Engine(1, 12)
    a = e.add(_shore(e), 25.0)
    e.run(3 * DAY)
    deaths = [ev for ev in e.ledger.events if ev.kind == "death"]
    assert not a.actor.body.alive and len(deaths) == 1
    assert deaths[0].physical["cause"] == "core_temperature_low"
    assert deaths[0].participants == (a.id,)
    assert e.ledger.verify() is None, "the hash chain is broken"


# ---------------------------------------------------------------- learning
def test_agents_discover_from_their_bodies_what_quiets_hunger_and_thirst():
    """
    No agent is told what food or water is. Among eight lone learners with
    no innate prior, some find that eating a kind of thing -- which the
    observer knows to be mostly tubers -- quiets hunger, and some that
    drinking from a kind the observer knows to be standing water quiets
    thirst. (Measured: three of eight each.)
    """
    agents = [a for _, a in _population(True, 0.0)]
    hunger = sum(any(act == "consume" and _mostly(a, k, TUBER)
                     for act, k, _, _ in a.goals.remedies("hunger"))
                 for a in agents)
    thirst = sum(any(act == "consume" and _mostly(a, k, WATER)
                     for act, k, _, _ in a.goals.remedies("thirst"))
                 for a in agents)
    assert hunger >= 2 and thirst >= 2, (hunger, thirst)


def test_an_innate_mouthing_prior_is_what_keeps_lone_agents_alive():
    """
    The counterfactual lever on consummatory_bias (declared, off in the
    baseline). Measured: five of eight lone learners live five days
    without it -- three die of thirst -- and all eight with it. Using what
    was learned did not by itself improve survival: agents identical but
    never using it lived six of eight.
    """
    without = sum(a.actor.body.alive for _, a in _population(True, 0.0))
    with_prior = sum(a.actor.body.alive for _, a in _population(True, 0.5))
    assert with_prior > without, (with_prior, without)


def test_every_remedy_and_death_is_on_the_record():
    """The ledger holds what an observer needs: each remedy an agent came
    to trust, each death with its cause, in an unbroken hash chain."""
    for e, a in _population(True, 0.0):
        assert e.ledger.verify() is None, "the hash chain is broken"
        recorded = {(ev.physical["drive"], ev.physical["kind"])
                    for ev in e.ledger.events if ev.kind == "remedy"}
        for drive in GO.SIGNALS:
            for act, kind, _, _ in a.goals.remedies(drive):
                assert (drive, repr(kind)) in recorded, (drive, act, kind)
        deaths = [ev for ev in e.ledger.events if ev.kind == "death"]
        if a.actor.body.alive:
            assert not deaths
        else:
            assert [d.physical["cause"] for d in deaths] == [
                a.actor.body.cause]


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
