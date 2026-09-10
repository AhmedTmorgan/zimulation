"""
Heat, verified: warming, drying, cooling, and friction at a contact.

Each test exists because the first physics got what it checks wrong, and
each error was found by driving the world with a body instead of injecting
numbers: heat never left anything; a damp stick was rubbed to its ignition
point without losing a drop; a failed ignition spent its joules twice; and,
once cooling was added, heating a whole stick evenly would have made
friction ignition impossible.

    python -m tests.v2.test_thermal
"""

from __future__ import annotations

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
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.rng import Streams
from zimulation.core.scheduler import DAY, HOUR, YEAR
from zimulation.world import combustion as C
from zimulation.world import objects as O
from zimulation.world import thermal as TH
from zimulation.world.materials_data import MATERIALS
from zimulation.world.space import Terrain

AMB = 288.0
#: the stroke at which the arm's speed limit and its oscillation limit meet
BEST = R.get("rub_speed_m_s") / (2 * R.get("max_stroke_frequency_hz"))


def _thing(name, mass, length=0.3, moisture=0.0, temp=None):
    return O.Thing(None, MATERIALS[name], mass, length, temp, moisture)


def _setup(moisture=0.0, board_moisture=0.0, seed=2):
    terr = Terrain(12, Streams(seed).get("t"))
    g = G.founder(Streams(1).get("g"))
    a = PR.Actor(1, P.Body(mass_kg=60.0, age_s=27.0 * YEAR), g,
                 terr.at(5, 5))
    stick = O.Thing(None, MATERIALS["softwood"], 0.03, 0.3, None, moisture,
                    a.here)
    board = O.Thing(None, MATERIALS["hardwood"], 0.3, 0.3, None,
                    board_moisture, a.here)
    a.cell.things += [stick, board]
    PR.grasp(a, stick)
    return a, stick, board


# ------------------------------------------------------- energy accounts
def test_heating_a_damp_thing_conserves_energy():
    """Heat warms to boiling, drives water off at its latent heat, then
    warms further. Every joule is accounted for exactly once."""
    boil = R.get("boiling_point_water_k")
    latent = R.get("latent_heat_vaporisation_water")
    for joules in (500.0, 5000.0, 20000.0, 60000.0):
        t = _thing("softwood", 0.05, moisture=0.2)
        c0, t0 = TH.heat_capacity(t), t.temperature_k
        driven = TH.add_heat(t, joules)
        if driven == 0.0:
            used = c0 * (t.temperature_k - t0)
        else:
            used = (c0 * (boil - t0) + driven * latent
                    + TH.heat_capacity(t) * (t.temperature_k - boil))
        assert abs(used - joules) < 1e-6 * joules, \
            f"{joules} J in, {used:.3f} J accounted for"


def test_water_pins_a_thing_at_the_boiling_point():
    t = _thing("softwood", 0.05, moisture=0.2)
    boil = R.get("boiling_point_water_k")
    to_boil = TH.heat_capacity(t) * (boil - t.temperature_k)
    half = 0.5 * 0.2 * 0.05 * R.get("latent_heat_vaporisation_water")
    TH.add_heat(t, to_boil + half)
    assert abs(t.temperature_k - boil) < 1e-9, "it rose past boiling wet"
    assert 0.0 < t.moisture < 0.2


def test_a_failed_ignition_no_longer_spends_its_energy_twice():
    """The first version warmed the object with the joules and evaporated
    water with the same joules. Now they are spent exactly once."""
    boil = R.get("boiling_point_water_k")
    t = _thing("softwood", 0.05, moisture=0.2, temp=boil)
    water0 = t.moisture * t.mass_kg
    assert C.try_ignite(t, 1000.0, at_time=0) is None
    driven = water0 - t.moisture * t.mass_kg
    warmed = TH.heat_capacity(t) * (t.temperature_k - boil)
    total = driven * R.get("latent_heat_vaporisation_water") + warmed
    assert abs(total - 1000.0) < 1e-6, f"{total:.3f} J for 1000 J"
    assert t.temperature_k == boil, "it warmed past boiling while wet"


# ---------------------------------------------------------------- cooling
def test_a_hot_thing_cools_to_its_surroundings():
    """Nothing used to cool: heat put in stayed for ever."""
    hot = _thing("softwood", 0.03, temp=500.0)
    TH.exchange_heat(hot, AMB, 1.0)
    assert hot.temperature_k > 495.0, "a second in air cooled it too fast"
    TH.exchange_heat(hot, AMB, DAY)
    assert abs(hot.temperature_k - AMB) < 0.01, \
        f"still {hot.temperature_k:.2f} K after a day"
    cold = _thing("softwood", 0.03, temp=260.0)
    TH.exchange_heat(cold, AMB, DAY)
    assert abs(cold.temperature_k - AMB) < 0.01, "a cold thing stayed cold"


