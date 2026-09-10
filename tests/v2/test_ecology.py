"""
Ecology, verified: matter appears where conditions allow, and follows them.

    python -m tests.v2.test_ecology
"""

from __future__ import annotations

import ast
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.behavior.params  # noqa: F401  (declares on import)
import zimulation.biology.params  # noqa: F401
import zimulation.cognition.params  # noqa: F401
import zimulation.world.params  # noqa: F401
from zimulation.behavior import primitives as PR
from zimulation.biology import genetics as G
from zimulation.biology import physiology as P
from zimulation.cognition import perception as PC
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.rng import Streams
from zimulation.core.scheduler import DAY, HOUR, YEAR
from zimulation.world import climate as CL
from zimulation.world import combustion as C
from zimulation.world import ecology as EC
from zimulation.world.materials_data import MATERIALS
from zimulation.world.space import Terrain

TUBER = MATERIALS["tuber"]


def _world(size=16, seed=3):
    terr = Terrain(size, Streams(seed).get("terrain"))
    return terr, EC.Ecology(terr, Streams(seed).get("ecology"))


def _tubers(cell):
    return [t for t in cell.things if t.material is TUBER]


def _stock(cell):
    return sum(t.mass_kg for t in _tubers(cell))


def _deepest(terr):
    return max((c for c in terr.all_cells() if c.water_fraction == 0.0),
               key=lambda c: c.soil_depth_m)


def _weather(cell, celsius, moisture):
    cell.temperature_k = 273.15 + celsius
    cell.moisture = moisture


def _dig(cell):
    cell.things = [t for t in cell.things if t.material is not TUBER]


# ----------------------------------------------------------------- plants
def test_plants_grow_only_where_soil_allows():
    terr, _ = _world()
    for c in terr.all_cells():
        if c.water_fraction > 0.0 or c.soil_depth_m <= 0.0:
            assert not _tubers(c), "tubers in water or on bare rock"
    deep = _deepest(terr)
    assert _tubers(deep), "the deepest soil grew nothing"
    assert _stock(deep) <= EC.tuber_capacity_kg(deep) + 1e-9


def test_winter_and_drought_halt_regrowth_and_spring_restores_it():
    terr, eco = _world()
    c = _deepest(terr)
    _dig(c)
    for _ in range(60):
        _weather(c, -2.0, 0.6)
        eco.update(DAY)
    assert not _tubers(c), "tubers grew in frozen ground"
    for _ in range(60):
        _weather(c, 15.0, 0.0)
        eco.update(DAY)
    assert not _tubers(c), "tubers grew in dry ground"
    for _ in range(90):
        _weather(c, 15.0, 0.6)
        eco.update(DAY)
    assert _tubers(c), "growing weather brought nothing back"


def test_a_dug_patch_recovers_over_weeks_not_days():
    terr, eco = _world()
    c = _deepest(terr)
    _dig(c)
    cap = EC.tuber_capacity_kg(c)
    for day in range(120):
        _weather(c, 15.0, 0.6)
        eco.update(DAY)
        if day == 9:
            assert _stock(c) < 0.5 * cap, "a dug patch was back in ten days"
    assert _stock(c) > 0.5 * cap, "four months of growing weather did not "
    "restore half the patch"


# -------------------------------------------------------- lying about
def test_rain_wets_fuel_and_the_air_dries_it_at_the_pace_of_its_thickness():
    """
    Three hours of rain soak a handful of grass until it cannot carry a
    flame, and barely touch a stick; three dry hours make the grass
    burnable again. A day of rain wets the stick through. The first version
    tied fuel to the ground's moisture, which stays saturated much of the
    year, and dry grass could burn on only a handful of days.
    """
    terr, eco = _world()
    c = _deepest(terr)
    key = (c.x, c.y)
    grass = eco._lay(c, MATERIALS["dry_grass"], R.get("grass_item_kg"),
                     R.get("grass_length_m"))
    stick = eco._lay(c, MATERIALS["softwood"], R.get("stick_item_kg"),
                     R.get("stick_length_m"))
    grass.moisture = stick.moisture = 0.02
    g_hold = MATERIALS["dry_grass"].moisture_capacity
    s_hold = MATERIALS["softwood"].moisture_capacity
    for _ in range(3):
        eco.update(HOUR, rain={key: 0.002})
    assert grass.moisture > 0.8 * g_hold, grass.moisture
    assert not C.can_sustain(grass), "rain-soaked grass could hold a flame"
    assert stick.moisture < 0.3 * s_hold, stick.moisture
    for _ in range(3):
        eco.update(HOUR)
    assert C.can_sustain(grass), "grass three dry hours after rain would "
    "not burn"
    for _ in range(24):
        eco.update(HOUR, rain={key: 0.002})
    assert stick.moisture > 0.5 * s_hold, stick.moisture


def _hourly(terr, eco, weather, days):
    """Step weather daily and ecology hourly, with rain falling in the
    first hours of each wet day. Yields after every hour."""
    rain_hours = int(R.get("rain_hours_per_wet_day"))
    for d in range(days):
        rain = CL.step_day(terr, d * DAY, weather)
        wet = any(v > 0.0 for v in rain.values())
        for h in range(24):
            eco.update(HOUR, rain=rain if wet and h < rain_hours else None)
            yield d, h


