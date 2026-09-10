"""
Causal inference, verified against worlds whose mechanism is known.

Each test builds a small world with a sealed true mechanism, lets a
learner watch or act in it, and checks the learner's verdict. The learner
never sees the mechanism; the test, playing observer, does.

    python -m tests.v2.test_causal
"""

from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.biology.params  # noqa: F401  (declares on import)
import zimulation.cognition.params  # noqa: F401
import zimulation.world.params  # noqa: F401
from zimulation.cognition import causal_inference as CI
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.rng import Streams
from zimulation.core.scheduler import DAY
from zimulation.observer.truth import GroundTruth, causal

A = ("category", 1)
B = ("category", 2)


def _watch(model, s, n, p_a, p_b_if_a, p_b_if_not, t0=0):
    for i in range(n):
        a = s.random() < p_a
        b = s.random() < (p_b_if_a if a else p_b_if_not)
        model.observe(A, B, a, b, t0 + i)


def _act(model, s, n, p_b_if_done, controls=0, p_b_if_held=None, t0=0):
    for i in range(n):
        model.intervene(A, B, True, s.random() < p_b_if_done, t0 + i)
    for i in range(controls):
        model.intervene(A, B, False, s.random() < p_b_if_held, t0 + n + i)


# ------------------------------------------------------- the four verdicts
def test_watching_alone_can_show_prediction_but_never_cause():
    """
    However strong the correlation, an agent that has only watched may
    conclude that A predicts B -- never that A causes it.
    """
    m = CI.CausalModel()
    _watch(m, Streams(1).get("w"), 80, 0.5, 0.85, 0.1)
    label, d, _ = m.verdict(A, B)
    assert label == CI.PREDICTS, f"watching produced {label}"
    assert d > 0.5


def test_acting_with_controls_reveals_a_real_cause():
    m = CI.CausalModel()
    _act(m, Streams(2).get("w"), 30, 0.8, controls=30, p_b_if_held=0.1)
    label, d, _ = m.verdict(A, B)
    assert label == CI.MAY_CAUSE, f"a real cause was judged {label}"


def test_intervention_exposes_a_confound():
    """
    Something hidden drives both A and B, so they go together when watched.
    Doing A changes nothing. The learner concludes they share a cause --
    exactly what the sealed mechanism says.
    """
    truth = GroundTruth("mechanism", {"A_causes_B": False,
                                      "hidden_common_cause": True})
    m = CI.CausalModel()
    s = Streams(3).get("w")
    _watch(m, s, 80, 0.5, 0.8, 0.1)
    _act(m, s, 30, 0.3, controls=30, p_b_if_held=0.3)
    label, _, _ = m.verdict(A, B)
    assert label == CI.SHARED_CAUSE, f"a confound was judged {label}"
    assert truth.reveal("zimulation.observer.causality")["hidden_common_cause"]


def test_an_action_that_does_nothing_is_found_to_do_nothing():
    m = CI.CausalModel()
    _act(m, Streams(4).get("w"), 30, 0.2, controls=30, p_b_if_held=0.2)
    assert m.verdict(A, B)[0] == CI.NOT_RELIABLE


# ----------------------------------------------------------- superstition
def test_superstition_comes_from_missing_controls():
    """
    B happens seven times in ten whatever anyone does -- an illness that
    passes on its own. An agent that always acts and never withholds has
    no comparison, credits the outcome to its action, and is wrong. The
    same agent given control trials is right. Nothing in the module writes
    either conclusion.
    """
    truth = GroundTruth("mechanism", {"A_causes_B": False, "base_rate": 0.7})
    s = Streams(5).get("w")

    naive = CI.CausalModel()
    _act(naive, s, 20, 0.7)
    believed, _, _ = naive.verdict(A, B)
    real = truth.reveal("zimulation.observer.causality")["A_causes_B"]
    assert believed == CI.MAY_CAUSE and real is False, (
        "an agent without controls did not fall into superstition -- the "
        "mechanism the experiment depends on is missing")

    careful = CI.CausalModel()
    _act(careful, s, 20, 0.7, controls=20, p_b_if_held=0.7)
    assert careful.verdict(A, B)[0] == CI.NOT_RELIABLE, \
        "control trials did not dissolve the illusion"


