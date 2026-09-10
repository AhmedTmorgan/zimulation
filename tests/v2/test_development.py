"""
Development and reproduction, verified on their own.

    python -m tests.v2.test_development
"""

from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.biology.params  # noqa: F401  (declares on import)
import zimulation.world.params  # noqa: F401
from zimulation.biology import development as D
from zimulation.biology import genetics as G
from zimulation.biology import physiology as P
from zimulation.biology import reproduction as REP
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.rng import Streams
from zimulation.core.scheduler import DAY, YEAR


def _adult(age=25.0, fat=None, mass=60.0):
    b = P.Body(mass_kg=mass, age_s=age * YEAR)
    if fat is not None:
        b.fat_kg = mass * fat
    return b


# ------------------------------------------------------------ development
def test_a_newborn_starts_at_birth_mass_and_grows_toward_its_genome():
    """The genome sets how large a body could grow; nourishment and time
    decide how much of that it does."""
    g = G.founder(Streams(4).get("g"))
    b = P.Body(mass_kg=R.get("birth_mass_kg"))
    assert abs(D.target_mass_kg(g, 0.0) - R.get("birth_mass_kg")) < 1e-9
    for _ in range(22 * 365):
        D.grow(b, g, DAY, nourished=1.0)
        P.feed(b, 0.05, 6.0e6)
        P.digest(b, DAY)
        b.age_s += DAY
    assert abs(b.mass_kg - g["adult_mass_kg"]) < 0.1 * g["adult_mass_kg"], (
        f"grew to {b.mass_kg:.1f} kg against a genetic target of "
        f"{g['adult_mass_kg']:.1f} kg")


def test_a_starved_child_does_not_grow():
    """Stunting is an outcome of scarcity, not a trait."""
    g = G.founder(Streams(4).get("g"))
    b = P.Body(mass_kg=R.get("birth_mass_kg"), age_s=5 * YEAR)
    before = b.mass_kg
    for _ in range(365):
        D.grow(b, g, DAY, nourished=0.0)
    assert b.mass_kg == before, "a child grew with no nourishment at all"


def test_growth_is_paid_for_from_the_energy_store():
    """Building tissue competes with staying warm for the same energy."""
    g = G.founder(Streams(4).get("g"))
    b = P.Body(mass_kg=R.get("birth_mass_kg"), age_s=10 * YEAR)
    fat_before = b.fat_kg
    spent = D.grow(b, g, 30 * DAY, nourished=1.0)
    assert spent > 0.0 and b.fat_kg < fat_before, \
        "growth cost nothing from the energy store"


def test_strength_rises_then_falls_with_no_switch_at_any_age():
    """
    No age at which an organism is switched on or off: strength is a
    continuous curve, and its largest step between neighbouring ages must
    be small.
    """
    g = G.founder(Streams(4).get("g"))
    ref = R.get("reference_body_mass_kg")
    vals = []
    for i in range(0, 900):
        b = P.Body(mass_kg=ref, age_s=(i / 10.0) * YEAR)
        vals.append(D.strength(g, b))
    peak = R.get("strength_peak_age_years")
    at = lambda age: vals[int(age * 10)]
    assert at(peak) > at(5.0) and at(peak) > at(80.0), \
        "strength did not peak in early adulthood"
    jumps = max(abs(vals[i + 1] - vals[i]) for i in range(len(vals) - 1))
    assert jumps < 0.05, f"strength jumped by {jumps:.3f} between ages"


def test_senses_decline_after_onset():
    onset = R.get("visual_acuity_decline_onset_years")
    assert D.sensory_acuity(onset - 5.0) == 1.0
    assert D.sensory_acuity(onset + 30.0) < 1.0


