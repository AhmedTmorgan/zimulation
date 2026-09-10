"""
Drives, remedies and places, verified.

The bodily signals here are synthetic but carry the real interoceptive
noise (interoception_sd), so the claims about learning what helps are
tested against the same noise an agent would feel.

    python -m tests.v2.test_goals
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.cognition.params  # noqa: F401  (declares on import)
from zimulation.cognition import goals as GO
from zimulation.cognition import places as PL
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.rng import Streams
from zimulation.core.scheduler import DAY

QUIET = {"hunger": 0.05, "thirst": 0.05, "cold": 0.0, "heat": 0.0,
         "pain": 0.0, "sleepiness": 0.05, "fullness": 0.5}


def _bout(goals, s, act, kind, effects, base=None, trace=None):
    """Record one bout whose true effect on each signal is `effects`, as
    felt through interoceptive noise."""
    sd = R.get("interoception_sd")
    base = dict(base or {"thirst": 0.5, "hunger": 0.4, "pain": 0.0})
    before = {k: v + s.gauss(0.0, sd) for k, v in base.items()}
    after = {k: v + effects.get(k, 0.0) + s.gauss(0.0, sd)
             for k, v in base.items()}
    return goals.record_bout(act, kind, before, after, trace_id=trace)


# ------------------------------------------------------------------ drives
def test_drives_are_bodily_signals_and_curiosity_only():
    """Section 13: no good, evil, religious or war drive."""
    assert set(GO.SIGNALS) | {GO.CURIOSITY} == {
        "hunger", "thirst", "cold", "heat", "pain", "rest", "curiosity"}


def test_the_most_pressing_signal_leads_and_curiosity_fills_the_quiet():
    g = GO.Goals(1)
    thirsty = dict(QUIET, thirst=0.7)
    assert g.most_urgent(thirsty)[0] == "thirst"
    cold = dict(QUIET, cold=0.9, thirst=0.7)
    assert g.most_urgent(cold)[0] == "cold"
    assert g.most_urgent(QUIET)[0] == GO.CURIOSITY


# --------------------------------------------------------------- remedies
def test_a_real_remedy_is_learned_after_a_few_bouts():
    """Drinking from kind W lowers thirst by 0.2 a bout; after a few bouts,
    felt through noise, it is a remedy and chewing stone is not."""
    g, s = GO.Goals(1), Streams(1).get("body")
    for i in range(4):
        _bout(g, s, "consume", "W", {"thirst": -0.2}, trace=i)
        _bout(g, s, "consume", "S", {}, trace=100 + i)
    found = g.remedies("thirst")
    assert found and found[0][:2] == ("consume", "W"), found
    assert all(k != "S" for _, k, _, _ in found)
    assert g.reliefs[("consume", "W")].examples == [0, 1, 2, 3]


def test_one_lucky_bout_is_not_a_remedy():
    g, s = GO.Goals(1), Streams(2).get("body")
    _bout(g, s, "consume", "W", {"thirst": -0.3})
    assert not g.remedies("thirst"), "a single bout was taken for a cure"


def test_false_remedies_are_rare_among_many_useless_acts():
    """
    Forty acts on kinds that do nothing, five bouts each, through the
    body's own noise. The confidence rule should admit few of them as
    remedies; this measures how few.
    """
    false = 0
    for seed in range(10):
        g, s = GO.Goals(1), Streams(seed).get("body")
        for k in range(40):
            for _ in range(5):
                _bout(g, s, "touch", k, {})
        false += len(g.remedies("thirst"))
    rate = false / 400
    assert rate < 0.05, f"{rate:.1%} of useless acts were taken for remedies"


def test_a_stronger_remedy_ranks_first():
    g, s = GO.Goals(1), Streams(3).get("body")
    for _ in range(5):
        _bout(g, s, "consume", "weak", {"thirst": -0.1})
        _bout(g, s, "consume", "strong", {"thirst": -0.3})
    found = g.remedies("thirst")
    assert [k for _, k, _, _ in found][:2] == ["strong", "weak"], found


# ------------------------------------------------------------------ places
def test_places_are_offered_nearest_first_and_empty_ones_are_not():
    p = PL.Places(1)
    p.note("W", (3, 4), 2, 0)
    p.note("W", (8, 8), 1, 0)
    assert p.where("W", (2, 2), 0) == [(3, 4), (8, 8)]
    p.note("W", (3, 4), 0, 10)
    assert p.where("W", (2, 2), 10) == [(8, 8)], "an emptied place was offered"
    assert p.where("unseen", (2, 2), 10) == []


def test_places_fade_as_episodic_memory_does():
    p = PL.Places(1)
    p.note("W", (1, 1), 1, 0)
    half = R.get("memory_half_life_days") * DAY
    assert p.where("W", (0, 0), 2 * half) == [(1, 1)]
    assert p.where("W", (0, 0), 10 * half) == [], "a place outlived memory"
    assert p.forget(10 * half) == 1 and not p.seen


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