def test_rain_takes_some_hours_from_fire_but_not_most():
    """
    Between rains the air dries fine fuel to about 12%, below the moisture
    that smothers a flame; while rain falls, and for a little after, it
    cannot burn. Stepped hourly, the share of hours in which every handful
    of dry grass could carry a flame must fall short of all of them and
    stay well above half. (Stepped a day at a time the rain comes first and
    the drying after, so fuel is always seen dry at the day's end -- which
    is why this is measured by the hour.)
    """
    terr = Terrain(8, Streams(6).get("terrain"))
    eco = EC.Ecology(terr, Streams(6).get("ecology"))
    w = Streams(6).get("weather")
    grass = [t for c in terr.all_cells() for t in c.things
             if t.material is MATERIALS["dry_grass"]]
    hours = burnable = 0
    for _ in _hourly(terr, eco, w, 60):
        hours += 1
        burnable += all(C.can_sustain(g) for g in grass if g.mass_kg > 0.0)
    share = burnable / hours
    assert 0.80 < share < 0.99, f"grass could burn in {share:.1%} of hours"


def test_stones_lie_only_on_rocky_ground_and_flint_only_in_some_places():
    terr, eco = _world(size=30, seed=5)
    rocky = [c for c in terr.all_cells() if c.water_fraction == 0.0
             and c.rock_exposure > R.get("rock_exposure_threshold")]
    for c in terr.all_cells():
        stones = [t for t in c.things if t.material in (
            MATERIALS["granite"], MATERIALS["flint"])]
        if c not in rocky:
            assert not stones, "stones on unexposed ground"
        flint = [t for t in stones if t.material is MATERIALS["flint"]]
        if flint:
            assert (c.x, c.y) in eco.flint
    share = len(eco.flint) / max(1, len(rocky))
    assert abs(share - R.get("flint_cell_fraction")) < 0.1, share


def test_water_is_found_only_where_it_stands_and_quenches_thirst():
    terr, _ = _world()
    for c in terr.all_cells():
        pools = [t for t in c.things if t.material is MATERIALS["water"]]
        assert bool(pools) == (c.water_fraction > 0.0)
    shore = next(c for c in terr.all_cells() if c.water_fraction > 0.0)
    pool = next(t for t in shore.things if t.material is MATERIALS["water"])
    a = PR.Actor(1, P.Body(mass_kg=60.0, age_s=27.0 * YEAR),
                 G.founder(Streams(1).get("g")), shore)
    a.body.water_kg -= 3.0
    s = Streams(2).get("body")

    def thirst():
        return sum(PC.sense_body(a.body, 0, s).features["thirst"]
                   for _ in range(20)) / 20
    before = thirst()
    for _ in range(20):
        assert PR.consume(a, pool).done
    assert before - thirst() > 0.1, "drinking from standing water did nothing"


# ------------------------------------------------------------ integrity
def test_ecology_knows_nothing_of_minds():
    """Food is not placed for anyone: the module cannot even see an
    agent."""
    tree = ast.parse((ROOT / "zimulation" / "world" / "ecology.py")
                     .read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not any(part in mod for part in (
                "cognition", "behavior", "biology", "social", "culture")), mod


def _run_year(seed, days=30):
    terr = Terrain(12, Streams(seed).get("terrain"))
    eco = EC.Ecology(terr, Streams(seed).get("ecology"))
    weather = Streams(seed).get("weather")
    for d in range(days):
        eco.update(DAY, rain=CL.step_day(terr, d * DAY, weather))
    return terr


def test_ecology_is_deterministic():
    def picture(terr):
        return sorted((c.x, c.y, t.material.name, round(t.mass_kg, 9),
                       round(t.moisture, 9))
                      for c in terr.all_cells() for t in c.things)
    assert picture(_run_year(7)) == picture(_run_year(7))


def test_a_year_of_weather_and_growth_is_cheap():
    t0 = time.process_time()
    _run_year(8, days=365)
    spent = time.process_time() - t0
    assert spent < 10.0, f"a year on a 12x12 map took {spent:.1f} CPU s"


def test_weather_is_regional_and_seasons_reach_the_ground():
    """One day's warmth anomaly covers the whole map, which is a few
    kilometres across; and winter reaches the cells the plants read."""
    terr = Terrain(12, Streams(4).get("terrain"))
    w = Streams(4).get("weather")
    flat = [c for c in terr.all_cells() if abs(c.elevation_m) < 1e-9]
    lows = []
    for d in range(365):
        CL.step_day(terr, d * DAY, w)
        lows.append(min(c.temperature_k for c in terr.all_cells()))
    assert min(lows) < 273.15 < max(lows), "no freezing day at 45 degrees"
    if len(flat) >= 2:
        spread = max(c.temperature_k for c in flat) - min(
            c.temperature_k for c in flat)
        assert spread < 2.0, f"flat cells differ by {spread:.1f} K on a day"


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
