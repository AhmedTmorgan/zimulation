"""Open-ended affordances: physical possibility must be behaviorally reachable."""

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
from zimulation.behavior import affordances as AF
from zimulation.behavior import primitives as PR
from zimulation.behavior.open_agent import Agent
from zimulation.biology import genetics as G
from zimulation.biology import physiology as P
from zimulation.core.engine import Engine
from zimulation.core.rng import Streams
from zimulation.core.scheduler import YEAR
from zimulation.world import objects as O
from zimulation.world.materials_data import MATERIALS
from zimulation.world.space import Terrain


def _actor():
    terrain = Terrain(12, Streams(7).get("terrain"))
    genome = G.founder(Streams(8).get("genome"))
    body = P.Body(mass_kg=60.0, age_s=25.0 * YEAR)
    actor = PR.Actor(1, body, genome, terrain.at(5, 5))
    return terrain, actor


def _thing(actor, material, mass=0.2, length=0.2):
    thing = O.Thing(None, MATERIALS[material], mass, length,
                    position=actor.here)
    actor.cell.things.append(thing)
    return thing


def test_affordances_do_not_peek_at_hidden_properties():
    src = (ROOT / "zimulation" / "behavior" / "affordances.py")
    tree = ast.parse(src.read_text(encoding="utf-8"))
    forbidden = {"material", "mass_kg", "temperature_k", "moisture",
                 "cutting_power", "burning", "integrity", "edge_quality",
                 "nutritive_energy", "toxicity"}
    touched = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not (touched & forbidden), touched & forbidden


def test_two_objects_make_blind_material_experiments_available():
    terrain, actor = _actor()
    stick = _thing(actor, "softwood", 0.03, 0.3)
    board = _thing(actor, "hardwood", 0.3, 0.3)
    PR.grasp(actor, stick)
    offered = AF.available(actor, terrain)
    for name in ("rub", "separate", "combine", "strike"):
        assert name in offered and offered[name], name
    assert any(a is stick and b is board for a, b in offered["rub"])


def test_open_agent_can_attempt_rubbing_without_knowing_its_effect():
    terrain, actor = _actor()
    stick = _thing(actor, "softwood", 0.03, 0.3)
    board = _thing(actor, "hardwood", 0.3, 0.3)
    PR.grasp(actor, stick)
    agent = Agent(1, actor, Streams(9))
    before = stick.temperature_k
    act = agent._act("rub", [stick, board], terrain, 0)
    assert act.done
    assert stick.temperature_k > before
    assert "rub" in {step.act for sk in agent.skills.items for step in sk.steps} \
        or agent.acts > 0


def test_throwing_and_force_application_are_attemptable_not_only_physical():
    terrain, actor = _actor()
    light = _thing(actor, "flint", 0.2)
    log = _thing(actor, "hardwood", 10.0, 1.0)
    PR.grasp(actor, light)
    offered = AF.available(actor, terrain)
    assert offered.get("throw"), "the body could throw but cognition could not try"
    assert offered.get("apply_force"), "the body could push but cognition could not try"

    agent = Agent(1, actor, Streams(10))
    destination = terrain.neighbours(actor.cell.x, actor.cell.y)[0]
    thrown = agent._act("throw", [light, destination], terrain, 0)
    assert thrown.done and light not in actor.held

    # Force application is checked independently after the throw because it
    # moves the actor together with the acted-on object.
    log.position = actor.here
    if log not in actor.cell.things:
        actor.cell.things.append(log)
    destination = terrain.neighbours(actor.cell.x, actor.cell.y)[0]
    pushed = agent._act("apply_force", [log, destination], terrain, 1)
    assert pushed.done


def test_spatial_attempts_are_not_falsely_stored_as_object_only_skills():
    terrain, actor = _actor()
    stone = _thing(actor, "flint", 0.2)
    PR.grasp(actor, stone)
    agent = Agent(1, actor, Streams(12))
    destination = terrain.neighbours(actor.cell.x, actor.cell.y)[0]
    assert agent._act("throw", [stone, destination], terrain, 0).done
    acts = {step.act for sk in agent.skills.items for step in sk.steps}
    assert "throw" not in acts, "destination was silently discarded from a skill"


def test_engine_uses_the_open_affordance_agent():
    e = Engine(11, 12)
    a = e.add(e.terrain.at(5, 5), 25.0)
    assert isinstance(a, Agent)


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