def test_stone_on_stone_stays_far_cooler_than_wood_on_wood():
    """
    Effusivity is why wood can glow under friction and stone cannot: the
    same work on the same contact raises wood several times higher.
    """
    wood = O.rub(_thing("softwood", 0.03), _thing("hardwood", 0.3),
                 60.0, 1.5, 30.0, Streams(1).get("r"))[2]
    stone = O.rub(_thing("flint", 0.17), _thing("granite", 0.9),
                  60.0, 1.5, 30.0, Streams(1).get("r"))[2]
    rise_wood = wood.peak_k - wood.start_k
    rise_stone = stone.peak_k - stone.start_k
    assert rise_wood > 4.0 * rise_stone, (rise_wood, rise_stone)


# --------------------------------------------- friction fire, by a body
def test_friction_fire_is_possible_but_takes_minutes_of_unbroken_effort():
    """
    A body, a dry softwood stick and a hardwood board. One minute of
    vigorous rubbing lights nothing; ten unbroken minutes leave a small
    smouldering ember. Nothing here injects energy.
    """
    for seed in range(5):
        a, stick, board = _setup(seed=seed)
        short = PR.rub(a, stick, board, 60.0, Streams(seed).get("r"),
                       stroke_m=BEST)
        assert not short.outcome["burning"], \
            f"a minute lit it (contact {short.outcome['contact_k']:.0f} K)"
        a, stick, board = _setup(seed=seed)
        fat0 = a.body.fat_kg
        bout = PR.rub(a, stick, board, 600.0, Streams(seed).get("r"),
                      stroke_m=BEST)
        assert bout.outcome["burning"], \
            f"ten minutes lit nothing ({bout.outcome['contact_k']:.0f} K)"
        ember = bout.outcome["ember"]
        assert 1e-5 < ember.mass_kg < 5e-3, \
            f"an ember of {ember.mass_kg * 1000:.2f} g"
        assert ember.burning.smouldering, "the ember was a flame"
        assert a.body.fat_kg < fat0, "ten minutes of rubbing cost nothing"


def test_pauses_throw_the_contact_heat_away():
    """Ten one-minute bouts an hour apart are as much work as ten unbroken
    minutes, and light nothing."""
    a, stick, board = _setup()
    s = Streams(0).get("r")
    for i in range(10):
        bout = PR.rub(a, stick, board, 60.0, s, now=i * HOUR,
                      stroke_m=BEST)
        assert not bout.outcome["burning"], f"bout {i} lit it"
        for th in (stick, board):
            TH.exchange_heat(th, a.cell.temperature_k, HOUR - 60.0)
    assert abs(stick.temperature_k - a.cell.temperature_k) < 1.0


def test_stroke_length_trades_speed_against_spread():
    """
    A short stroke is slow, because an arm cannot oscillate faster than a
    few times a second; a long one is fast but spreads the heat along its
    track. The contact gets hottest in between -- a trade-off nobody wrote
    down as a rule.
    """
    peaks = {}
    for stroke in (0.02, BEST, 0.5):
        a, stick, board = _setup()
        peaks[stroke] = PR.rub(a, stick, board, 120.0, Streams(4).get("r"),
                               stroke_m=stroke).outcome["contact_k"]
    assert peaks[BEST] > peaks[0.02] and peaks[BEST] > peaks[0.5], peaks


def test_damp_wood_is_slower_and_soaked_wood_never_catches():
    """
    Water in the heated layer must go before the contact can pass boiling,
    so damp wood gets less hot for the same work; fuel wetter than the
    extinction moisture never embers. The damp penalty here is milder than
    in practice -- see world.thermal.
    """
    peaks = {}
    for m in (0.0, 0.25):
        a, stick, board = _setup(moisture=m)
        peaks[m] = PR.rub(a, stick, board, 300.0, Streams(5).get("r"),
                          stroke_m=BEST).outcome["contact_k"]
    assert peaks[0.25] < peaks[0.0], peaks
    soaked = R.get("moisture_extinction") + 0.05
    a, stick, board = _setup(moisture=soaked, board_moisture=soaked)
    bout = PR.rub(a, stick, board, 1200.0, Streams(5).get("r"),
                  stroke_m=BEST)
    assert not bout.outcome["burning"], "soaked wood gave an ember"


def test_an_ember_left_alone_goes_out():
    a, stick, board = _setup()
    ember = PR.rub(a, stick, board, 600.0, Streams(1).get("r"),
                   stroke_m=BEST).outcome["ember"]
    assert ember is not None
    t = 0.0
    while ember.burning is not None and t < DAY:
        C.burn_step(ember, 10.0)
        t += 10.0
    assert ember.burning is None, "a lone ember smouldered for a day"
    assert t < HOUR, f"a lone ember lasted {t / 60:.0f} minutes"


def test_heat_is_deterministic():
    def run():
        a, stick, board = _setup()
        bout = PR.rub(a, stick, board, 600.0, Streams(3).get("r"),
                      stroke_m=BEST)
        return (round(bout.outcome["contact_k"], 9),
                round(stick.temperature_k, 9), round(stick.mass_kg, 12))
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