# ----------------------------------------------------------- reproduction
def test_immature_bodies_cannot_conceive_or_inseminate():
    child = _adult(age=8.0)
    assert REP.fecundity(child, REP.FEMALE) == 0.0
    s = Streams(1).get("r")
    father_child = _adult(age=10.0)
    g = G.founder(s)
    for _ in range(500):
        assert REP.inseminate(_adult(), REP.FEMALE, father_child, REP.MALE,
                              g, 0, s) is None, \
            "an immature body produced a conception"


def test_a_thin_body_stops_ovulating():
    """Famine lowers births before it raises deaths (Frisch & McArthur)."""
    fed = _adult(fat=0.20)
    thin = _adult(fat=R.get("fat_fraction_ovulation_low") - 0.01)
    assert REP.fecundity(fed, REP.FEMALE) > 0.0
    assert REP.fecundity(thin, REP.FEMALE) == 0.0


def test_nursing_suppresses_conception():
    """The birth-spacing mechanism of forager populations -- no decision."""
    b = _adult(fat=0.20)
    assert (REP.fecundity(b, REP.FEMALE, nursing_s_remaining=YEAR)
            < REP.fecundity(b, REP.FEMALE) * 0.5)


def test_fecundity_declines_and_ends_but_life_does_not():
    b = _adult(fat=0.20)
    young = REP.fecundity(b, REP.FEMALE)
    b.age_s = 44 * YEAR
    later = REP.fecundity(b, REP.FEMALE)
    b.age_s = R.get("fertility_end_years") * YEAR
    assert 0.0 < later < young
    assert REP.fecundity(b, REP.FEMALE) == 0.0
    assert b.alive, "reproductive senescence killed the body"


def test_conception_to_birth_carries_both_parents_forward():
    s = Streams(8).get("r")
    mg, fg = G.founder(s), G.founder(s)
    preg = REP.Pregnancy(fg, conceived_s=0)
    assert preg.due_s == R.get("gestation_days") * DAY
    assert REP.gestation_power_w(preg, DAY) > 0.0
    assert REP.gestation_power_w(preg, preg.due_s) == 0.0
    cg, cb, sex, nurse = REP.deliver(_adult(fat=0.2), mg, preg, s)
    assert cg.generation == max(mg.generation, fg.generation) + 1
    assert abs(cb.mass_kg - R.get("birth_mass_kg")) < 1e-9
    assert sex in (REP.MALE, REP.FEMALE)
    assert nurse > 0.0


def test_maternal_mortality_is_derived_not_declared():
    """
    Birth deaths come from tissue damage passing its threshold. The rate
    is implied by the complication rate and severity range, and it must
    land near the pre-modern figure of roughly one to two per hundred.
    Also checks the sex ratio from the same births.
    """
    s = Streams(12).get("births")
    mg, fg = G.founder(s), G.founder(s)
    n, dead, male = 20000, 0, 0
    for _ in range(n):
        mother = _adult(fat=R.get("fat_fraction_healthy"))
        _, _, sex, _ = REP.deliver(mother, mg, REP.Pregnancy(fg, 0), s)
        dead += (not mother.alive)
        male += (sex == REP.MALE)
    rate = dead / n
    assert 0.008 < rate < 0.025, f"maternal mortality {rate:.3%} per birth"
    frac = male / n
    assert abs(frac - R.get("sex_ratio_male_fraction")) < 0.012, \
        f"sex ratio {frac:.3f}"


def test_reproduction_models_no_motivation():
    """
    Section 28: sexual motivation and reproduction are separate systems.
    This module is only the second; it must not grow the first.
    """
    src = (ROOT / "zimulation" / "biology" / "reproduction.py").read_text(
        encoding="utf-8")
    names = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Name):
            names.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            names.add(node.attr.lower())
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.arg)):
            names.add(getattr(node, "name", getattr(node, "arg", "")).lower())
    for word in ("attract", "desire", "partner", "prefer", "orientation",
                 "choose", "choice", "pair"):
        hits = [n for n in names if word in n]
        assert not hits, f"reproduction models motivation: {hits}"


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
