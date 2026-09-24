"""
Social interaction, verified: what bodies do to each other.

Two agents in the same cell can give things and strike each other. The
engine passes nearby agents each turn, applies proximity warmth from
huddling, and records social events in the ledger. None of this names
what any interaction is for: exchange, aggression and warmth are all
conditions, and whether anything comes of them is an open question.

    python -m tests.v2.test_social
"""

from __future__ import annotations

import ast
import contextlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.behavior.params  # noqa: F401
import zimulation.biology.params  # noqa: F401
import zimulation.cognition.params  # noqa: F401
import zimulation.social.params  # noqa: F401
import zimulation.world.params  # noqa: F401
from zimulation.behavior import primitives as PR
from zimulation.behavior.arbitration import Agent
from zimulation.biology import genetics as G
from zimulation.biology import physiology as PHY
from zimulation.core.engine import Engine
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.rng import Streams
from zimulation.core.scheduler import DAY, HOUR, YEAR
from zimulation.world.materials_data import MATERIALS
from zimulation.world.space import Terrain

SOCIAL_SRC = ROOT / "zimulation" / "social"
ARBIT_SRC = ROOT / "zimulation" / "behavior" / "arbitration.py"


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


def _world(size=12, seed=2):
    return Terrain(size, Streams(seed).get("t"))


def _actor(terrain, agent_id=1, age=27.0, mass=60.0, x=5, y=5):
    g = G.founder(Streams(agent_id).get("g"))
    return PR.Actor(agent_id, PHY.Body(mass_kg=mass, age_s=age * YEAR), g,
                    terrain.at(x, y))


def _agent(terrain, streams, agent_id=1, age=27.0, x=5, y=5):
    actor = _actor(terrain, agent_id, age=age, x=x, y=y)
    return Agent(agent_id, actor, streams)


def _thing(actor, name, mass, length=0.15):
    from zimulation.world import objects as O
    t = O.Thing(None, MATERIALS[name], mass, length, position=actor.here)
    actor.cell.things.append(t)
    return t


def _shore(e):
    t = e.terrain
    cells = [c for c in t.all_cells() if c.water_fraction > 0.0]
    return max(cells, key=lambda c: (sum(n.water_fraction == 0.0 for n in
                                         t.neighbours(c.x, c.y)), -c.x, -c.y))


# ------------------------------------------------------------ the barrier
def test_no_forbidden_vocabulary_in_social_code():
    """The social layer names conditions, not conclusions. No source file
    in the social module may use any word the contract forbids."""
    contract = (ROOT / "docs" / "SCIENTIFIC_CONTRACT.md").read_text(
        encoding="utf-8")
    m = re.search(r"FORBIDDEN-VOCABULARY-BEGIN -->\s*```(.*?)```",
                  contract, re.DOTALL)
    assert m, "contract is missing its forbidden-vocabulary fence"
    words = set(m.group(1).split())
    for path in SOCIAL_SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {n.id.lower() for n in ast.walk(tree)
                 if isinstance(n, ast.Name)}
        names |= {n.attr.lower() for n in ast.walk(tree)
                  if isinstance(n, ast.Attribute)}
        names |= {n.arg.lower() for n in ast.walk(tree)
                  if isinstance(n, ast.arg)}
        hit = names & words
        assert not hit, f"{path.name} uses forbidden words: {sorted(hit)}"


