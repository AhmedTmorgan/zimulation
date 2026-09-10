"""
The physical world, verified on its own.

Phase 2 of the migration says to build the world and check it before any
agent exists. That order matters: if the physics is only ever exercised
through agents, then every observation is confounded by whatever the
agents happen to do, and a broken world looks like an uninteresting
result.

Nothing in this file involves cognition, and nothing in it names a
conclusion. The assertions are about matter: what burns, what fractures,
what cuts, what goes out.

    python -m tests.v2.test_physics
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.world.params  # noqa: F401  (declares parameters on import)
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.rng import Streams
from zimulation.world import combustion as C
from zimulation.world import objects as O
from zimulation.world.materials_data import MATERIALS


def _thing(material_name, mass=1.0, length=0.5, moisture=0.0):
    return O.Thing(None, MATERIALS[material_name], mass, length,
                   moisture=moisture)


# ------------------------------------------------------------- combustion
def test_stone_never_ignites():
    """
    No amount of energy makes a rock burn. An agent may try; the world
    will not oblige, and that refusal is information available to anyone
    paying attention.
    """
    rock = _thing("flint", mass=0.5)
    assert C.ignition_energy(rock) is None
    assert C.try_ignite(rock, 1e12, at_time=0) is None
    assert not C.can_sustain(rock)


def test_fine_dry_fuel_ignites_far_more_easily_than_a_log():
    """
    The ordering that makes tinder tinder, without any concept of tinder.
    """
    grass = _thing("dry_grass", mass=0.02, length=0.3)
    log = _thing("hardwood", mass=4.0, length=1.0)
    e_grass = C.ignition_energy(grass)
    e_log = C.ignition_energy(log)
    assert e_grass < e_log / 50.0, (
        f"a wisp of dry grass ({e_grass:.0f} J) should be far cheaper to "
        f"ignite than a log ({e_log:.0f} J)")


def test_wet_fuel_costs_more_and_past_a_point_cannot_burn():
    dry = _thing("softwood", mass=0.3, moisture=0.05)
    damp = _thing("softwood", mass=0.3, moisture=0.25)
    assert C.ignition_energy(damp) > C.ignition_energy(dry)

    soaked = _thing("softwood", mass=0.3,
                    moisture=R.get("moisture_extinction") + 0.05)
    assert not C.can_sustain(soaked), "soaked fuel sustained a flame"
    assert C.try_ignite(soaked, 1e9, at_time=0) is None


def test_failed_attempts_accumulate_heat_and_dry_the_fuel():
    """
    Persistence pays -- in quick succession. The energy here arrives with
    no time between attempts; with time between them the object cools
    (world.thermal, tested there), so persistence has to be sustained.
    """
    stick = _thing("softwood", mass=0.05, length=0.4, moisture=0.20)
    start_t, start_m = stick.temperature_k, stick.moisture
    for _ in range(200):
        C.try_ignite(stick, 400.0, at_time=0)
    assert stick.temperature_k > start_t, "repeated energy did not warm it"
    assert stick.moisture < start_m, "repeated energy did not dry it"


def test_burning_consumes_mass_and_eventually_goes_out():
    """
    Combustion destroys what feeds it. This is why maintenance is a
    distinct stage from use: something must be added, or it ends.
    """
    grass = _thing("dry_grass", mass=0.05, length=0.4)
    lit = C.try_ignite(grass, C.ignition_energy(grass) * 1.1, at_time=0)
    assert lit is not None, "dry grass would not light"

    total_heat, out, steps = 0.0, False, 0
    while not out and steps < 100000:
        heat, out = C.burn_step(grass, dt_s=1.0)
        total_heat += heat
        steps += 1
    assert out, "the flame never went out despite consuming its fuel"
    assert grass.mass_kg <= 0.0
    assert total_heat > 0.0


def test_smouldering_outlasts_flame():
    """
    An ember survives being carried; a flame does not. Nothing in the
    model says an ember is useful -- only that it lasts longer.
    """
    def burn_out(smoulder):
        stick = _thing("hardwood", mass=0.2, length=0.5)
        C.try_ignite(stick, C.ignition_energy(stick) * 1.1, at_time=0)
        stick.burning.smouldering = smoulder
        steps = 0
        while stick.burning is not None and steps < 1000000:
            C.burn_step(stick, dt_s=1.0)
            steps += 1
        return steps

    assert burn_out(True) > burn_out(False) * 2, \
        "smouldering did not outlast flaming combustion"


def test_combustion_spreads_to_neighbours_but_not_across_a_gap():
    lit = _thing("dry_grass", mass=0.08, length=0.5)
    C.try_ignite(lit, C.ignition_energy(lit) * 1.2, at_time=0)

    near = _thing("dry_grass", mass=0.02, length=0.3)
    far = _thing("dry_grass", mass=0.02, length=0.3)
    reach = C.radiant_reach(1000.0)

    caught = C.spread(lit, [(near, reach * 0.1), (far, reach * 5.0)],
                      dt_s=60.0, at_time=1)
    assert far not in caught, "combustion jumped an impossible gap"


# -------------------------------------------------------------- mechanics
def test_striking_flint_yields_edges_and_granite_does_not():
    """
    The single most consequential physical fact in the early world, and
    nothing states it: flint is hard *and* brittle, so it fractures
    conchoidally into acute edges. Granite is hard and tough, so it does
    not. No technology tree, no recipe -- just material properties.
    """
    s = Streams(11).get("fracture")
    hammer = _thing("granite", mass=1.2, length=0.2)

    flint = _thing("flint", mass=0.6, length=0.15)
    energy = R.get("fracture_energy_scale") * flint.mass_kg * 3.0
    shards = O.strike(hammer, flint, energy, s)
    assert shards, "flint did not fracture under a heavy blow"
    assert max(f.cutting_power for f in shards) > 0.2, \
        "flint fragments had no usable edge"

    granite = _thing("granite", mass=0.6, length=0.15)
    assert not MATERIALS["granite"].brittle
    lumps = O.strike(hammer, granite, energy, s)
    assert not lumps, "granite fractured into fragments like flint"


def test_a_blunt_lump_does_not_cut():
    lump = _thing("flint", mass=0.4)
    assert lump.cutting_power == 0.0, \
        "an unworked lump had cutting power before any edge existed"


def test_sustained_rubbing_heats_and_a_single_stroke_does_not():
    """
    Originating combustion by friction must be hard but possible. If one
    stroke sufficed it would be a button; if a thousand did not, the path
    would be closed and the experiment could not ask the question.
    """
    s = Streams(3).get("friction")

    one = _thing("softwood", mass=0.03, length=0.3)
    before = one.temperature_k
    O.rub(one, _thing("hardwood", mass=0.3), 60.0, 1.5, 1.0, s)
    assert one.temperature_k - before < 50.0, "one stroke did too much"

    many = _thing("softwood", mass=0.03, length=0.3)
    for _ in range(600):
        O.rub(many, _thing("hardwood", mass=0.3), 60.0, 1.5, 1.0, s)
    assert many.temperature_k > one.temperature_k, \
        "sustained rubbing did not accumulate heat"


def test_thin_things_burn_faster_than_thick_ones_of_equal_mass():
    thin = _thing("hardwood", mass=0.2, length=2.0)
    thick = _thing("hardwood", mass=0.2, length=0.1)
    assert thin.surface_area_m2 > thick.surface_area_m2

    def lifetime(o):
        C.try_ignite(o, C.ignition_energy(o) * 1.2, at_time=0)
        n = 0
        while o.burning is not None and n < 1000000:
            C.burn_step(o, dt_s=1.0)
            n += 1
        return n

    assert lifetime(thin) < lifetime(thick), \
        "a thin stick did not burn out faster than a compact one"


# ------------------------------------------------------------------ space
def _terrain(size=20, seed=3):
    from zimulation.world.space import Terrain
    return Terrain(size, Streams(seed).get("terrain"))


def test_terrain_has_places_that_differ():
    """
    If every cell were alike, moving would be pointless and local
    knowledge would be complete knowledge. Both would quietly settle
    questions the experiment is meant to ask.
    """
    t = _terrain()
    cells = t.all_cells()
    elevations = [c.elevation_m for c in cells]
    assert max(elevations) - min(elevations) > 50.0, "the map is flat"
    assert any(c.water_fraction > 0.0 for c in cells), "no water anywhere"
    assert any(c.water_fraction == 0.0 for c in cells), "no dry land"
    assert any(c.rock_exposure > 0.3 for c in cells),         "no exposed rock, so knappable stone could never be found"


def test_sight_is_limited_and_ridges_block_it():
    from zimulation.world import space as SP
    t = _terrain(size=40)
    a = t.at(2, 2)
    far = t.at(38, 38)
    assert not SP.visible_from(t, a, far) or         t.distance_m(a, far) <= R.get("visibility_clear_day"),         "saw something beyond the horizon"
    assert SP.visible_from(t, a, a), "a cell cannot see itself"


def test_sound_carries_less_far_than_sight():
    """
    The asymmetry that makes signalling at a distance worth anything: a
    call can reach someone who cannot see you.
    """
    assert R.get("sound_audible_distance") < R.get("visibility_clear_day")


def test_climbing_costs_more_than_walking_level():
    from zimulation.world import space as SP
    t = _terrain()
    cells = t.all_cells()
    low = min(cells, key=lambda c: c.elevation_m)
    high = max(cells, key=lambda c: c.elevation_m)
    up = SP.travel_cost_s(t, low, high, 1.2)
    down = SP.travel_cost_s(t, high, low, 1.2)
    assert up > down, "climbing cost no more than descending"


# ---------------------------------------------------------------- climate
def test_seasons_follow_from_axial_tilt():
    """
    Summer is warmer than winter because the sun is higher, and that
    follows from the tilt alone. Nothing writes a season into the world.
    """
    from zimulation.world import climate as CL
    from zimulation.core.scheduler import DAY
    t = _terrain()
    cell = t.at(10, 10)
    lat = CL.latitude_of(t, cell)
    noon = DAY // 4

    def at_day(d):
        return CL.temperature_at(d * DAY + noon, cell, lat)

    summer, winter = at_day(91), at_day(273)
    equinox = at_day(0)
    assert summer > equinox > winter, (
        f"seasons out of order: summer {summer:.1f} equinox {equinox:.1f} "
        f"winter {winter:.1f}")


def test_higher_latitude_is_colder():
    from zimulation.world import climate as CL
    from zimulation.core.scheduler import DAY
    t = _terrain()
    south, north = t.at(10, 0), t.at(10, t.size - 1)
    noon = 91 * DAY + DAY // 4
    ts = CL.temperature_at(noon, south, CL.latitude_of(t, south))
    tn = CL.temperature_at(noon, north, CL.latitude_of(t, north))
    assert tn < ts, "the northern edge was not colder than the southern"


def test_night_is_colder_than_day():
    from zimulation.world import climate as CL
    from zimulation.core.scheduler import DAY
    t = _terrain()
    cell = t.at(10, 10)
    lat = CL.latitude_of(t, cell)
    day = CL.temperature_at(91 * DAY + DAY // 4, cell, lat)
    night = CL.temperature_at(91 * DAY + 3 * DAY // 4, cell, lat)
    assert night < day - 5.0, "no meaningful day-night swing"


def test_elevation_cools_by_lapse_rate():
    from zimulation.world import climate as CL
    from zimulation.core.scheduler import DAY
    t = _terrain()
    cells = [c for c in t.all_cells() if c.water_fraction == 0.0]
    low = min(cells, key=lambda c: c.elevation_m)
    high = max(cells, key=lambda c: c.elevation_m)
    lat = CL.latitude_of(t, low)
    tick = 91 * DAY + DAY // 4
    assert (CL.temperature_at(tick, high, lat)
            < CL.temperature_at(tick, low, lat)), "height did not cool"


def test_rain_is_episodic_and_wets_the_ground():
    """
    Rain must fall in bursts, not as a constant trickle. Continuous
    drizzle would keep fuel permanently damp and quietly close off
    combustion; dry spells are what make it possible at all.
    """
    from zimulation.world import climate as CL
    from zimulation.core.scheduler import DAY
    t = _terrain()
    cell = t.at(10, 10)
    lat = CL.latitude_of(t, cell)
    s = Streams(9).get("rain")
    days = [CL.precipitation(d * DAY, cell, lat, s) for d in range(365)]
    wet = sum(1 for r in days if r > 0.0)
    assert 0 < wet < 300, f"{wet} wet days of 365 is not episodic"

    cell.moisture = 0.1
    before = cell.moisture
    CL.update_moisture(cell, 0.02, 288.0, DAY)
    assert cell.moisture > before, "rain did not wet the ground"

    for _ in range(60):
        CL.update_moisture(cell, 0.0, 300.0, DAY)
    assert cell.moisture < 0.2, "warm dry weather never dried the ground"


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
