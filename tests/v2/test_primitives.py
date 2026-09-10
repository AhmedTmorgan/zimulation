"""
Sensorimotor primitives, verified: what a body can physically do.

The first test is the one that matters most, because it exposed a real
error. The world's fracture threshold used to require three hundred times
the energy of a human blow; the physics test passed by injecting energy
directly. This suite never injects energy. Everything goes through a body.

    python -m tests.v2.test_primitives
"""

from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.behavior.params  # noqa: F401  (declares on import)
import zimulation.biology.params  # noqa: F401
import zimulation.cognition.params  # noqa: F401
import zimulation.world.params  # noqa: F401
from zimulation.behavior import primitives as PR
from zimulation.biology import genetics as G
from zimulation.biology import physiology as P
from zimulation.core.rng import Streams
from zimulation.core.scheduler import YEAR
from zimulation.world import objects as O
from zimulation.world.materials_data import MATERIALS
from zimulation.world.space import Terrain

SRC = ROOT / "zimulation" / "behavior" / "primitives.py"


def _world(size=12, seed=2):
    return Terrain(size, Streams(seed).get("t"))


def _actor(terrain, age=27.0, mass=60.0, x=5, y=5):
    g = G.founder(Streams(1).get("g"))
    return PR.Actor(1, P.Body(mass_kg=mass, age_s=age * YEAR), g,
                    terrain.at(x, y))


def _thing(actor, name, mass, length=0.15):
    t = O.Thing(None, MATERIALS[name], mass, length, position=actor.here)
    actor.cell.things.append(t)
    return t


# ---------------------------------------------------------------- the ban
def test_no_primitive_is_a_civilisation_level_action():
    """Section 8 / 69: the repertoire is what a body does, not what a
    culture does. None of these may be a primitive."""
    banned = {"farm", "herd", "hunt", "forage", "gather", "cook", "build",
              "craft", "trade", "pray", "preach", "teach", "learn", "fight",
              "attack", "marry", "court", "worship", "rule", "govern",
              "domesticate", "heal", "tend", "steal", "knap", "kindle"}
    names = set(PR.PRIMITIVES)
    defined = {n.name for n in ast.walk(ast.parse(SRC.read_text(
        encoding="utf-8"))) if isinstance(n, ast.FunctionDef)}
    assert not (names & banned), f"semantic shortcuts: {names & banned}"
    assert not (defined & banned), f"semantic functions: {defined & banned}"
    assert len(PR.PRIMITIVES) == 22


def test_no_primitive_creates_combustion_by_fiat():
    """Only the combustion physics may set something burning."""
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) \
                else [node.target]
            for t in targets:
                assert not (isinstance(t, ast.Attribute)
                            and t.attr == "burning"), \
                    "a primitive sets .burning directly"
        if isinstance(node, ast.Call) and getattr(node.func, "attr",
                                                  "") == "Combusting":
            raise AssertionError("a primitive constructs combustion itself")


# ------------------------------------------------------ the knapping path
def test_a_human_arm_can_knap_flint():
    """
    A hammerstone in one hand, a flint core in the other, one blow. The
    energy comes from the arm, not from the test. Before the fracture
    threshold was corrected this failed: no arm could deliver 8,400 J.
    """
    terr = _world()
    best = 0.0
    for seed in range(5):
        a = _actor(terr)
        hammer = _thing(a, "granite", 0.8)
        core = _thing(a, "flint", 0.6)
        PR.grasp(a, hammer)
        PR.grasp(a, core)
        act = PR.strike(a, hammer, core, Streams(seed).get("k"))
        assert act.done and act.outcome["fragments"] > 0, (
            f"an adult's blow ({act.outcome['impact_j']:.0f} J) broke "
            f"nothing")
        best = max([best] + [t.cutting_power for t in a.cell.things])
    assert best > 0.2, f"best edge from five cores was {best:.2f}"


def test_a_small_child_cannot_knap_a_large_core():
    terr = _world()
    child = _actor(terr, age=6.0, mass=20.0)
    hammer = _thing(child, "granite", 0.8)
    core = _thing(child, "flint", 0.6)
    PR.grasp(child, hammer)
    PR.grasp(child, core)
    act = PR.strike(child, hammer, core, Streams(1).get("k"))
    assert act.outcome.get("fragments", 0) == 0, \
        "a six-year-old's blow fractured an adult-sized core"