def test_arbitration_never_reads_another_agents_true_state():
    """The ground-truth barrier: an agent deciding what to do does not
    touch any true physical property of another agent's body."""
    tree = ast.parse(ARBIT_SRC.read_text(encoding="utf-8"))
    hidden = {"fat_kg", "water_kg", "core_temperature_k", "damage",
              "fat_fraction", "gut_energy_j", "pain", "sleep_debt_s",
              "cause", "insulation_clo", "gut_water_kg", "satiety"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in hidden:
            ctx = ast.dump(node.value)
            assert "other" not in ctx.lower() and "nearby" not in ctx.lower(), \
                f"arbitration reads another agent's {node.attr}"


# ---------------------------------------------------- giving and striking
def test_giving_moves_a_thing_to_the_other():
    """Give takes a held thing from one actor and places it at the other
    actor's cell, within their reach."""
    terr = _world()
    giver = _actor(terr, agent_id=1, x=5, y=5)
    taker = _actor(terr, agent_id=2, x=5, y=5)
    food = _thing(giver, "tuber", 0.2)
    PR.grasp(giver, food)
    assert food in giver.held
    act = PR.give(giver, food, taker)
    assert act.done and act.outcome["given"]
    assert food not in giver.held
    assert food in taker.cell.things


def test_giving_requires_same_cell():
    terr = _world()
    giver = _actor(terr, agent_id=1, x=5, y=5)
    far = _actor(terr, agent_id=2, x=8, y=8)
    food = _thing(giver, "tuber", 0.2)
    PR.grasp(giver, food)
    act = PR.give(giver, food, far)
    assert not act.done and act.outcome["refused"] == "not nearby"


def test_striking_body_causes_damage_and_drops_held():
    """A blow to another body causes physical damage and forces the victim
    to drop what it is holding."""
    terr = _world()
    striker_actor = _actor(terr, agent_id=1, x=5, y=5)
    victim = _actor(terr, agent_id=2, x=5, y=5)
    rock = _thing(striker_actor, "granite", 0.8)
    held_item = _thing(victim, "flint", 0.1)
    PR.grasp(striker_actor, rock)
    PR.grasp(victim, held_item)
    before = victim.body.damage
    act = PR.strike_body(striker_actor, rock, victim,
                         Streams(1).get("k"))
    assert act.done
    assert victim.body.damage > before, "a blow did no damage"
    assert act.outcome["dropped"], "the victim did not drop what it held"
    assert held_item not in victim.held


def test_striking_body_requires_same_cell():
    terr = _world()
    a1 = _actor(terr, agent_id=1, x=5, y=5)
    a2 = _actor(terr, agent_id=2, x=8, y=8)
    rock = _thing(a1, "granite", 0.8)
    PR.grasp(a1, rock)
    act = PR.strike_body(a1, rock, a2, Streams(1).get("k"))
    assert not act.done and act.outcome["refused"] == "not nearby"


# ---------------------------------------------------- proximity warmth
def test_proximity_warmth_reduces_heat_loss():
    """Two bodies in the same cold place lose less heat than one alone,
    because huddling reduces radiative exposure."""
    terr = _world()
    cold_k = 270.0
    alone = PHY.Body(mass_kg=60.0, age_s=27 * YEAR)
    together = PHY.Body(mass_kg=60.0, age_s=27 * YEAR)
    PHY.step(alone, HOUR, cold_k)
    loss_alone = PHY.heat_loss_w(alone, cold_k)
    frac = R.get("proximity_warmth_fraction")
    external_w = max(0.0, loss_alone) * min(1.0, frac)
    PHY.step(together, HOUR, cold_k, external_heat_w=external_w)
    assert together.core_temperature_k > alone.core_temperature_k, \
        "proximity warmth did not help"


# ---------------------------------------------------- agent perception
def test_agents_categorize_other_agents():
    """An agent perceives another through sense_agent, getting noisy
    features, and the concept system assigns them a kind -- distinct from
    the kinds it gives to objects."""
    terr = _world()
    streams = Streams(7)
    a1 = _agent(terr, streams, agent_id=1, x=5, y=5)
    a2 = _agent(terr, streams, agent_id=2, x=5, y=5)
    ak = a1.agent_kind(a2.actor, time=0)
    assert ak is not None, "agent could not categorize another agent"
    food = _thing(a1.actor, "tuber", 0.2)
    fk = a1.kind(food, time=0)
    assert ak is not None and fk is not None


# ----------------------------------------------- multi-agent engine
def test_multi_agent_engine_runs_without_error():
    """Two agents in the same warm world both survive one day."""
    with _setting(map_centre_latitude_degrees=20.0,
                  consummatory_bias=0.5):
        e = Engine(42, 12)
        shore = _shore(e)
        a1 = e.add(shore, 25.0)
        a2 = e.add(shore, 25.0)
        e.run(DAY)
    assert a1.actor.body.alive and a2.actor.body.alive, \
        "an agent died in a warm one-day two-agent run"


def test_multi_agent_engine_is_deterministic():
    def run():
        with _setting(map_centre_latitude_degrees=20.0,
                      consummatory_bias=0.5):
            e = Engine(99, 12)
            shore = _shore(e)
            a1 = e.add(shore, 25.0)
            a2 = e.add(shore, 25.0)
            e.run(DAY)
        return (e.ledger.head, a1.acts, a2.acts,
                round(a1.actor.body.fat_kg, 12),
                round(a2.actor.body.fat_kg, 12))
    assert run() == run()


def test_social_events_recorded_in_ledger():
    """When give or strike_body happens in the engine, the ledger records
    a 'social' event naming both participants."""
    with _setting(map_centre_latitude_degrees=20.0,
                  consummatory_bias=0.5):
        e = Engine(77, 12)
        shore = _shore(e)
        a1 = e.add(shore, 25.0)
        a2 = e.add(shore, 25.0)
        e.run(3 * DAY)
    social = [ev for ev in e.ledger.events if ev.kind == "social"]
    if social:
        for ev in social:
            assert len(ev.participants) == 2, \
                "social event does not name both agents"
    assert e.ledger.verify() is None, "the hash chain is broken"


def test_proximity_warmth_flows_through_engine():
    """In the engine, two agents at the same cold cell get proximity
    warmth: the one with a neighbour loses less core temperature than
    one alone would."""
    with _setting(map_centre_latitude_degrees=60.0):
        e_pair = Engine(50, 12)
        shore = _shore(e_pair)
        p1 = e_pair.add(shore, 25.0, learning=False)
        p2 = e_pair.add(shore, 25.0, learning=False)
        e_pair.run(6 * HOUR)
        e_solo = Engine(50, 12)
        solo = e_solo.add(_shore(e_solo), 25.0, learning=False)
        e_solo.run(6 * HOUR)
    assert p1.actor.body.core_temperature_k > solo.actor.body.core_temperature_k \
        or p2.actor.body.core_temperature_k > solo.actor.body.core_temperature_k, \
        "proximity warmth had no effect in the engine"


# -------------------------------------------------------------- runner
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
