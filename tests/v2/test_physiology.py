"""
The body, verified on its own.

Phase 3 builds a biological organism with no culture and no cognition.
What has to be true before anything is built on top:

  - death comes from physiology, never from an age
  - cold is expensive in energy before it is dangerous in temperature
  - external heat substitutes for metabolic heat, without the model
    saying anywhere that heat is desirable
  - old bodies fail more readily than young ones purely because repair
    declines

    python -m tests.v2.test_physiology
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.biology.params  # noqa: F401  (declares on import)
import zimulation.cognition.params  # noqa: F401
import zimulation.world.params  # noqa: F401
from zimulation.biology import physiology as P
from zimulation.cognition import perception as PC
from zimulation.core.rng import Streams
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.scheduler import DAY, HOUR, YEAR

WARM = R.get("thermal_comfort_ambient_k")
COLD = 268.0          # -5 C
FREEZING = 253.0      # -20 C


def test_a_fed_body_in_comfort_stays_alive_indefinitely():
    """
    The baseline must not kill by itself. If a body dies while warm and
    fed, every later result is confounded by a leak in the accounting.
    """
    b = P.Body()
    for _ in range(365):
        unmet = P.step(b, DAY, WARM, activity=1.2)
        # feed it back what a day costs, as an organism eating would
        P.feed(b, 2.0, 6.0e6, water_fraction=0.6)
        b.water_kg = b.mass_kg * R.get("water_fraction_of_mass")
        assert unmet == 0.0
    assert b.alive, f"a warm, fed body died of {b.cause}"


def test_cold_costs_energy_long_before_it_lowers_core_temperature():
    """
    The central claim of the thermal model. Cold shows up first as a food
    problem: shivering burns fuel to hold the line. Only when shivering
    cannot keep up does the core start to fall.

    This is what could make external heat matter to an organism -- and
    nothing in the model says it does.
    """
    warm, cold = P.Body(), P.Body()
    warm_spend = P.thermoregulate(warm, WARM, HOUR)
    cold_spend = P.thermoregulate(cold, COLD, HOUR)

    assert cold_spend > warm_spend * 5.0, (
        f"an hour at -5 C cost {cold_spend:.0f} J against {warm_spend:.0f} J "
        f"in comfort; cold is not expensive enough to matter")

    # Shivering does not hold the line for an unclothed body at -5 C -- no
    # real one does either -- but it must slow the fall substantially.
    # Without any metabolic response the core would drop by the full heat
    # deficit; with it, considerably less.
    drop = R.get("core_temperature_k") - cold.core_temperature_k
    naive = (P.heat_loss_w(P.Body(), COLD) * HOUR
             / R.get("body_heat_capacity_j_per_k"))
    assert drop < naive * 0.5, (
        f"core fell {drop:.2f} K against {naive:.2f} K with no metabolic "
        f"response at all; shivering is barely doing anything")
    assert drop > 0.0, "an unclothed body at -5 C lost no core heat at all"


def test_severe_cold_eventually_wins():
    """
    Shivering has a ceiling. Past it the core falls and the organism dies
    of hypothermia -- an outcome of heat flow, not a rule about weather.
    """
    b = P.Body()
    for _ in range(48):
        P.step(b, HOUR, FREEZING, activity=1.0)
        if not b.alive:
            break
    assert not b.alive, "-20 C for two days was survived bare and inactive"
    assert b.cause == "core_temperature_low", f"died of {b.cause} instead"


def test_external_heat_substitutes_for_burning_your_own_fuel():
    """
    A body beside a heat source spends less of itself. The module has no
    concept of a heat source; it takes watts and does arithmetic.
    """
    alone = P.Body()
    beside = P.Body()
    spent_alone = P.thermoregulate(alone, COLD, HOUR)
    spent_beside = P.thermoregulate(beside, COLD, HOUR, external_heat_w=150.0)
    assert spent_beside < spent_alone, \
        "external heat did not reduce metabolic expenditure"


def test_insulation_reduces_the_cost_of_cold():
    """
    Anything that raises insulation makes cold cheaper. Nothing here knows
    what clothing or shelter is; an object over a body raises a number.
    """
    bare = P.Body()
    covered = P.Body()
    covered.insulation_clo = R.get("bare_skin_insulation_clo") * 6.0
    assert (P.thermoregulate(covered, COLD, HOUR)
            < P.thermoregulate(bare, COLD, HOUR)), \
        "insulation did not reduce the cost of staying warm"


def test_starvation_is_a_process_that_ends_in_death():
    b = P.Body()
    days = 0
    while b.alive and days < 400:
        P.step(b, DAY, WARM, activity=1.4)
        b.water_kg = b.mass_kg * R.get("water_fraction_of_mass")
        days += 1
    assert not b.alive, "an unfed body never starved"
    assert b.cause == "energy_exhausted", f"died of {b.cause} instead"
    assert 20 < days < 200, (
        f"starvation took {days} days, which is not a plausible span for a "
        f"body with this much stored energy")


def test_thirst_kills_faster_than_hunger():
    """
    An ordering with consequences: water is the more urgent constraint, so
    an organism that solves food but not water still dies.
    """
    def survive(with_water):
        b = P.Body()
        d = 0
        while b.alive and d < 400:
            P.step(b, DAY, WARM, activity=1.2)
            P.feed(b, 2.0, 6.0e6)
            if with_water:
                b.water_kg = b.mass_kg * R.get("water_fraction_of_mass")
            d += 1
        return d, b.cause

    dry_days, dry_cause = survive(False)
    assert dry_cause == "water_exhausted", f"expected thirst, got {dry_cause}"
    assert dry_days < 30, f"survived {dry_days} days without any water"


def test_no_maximum_age_exists_anywhere():
    """
    The rule Zimulation 1 broke for a long time. A body kept warm, fed and
    watered must not die on a schedule -- only from something physical.
    """
    b = P.Body()
    for _ in range(120):
        for _ in range(365):
            P.step(b, DAY, WARM, activity=1.0)
            P.feed(b, 2.0, 6.0e6)
            b.water_kg = b.mass_kg * R.get("water_fraction_of_mass")
        if not b.alive:
            break
    assert b.alive, (
        f"a perfectly maintained body died of {b.cause} at "
        f"{b.age_years:.0f} years; something is enforcing a lifespan")


def test_repair_declines_with_age_so_old_bodies_carry_damage():
    """
    The only reason age matters. Same insult, different outcome, because
    an older body clears it more slowly.
    """
    young = P.Body(age_s=20 * YEAR)
    old = P.Body(age_s=70 * YEAR)
    assert (P.repair_capacity(old, 1.0)
            < P.repair_capacity(young, 1.0) * 0.5), \
        "repair capacity barely fell across fifty years"

    for b in (young, old):
        P.injure(b, 0.4)
    for _ in range(30):
        P.repair(young, DAY, 1.0)
        P.repair(old, DAY, 1.0)
    assert old.damage > young.damage, \
        "the older body did not retain more damage after the same injury"


def test_starving_bodies_barely_repair():
    fed = P.Body()
    starving = P.Body()
    assert (P.repair_capacity(starving, 0.05)
            < P.repair_capacity(fed, 1.0) * 0.2), \
        "nourishment did not gate repair"


def test_pain_and_sleep_debt_degrade_performance():
    """
    Bounded rationality has a physical floor: a body in pain and short of
    sleep performs worse. Nothing calls this foolishness.
    """
    rested = P.Body()
    assert rested.impairment < 0.05

    tired = P.Body()
    P.accumulate_sleep_debt(tired, 4 * DAY, sleeping=False)
    P.injure(tired, 0.3)
    assert tired.impairment > 0.3, \
        "four days awake and injured left performance intact"

    P.accumulate_sleep_debt(tired, 3 * DAY, sleeping=True)
    assert tired.sleep_debt_s == 0.0, "sleeping did not discharge the debt"


def test_bigger_bodies_cost_more_but_less_than_proportionally():
    """Kleiber, which is why body size is a real trade-off."""
    small = P.Body(mass_kg=45.0)
    large = P.Body(mass_kg=90.0)
    rs, rl = P.resting_rate_w(small), P.resting_rate_w(large)
    assert rl > rs, "a larger body did not cost more to run"
    assert rl < rs * 2.0, \
        "metabolic cost scaled linearly with mass; Kleiber says otherwise"


# -------------------------------------------------------------- the gut
def test_a_meal_reaches_the_store_over_hours_not_at_once():
    b = P.Body()
    fat0 = b.fat_kg
    P.feed(b, 1.0, 3.2e6, water_fraction=0.6)
    assert b.fat_kg == fat0 and b.gut_energy_j == 3.2e6
    P.digest(b, R.get("gastric_half_time_food_s"))
    assert abs(b.gut_energy_j - 1.6e6) < 1.0, "a half-time was not a half"
    P.digest(b, 12 * 3600.0)
    assert b.gut_energy_j < 0.01 * 3.2e6
    gained = (b.fat_kg - fat0) * R.get("energy_store_capacity_j_per_kg")
    # Emptying is exponential and never quite finishes; what the claim
    # rests on is that nothing is lost or made: absorbed plus still in the
    # stomach is exactly what was eaten.
    assert abs(gained + b.gut_energy_j - 3.2e6) < 1.0,         f"{gained:.0f} J absorbed and {b.gut_energy_j:.0f} J in the gut"


def test_a_full_stomach_takes_no_more():
    b = P.Body()
    took = P.feed(b, 10.0, 3.2e6)
    assert abs(b.gut_kg - b.stomach_capacity_kg) < 1e-9
    assert abs(took - b.stomach_capacity_kg * 3.2e6) < 1.0
    assert P.feed(b, 1.0, 3.2e6) == 0.0


def _felt(b, s, signal):
    return sum(PC.sense_body(b, 0, s).features[signal]
               for _ in range(20)) / 20


def test_drinking_quenches_thirst_before_the_water_is_absorbed():
    """Thirst falls as water is swallowed, as it does in people, well
    before the water reaches the body. Twenty readings are averaged,
    because the signal itself is noisy."""
    s = Streams(2).get("body")
    b = P.Body()
    b.water_kg -= 3.0
    before = _felt(b, s, "thirst")
    P.feed(b, 1.5, 0.0, water_fraction=1.0)
    after = _felt(b, s, "thirst")
    assert before - after > 0.2, (before, after)
    w0 = b.water_kg
    P.digest(b, 3600.0)
    assert b.water_kg - w0 > 1.3, "the water was never absorbed"


def test_hunger_returns_hours_after_a_meal():
    """An empty stomach is felt as hunger within hours though the
    reserves have hardly changed -- the fast signal that makes meals
    recur."""
    s = Streams(3).get("body")
    b = P.Body()
    P.feed(b, b.stomach_capacity_kg, 3.2e6, water_fraction=0.6)
    sated = _felt(b, s, "hunger")
    P.step(b, 6 * 3600.0, WARM)
    later = _felt(b, s, "hunger")
    assert later - sated > 0.25, (sated, later)


# ------------------------------------------------------------ hypothermia
def _fed_hours(ambient_k, hours):
    """A bare adult, fed and watered three times a day, at a constant
    temperature. Returns the body and the hours it lived."""
    b, h = P.Body(), 0
    while b.alive and h < hours:
        if h % 8 == 0:
            P.feed(b, 0.9, 3.2e6, water_fraction=0.6)
            P.feed(b, 0.5, 0.0, water_fraction=1.0)
        P.step(b, HOUR, ambient_k)
        h += 1
    return b, h


def test_shivering_fails_as_the_core_cools():
    """Full shivering down to about 35 C core, none by about 30 C, and a
    body that cold can no longer act (Danzl & Pozos 1994)."""
    b = P.Body()
    assert P.shivering_capacity(b) == 1.0 and b.impairment < 0.1
    b.core_temperature_k = R.get("shivering_stop_core_k")
    assert P.shivering_capacity(b) == 0.0
    assert b.impairment == 1.0, "a body at a 30 C core could still act"


def test_freezing_air_kills_a_bare_fed_body_within_a_day():
    """
    At -1 C a bare adult cannot shiver enough; its core falls, shivering
    fails and hypothermia runs away -- in hours. The first version let a
    body shiver at full strength at any core temperature, and a bare, fed,
    watered adult lived seventeen days at -1 C, dying at last of hunger.
    """
    b, hours = _fed_hours(272.15, 72)
    assert not b.alive and b.cause == "core_temperature_low", b.cause
    assert hours <= 24, f"a bare body survived {hours} h at -1 C"


def test_moderate_cold_is_a_food_problem_not_a_temperature_one():
    """At 10 C shivering still keeps up: the core holds and the cost is
    paid in fuel."""
    fat0 = P.Body().fat_kg
    b, _ = _fed_hours(283.15, 72)
    assert b.alive and b.core_temperature_k > R.get("shivering_full_core_k")
    assert b.fat_kg < fat0, "three days at 10 C cost nothing"


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