def test_a_flake_cuts_what_a_lump_cannot_and_dulls_with_use():
    terr = _world()
    a = _actor(terr)
    flake = _thing(a, "flint", 0.05)
    flake.edge_quality = 0.8
    flake.edge_angle_rad = (3.141592653589793 / 2.0) * 0.2
    lump = _thing(a, "flint", 0.3)
    flesh = _thing(a, "muscle", 1.0)
    PR.grasp(a, flake)
    before = flake.edge_quality
    assert PR.separate(a, flake, flesh, Streams(1).get("c")).outcome[
        "separated"], "a sharp flake would not part flesh"
    assert flake.edge_quality < before, "cutting did not dull the edge"
    PR.release(a, flake)
    PR.grasp(a, lump)
    assert not PR.separate(a, lump, flesh, Streams(2).get("c")).outcome[
        "separated"], "a blunt lump parted flesh"


# ------------------------------------------------------ binding, eating
def test_fibre_binds_and_dry_grass_does_not():
    terr = _world()
    a = _actor(terr)
    fibre = _thing(a, "bark_fibre", 0.02, 0.8)
    grass = _thing(a, "dry_grass", 0.02, 0.8)
    stick = _thing(a, "hardwood", 0.4, 0.8)
    assert PR.combine(a, fibre, stick).outcome["combined"]
    assert fibre.attached_to is stick
    assert not PR.combine(a, grass, stick).outcome["combined"]


def test_eating_feeds_only_on_what_nourishes_and_can_be_bitten():
    terr = _world()
    a = _actor(terr)
    root = _thing(a, "tuber", 0.2)
    fat0 = a.body.fat_kg
    act = PR.consume(a, root)
    assert act.done and a.body.gut_energy_j > 0.0,         "the tuber never reached the stomach"
    assert a.body.fat_kg == fat0, "food reached the store undigested"
    P.digest(a.body, 6 * 3600.0)
    assert a.body.fat_kg > fat0, "a digested tuber fed nothing"
    rock = _thing(a, "flint", 0.2)
    assert not PR.consume(a, rock).done, "a jaw bit into flint"


# ---------------------------------------------------- limits of the body
def test_a_body_cannot_lift_what_is_too_heavy():
    terr = _world()
    a = _actor(terr)
    boulder = _thing(a, "granite", 200.0, 0.6)
    assert PR.grasp(a, boulder).outcome.get("refused") == "too heavy"


def test_two_hands_hold_two_things():
    terr = _world()
    a = _actor(terr)
    things = [_thing(a, "flint", 0.1) for _ in range(3)]
    assert PR.grasp(a, things[0]).done and PR.grasp(a, things[1]).done
    assert PR.grasp(a, things[2]).outcome.get("refused") == "hands full"


def test_moving_is_local_and_climbing_costs_more():
    terr = _world(size=20, seed=5)
    a = _actor(terr, x=10, y=10)
    assert PR.move(a, terr, terr.at(15, 15)).outcome.get("refused"), \
        "a body moved to a non-adjacent cell in one step"
    best = None
    for c in terr.all_cells():
        for nb in terr.neighbours(c.x, c.y):
            rise = nb.elevation_m - c.elevation_m
            if best is None or rise > best[2]:
                best = (c, nb, rise)
    low, high, _ = best
    up, down = _actor(terr, x=low.x, y=low.y), _actor(terr, x=high.x,
                                                     y=high.y)
    e_up = PR.move(up, terr, high).energy_j
    e_down = PR.move(down, terr, low).energy_j
    assert e_up > e_down, "climbing cost no more than descending"


