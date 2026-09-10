"""Perceptual grounding of the active open-ended agent.

The scientific baseline must not gain perfect object identity from Python.
An organism may classify what it currently sees or handles, but continuity
of an individual object is not supplied by the host runtime.

    python -m tests.v2.test_perceptual_grounding
"""

from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.behavior.params  # noqa: F401
import zimulation.biology.params  # noqa: F401
import zimulation.cognition.params  # noqa: F401
import zimulation.world.params  # noqa: F401
from zimulation.behavior.perceptual_agent import Agent
from zimulation.core.engine import Engine
from zimulation.world import objects as O
from zimulation.world.materials_data import MATERIALS

SRC = ROOT / "zimulation" / "behavior" / "perceptual_agent.py"


def _land(engine):
    return next(c for c in engine.terrain.all_cells() if c.water_fraction == 0.0)


def _thing(agent, name="flint", mass=0.1, length=0.1):
    t = O.Thing(None, MATERIALS[name], mass, length, position=agent.actor.here)
    agent.actor.cell.things.append(t)
    return t


def test_the_active_engine_uses_perceptual_grounding():
    e = Engine(1, 10)
    a = e.add(_land(e), 25.0)
    assert isinstance(a, Agent)


def test_active_cognition_never_calls_python_id_for_an_object():
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == "id"]
    assert not calls, "active cognition uses host-language object identity"


def test_a_nearby_thing_is_not_touched_for_free():
    e = Engine(2, 10)
    a = e.add(_land(e), 25.0)
    a._terrain = e.terrain
    stone = _thing(a)
    a.kind(stone, 0)
    seen_features = set().union(*(set(c.stats) for c in a.concepts.items))
    assert "apparent_size" in seen_features
    assert "hardness_felt" not in seen_features
    assert "edge_felt" not in seen_features


def test_handling_can_add_information_that_sight_did_not_supply():
    e = Engine(3, 10)
    a = e.add(_land(e), 25.0)
    a._terrain = e.terrain
    stone = _thing(a)
    a.kind(stone, 0)
    done = a._act("grasp", [stone], e.terrain, 1)
    assert done.done
    features = set().union(*(set(c.stats) for c in a.concepts.items))
    assert "hardness_felt" in features
    assert "edge_felt" in features


def test_reencounter_is_new_evidence_not_a_perfect_pointer_lookup():
    e = Engine(4, 10)
    a = e.add(_land(e), 25.0)
    a._terrain = e.terrain
    stone = _thing(a)
    a.kind(stone, 0)
    n0 = sum(c.n for c in a.concepts.items)
    a.kind(stone, 1)
    n1 = sum(c.n for c in a.concepts.items)
    assert n1 > n0, "re-encounter returned a cached host-object label"


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
