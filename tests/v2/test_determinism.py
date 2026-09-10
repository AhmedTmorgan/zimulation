"""
Determinism and observer independence.

    version + scenario + parameters + seed  ->  identical event ledger

These tests exercise the core against a toy process rather than the real
world model, so they keep working while the world is being built and fail
loudly if the foundations drift.

    python -m tests.v2.test_determinism
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from zimulation.core.events import Ledger
from zimulation.core.rng import Streams
from zimulation.core.scheduler import (DAY, HOUR, PRIORITY_ACTION,
                                       PRIORITY_PHYSICS, Scheduler)


def _toy_run(seed, extra_stream=False, horizon=30 * DAY):
    """
    A small run that touches every piece of the core: two recurring
    processes at different scales, a stream per entity, and events written
    to a hash-chained ledger.
    """
    streams = Streams(seed)
    ledger = Ledger()
    sched = Scheduler()

    def slow():
        r = streams.get("weather").random()
        ledger.append(sched.now, "weather_shifted",
                      physical={"index": r}, stream="weather")

    def fast():
        for who in (1, 2, 3):
            s = streams.entity("move", who)
            if s.random() < 0.4:
                ledger.append(sched.now, "object_moved",
                              participants=(who,),
                              physical={"distance_m": s.uniform(0.0, 2.0)},
                              perceived_by=(who,), stream=f"move#{who}")

    sched.every(DAY, slow, PRIORITY_PHYSICS, "weather")
    sched.every(6 * HOUR, fast, PRIORITY_ACTION, "movement")

    if extra_stream:
        # A mechanism added later must not disturb existing streams.
        def unrelated():
            streams.get("newly_added_mechanism").random()
        sched.every(DAY, unrelated, PRIORITY_ACTION, "unrelated")

    sched.run_until(horizon)
    return ledger, streams, sched


def test_same_seed_same_history():
    """The basic contract. Byte-identical, not merely similar."""
    a, _, _ = _toy_run(4242)
    b, _, _ = _toy_run(4242)
    assert len(a) == len(b), f"event counts differ: {len(a)} vs {len(b)}"
    assert a.head == b.head, f"ledger heads differ: {a.head} vs {b.head}"
    for x, y in zip(a.events, b.events):
        assert x.as_dict() == y.as_dict(), f"first divergence at {x.event_id}"


def test_different_seed_different_history():
    """A seed that changes nothing would mean the seed is not being used."""
    a, _, _ = _toy_run(4242)
    b, _, _ = _toy_run(4243)
    assert a.head != b.head, "different seeds produced identical history"


def test_new_mechanism_does_not_disturb_existing_streams():
    """
    Stream independence, which is what makes counterfactual replay valid.

    Adding a mechanism that draws from its own stream must leave every
    other stream's sequence untouched. If it did not, no ablation could be
    attributed: removing a mechanism would shift all randomness downstream
    and the difference in outcome would be unreadable.
    """
    _, s1, _ = _toy_run(77)
    _, s2, _ = _toy_run(77, extra_stream=True)
    for name in ("weather", "move#1", "move#2", "move#3"):
        assert s1.get(name).draws == s2.get(name).draws, (
            f"stream {name} drew a different number of times when an "
            f"unrelated mechanism was added")


def test_ledger_detects_tampering():
    """History must not be quietly editable after the fact."""
    led, _, _ = _toy_run(9)
    assert led.verify() is None, "clean ledger reported as tampered"
    victim = led.events[len(led.events) // 2]
    victim.physical["index"] = 0.123456
    assert led.verify() == victim.event_id, "tampering went undetected"


def test_observer_cannot_change_history():
    """
    Contract section 5: changing a detector must never change history.

    Detectors are pure functions of the ledger. Running one -- including
    one that reads ground truth -- must leave the ledger head untouched.
    """
    from zimulation.observer.truth import GroundTruth

    led, _, _ = _toy_run(31)
    before_head, before_len = led.head, len(led)

    truth = GroundTruth("real_cause_of_weather", "orbital_forcing")

    def detector(ledger):
        seen = truth.reveal("zimulation.observer.classifiers")
        moved = [e for e in ledger.events if e.kind == "object_moved"]
        return len(moved), seen

    count, seen = detector(led)
    assert seen == "orbital_forcing"
    assert led.head == before_head, "a detector changed the ledger head"
    assert len(led) == before_len, "a detector appended to the ledger"

    # And running it twice gives the same answer -- no hidden state.
    assert detector(led)[0] == count


def test_scheduler_is_deterministic_under_ties():
    """
    Same-tick ordering must be fixed, or heap internals decide history.
    """
    def order_for(seed_of_scheduling):
        out = []
        s = Scheduler()
        items = [("a", PRIORITY_ACTION), ("b", PRIORITY_PHYSICS),
                 ("c", PRIORITY_ACTION), ("d", PRIORITY_PHYSICS)]
        if seed_of_scheduling:
            items = list(reversed(items))
        for label, pri in items:
            s.at(1000, (lambda l=label: out.append(l)), pri, label)
        s.run_until(2000)
        return out

    forward = order_for(False)
    assert forward == ["b", "d", "a", "c"], (
        f"priority did not order same-tick tasks: {forward}")
    # Scheduling order breaks ties within a priority, so reversing the
    # scheduling order must reverse the within-priority order -- and
    # nothing else.
    backward = order_for(True)
    assert backward == ["d", "b", "c", "a"], (
        f"tie-break was not scheduling order: {backward}")


def test_snapshot_restores_exactly():
    """
    Resumability: a restored run must continue identically, or long
    experiments cannot be checkpointed and no result is reproducible past
    the first crash.
    """
    streams = Streams(555)
    for _ in range(20):
        streams.get("a").random()
        streams.get("b").random()
    snap = streams.snapshot()

    tail_a = [streams.get("a").random() for _ in range(10)]

    restored = Streams(555)
    restored.restore(snap)
    tail_b = [restored.get("a").random() for _ in range(10)]

    assert tail_a == tail_b, "restored stream diverged from the original"
    assert restored.get("a").draws == streams.get("a").draws


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