# -------------------------------------------------------- heat and sound
def test_rubbing_warms_and_brief_rubbing_lights_nothing():
    terr = _world()
    a = _actor(terr)
    stick = _thing(a, "softwood", 0.03, 0.3)
    board = _thing(a, "hardwood", 0.3, 0.3)
    PR.grasp(a, stick)
    t0 = stick.temperature_k
    act = PR.rub(a, stick, board, 60.0, Streams(1).get("r"))
    assert stick.temperature_k > t0, "rubbing warmed nothing"
    assert not act.outcome["burning"], "one minute of rubbing lit a stick"
    stone = _thing(a, "flint", 0.3)
    other = _thing(a, "granite", 0.5)
    PR.release(a, stick)
    PR.grasp(a, stone)
    assert not PR.rub(a, stone, other, 3600.0,
                      Streams(2).get("r")).outcome["burning"], \
        "an hour of rubbing stone on stone lit it"


def test_a_signal_carries_a_token_and_no_meaning():
    terr = _world()
    a = _actor(terr, x=5, y=5)
    near = _actor(terr, x=5, y=5)
    far = _actor(terr, x=10, y=10)
    sig = PR.emit_signal(a, token=7, loudness=1.0).outcome["signal"]
    assert not hasattr(sig, "meaning") and sig.token == 7
    assert sig in PR.listen(near, terr, [sig]).outcome["heard"]
    assert sig not in PR.listen(far, terr, [sig]).outcome["heard"]


def test_every_act_that_does_work_costs_energy():
    terr = _world()
    a = _actor(terr)
    fat0 = a.body.fat_kg
    hammer = _thing(a, "granite", 0.8)
    core = _thing(a, "flint", 0.6)
    acts = [PR.grasp(a, hammer), PR.grasp(a, core),
            PR.strike(a, hammer, core, Streams(3).get("k")),
            PR.emit_signal(a, 1, 1.0)]
    for act in acts:
        assert act.done and act.duration_s > 0 and act.energy_j > 0.0, act
    assert a.body.fat_kg < fat0, "work was done and nothing was paid"


def test_acting_is_deterministic():
    def run():
        terr = _world()
        a = _actor(terr)
        hammer = _thing(a, "granite", 0.8)
        core = _thing(a, "flint", 0.6)
        PR.grasp(a, hammer)
        PR.grasp(a, core)
        PR.strike(a, hammer, core, Streams(9).get("k"))
        return sorted(round(t.mass_kg, 12) for t in a.cell.things)
    assert run() == run()


def test_a_body_can_drag_what_it_cannot_lift_but_not_without_limit():
    terr = _world()
    a = _actor(terr)
    log = _thing(a, "hardwood", 60.0, 2.0)
    assert PR.grasp(a, log).outcome.get("refused") == "too heavy"
    nxt = terr.neighbours(a.cell.x, a.cell.y)[0]
    act = PR.apply_force(a, log, terr, nxt)
    assert act.done and a.cell is nxt and log.position == (nxt.x, nxt.y)
    boulder = _thing(a, "granite", 500.0, 1.0)
    onward = terr.neighbours(a.cell.x, a.cell.y)[0]
    assert PR.apply_force(a, boulder, terr, onward).outcome.get(
        "refused") == "too heavy", "a body dragged half a tonne"


def test_a_light_stone_flies_farther_than_a_heavy_one():
    """The arm gives a throw roughly fixed energy, so heavier things leave
    the hand slower and land nearer."""
    terr = _world(size=40, seed=2)
    a = _actor(terr, x=5, y=5)
    far = terr.at(35, 5)
    light = _thing(a, "flint", 0.3)
    heavy = _thing(a, "granite", 3.0)
    PR.grasp(a, light)
    near_throw = PR.throw(a, light, terr, far)
    PR.grasp(a, heavy)
    heavy_throw = PR.throw(a, heavy, terr, far)
    assert near_throw.done and heavy_throw.done
    assert light not in a.held and heavy not in a.held
    assert near_throw.outcome["range_m"] > heavy_throw.outcome["range_m"]


def test_a_toxic_mouthful_does_harm():
    from zimulation.world.materials import Material
    terr = _world()
    a = _actor(terr)
    bitter = Material("bitter_root", 1050.0, 0.08, 0.25, 0.15, 0.2, 0.5,
                      3400.0, nutritive_energy=2.0e6, toxicity=0.8)
    root = O.Thing(None, bitter, 0.2, 0.1, position=a.here)
    a.cell.things.append(root)
    before = a.body.damage
    assert PR.consume(a, root).done
    assert a.body.damage > before, "a toxic mouthful did no harm"


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