def test_superstition_is_the_price_of_learning_fast():
    """
    The hypothesis parameter behaves as a real trade-off. In a world where
    A does nothing, agents that settle after two trials are fooled far more
    often than agents that wait for twenty.
    """
    key = "causal_evidence_threshold"
    original = R.get(key)
    try:
        def fooled(threshold, seed):
            R.set(key, float(threshold))
            s = Streams(seed).get("w")
            wrong = 0
            for _ in range(400):
                m = CI.CausalModel()
                _act(m, s, threshold, 0.3, controls=threshold,
                     p_b_if_held=0.3)
                wrong += m.verdict(A, B)[0] == CI.MAY_CAUSE
            return wrong / 400

        hasty, patient = fooled(2, 11), fooled(20, 12)
        assert hasty > patient + 0.1, (
            f"hasty learners fooled {hasty:.0%}, patient {patient:.0%}; the "
            f"evidence threshold is not trading speed for accuracy")
    finally:
        R.set(key, original)


# -------------------------------------------------------- time and change
def test_causes_must_come_before_effects():
    w = R.get("causal_window_s")
    assert CI.precedes(0, 10)
    assert not CI.precedes(10, 0), "an effect before its cause counted"
    assert not CI.precedes(0, 0)
    assert not CI.precedes(0, w + 1), "an outcome long after counted"


def test_a_changed_world_can_change_a_mind():
    """
    Evidence fades with the memories it came from, so when A stops working
    the old verdict does not hold on forever.
    """
    s = Streams(6).get("w")
    m = CI.CausalModel()
    _act(m, s, 30, 0.8, controls=30, p_b_if_held=0.1)
    assert m.verdict(A, B)[0] == CI.MAY_CAUSE
    m.decay(200 * DAY)
    _act(m, s, 30, 0.1, controls=30, p_b_if_held=0.1, t0=200 * DAY)
    assert m.verdict(A, B)[0] == CI.NOT_RELIABLE, \
        "an agent held to a cause that had stopped working"


def test_certainty_grows_with_evidence_but_never_completes():
    m = CI.CausalModel()
    s = Streams(7).get("w")
    _act(m, s, 3, 0.8, controls=3, p_b_if_held=0.1)
    early = CI.certainty(m.table(A, B))
    _act(m, s, 200, 0.8, controls=200, p_b_if_held=0.1, t0=10)
    late = CI.certainty(m.table(A, B))
    assert early < late < 1.0


# ------------------------------------------------------------ the barrier
def test_the_learner_never_reads_the_true_mechanism():
    """
    The verdict is a belief about a cause; the mechanism is the observer's.
    Checked on the AST and under execution.
    """
    src = (ROOT / "zimulation" / "cognition"
           / "causal_inference.py").read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Attribute):
            assert node.attr not in ("reveal", "ground"), \
                f"causal inference reaches for {node.attr}"
    m = CI.CausalModel()
    s = Streams(8).get("w")
    with causal():
        _act(m, s, 20, 0.8, controls=20, p_b_if_held=0.1)
        label, _, _ = m.verdict(A, B)
    assert label == CI.MAY_CAUSE, "learning failed inside a causal block"


def test_learning_is_deterministic():
    def run(seed):
        m = CI.CausalModel()
        s = Streams(seed).get("w")
        _watch(m, s, 40, 0.5, 0.7, 0.2)
        _act(m, s, 15, 0.6, controls=15, p_b_if_held=0.3, t0=100)
        m.decay(5 * DAY)
        return m.verdict(A, B)
    assert run(21) == run(21)


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
