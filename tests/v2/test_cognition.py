"""
Perception, memory and belief, verified on their own.

The guard that matters most here is the ground-truth barrier. Memory is
where Zimulation 1's barrier was tested, and where it leaked once. These
tests check it structurally and under execution.

    python -m tests.v2.test_cognition
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
from zimulation.biology import physiology as P
from zimulation.cognition import belief as B
from zimulation.cognition import memory as M
from zimulation.cognition import perception as PC
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.rng import Streams
from zimulation.core.scheduler import DAY, YEAR
from zimulation.observer.truth import GroundTruth, TruthLeak, causal
from zimulation.world import combustion as C
from zimulation.world import objects as O
from zimulation.world.materials_data import MATERIALS
from zimulation.world.space import Terrain

COG = ROOT / "zimulation" / "cognition"


def _thing(name="flint", mass=0.5, length=0.15):
    t = O.Thing(7, MATERIALS[name], mass, length)
    return t


def _names(path):
    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Attribute):
            out.append((node.attr, node))
        elif isinstance(node, ast.Name):
            out.append((node.id, node))
    return out


# ----------------------------------------------------------- the barrier
def test_cognition_never_opens_ground_truth():
    """
    No cognition module reveals ground truth, or reads `.value` off a
    trace's sealed ground. Checked on the AST of every cognition file.
    """
    hits = []
    for f in sorted(COG.glob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "reveal":
                hits.append(f"{f.name}:{node.lineno} reveal")
            if (isinstance(node, ast.Attribute) and node.attr == "value"
                    and isinstance(node.value, (ast.Attribute, ast.Name))
                    and getattr(node.value, "attr",
                                getattr(node.value, "id", "")) == "ground"):
                hits.append(f"{f.name}:{node.lineno} ground.value")
    assert not hits, "cognition opens ground truth: " + ", ".join(hits)


def test_a_memory_cannot_know_whether_it_is_true():
    """
    Under execution: the sealed record of what happened travels with the
    trace, the observer can open it, and causal code cannot.
    """
    mem = M.Memory()
    tr = mem.encode(("place", 3, 4), 0, 0, {"warmth_felt": 2.0}, M.TOLD,
                    ground=GroundTruth("trace_origin",
                                       {"source": M.TOLD, "event": 17}))
    assert (tr.ground.reveal("zimulation.observer.history")["event"] == 17)
    with causal():
        for attempt in (lambda: tr.ground.value,
                        lambda: bool(tr.ground),
                        lambda: tr.ground == {"event": 17}):
            try:
                attempt()
            except TruthLeak:
                continue
            raise AssertionError("a trace's ground truth was readable")


def test_cognition_makes_no_global_queries():
    """Section 49: nothing in a mind may take the world as a whole."""
    for f in sorted(COG.glob("*.py")):
        names = [n for n, _ in _names(f)]
        assert "all_cells" not in names, f"{f.name} queries the whole world"


# ------------------------------------------------------------- perception
def test_perception_reports_properties_never_names():
    s = Streams(1).get("see")
    t = _thing()
    here = Terrain(8, Streams(2).get("t")).at(4, 4)
    p = PC.sense_thing(t, here, here, None, 0, 1.0, 0.0, s, touching=True)
    for bad in ("flint", "stone", "material", "name", "tool"):
        assert not any(bad in k for k in p.features), \
            f"a percept carried a category: {sorted(p.features)}"
    assert "hardness_felt" in p.features


def test_hardness_and_edge_need_handling():
    """A sharp flake and a dull pebble can look alike."""
    s = Streams(1).get("see")
    terr = Terrain(8, Streams(2).get("t"))
    c = terr.at(4, 4)
    seen = PC.sense_thing(_thing(), c, c, terr, 0, 1.0, 0.0, s)
    assert "hardness_felt" not in seen.features
    assert "edge_felt" not in seen.features


def test_perception_is_noisy_and_noise_has_causes():
    """
    Weber-law error, worse with dim senses and with a suffering body.
    """
    terr = Terrain(8, Streams(2).get("t"))
    c = terr.at(4, 4)
    t = _thing(mass=1.0)

    def spread(acuity, impairment, seed):
        s = Streams(seed).get("see")
        xs = [PC.sense_thing(t, c, c, terr, 0, acuity, impairment,
                             s).features["apparent_size"]
              for _ in range(400)]
        m = sum(xs) / len(xs)
        return m, (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5

    m, sd_sharp = spread(1.0, 0.0, 5)
    assert abs(m - t.volume_m3) < 0.1 * t.volume_m3, "perception is biased"
    assert sd_sharp > 0.0, "perception is noiseless"
    _, sd_dim = spread(0.5, 0.0, 6)
    _, sd_hurt = spread(1.0, 0.8, 7)
    assert sd_dim > sd_sharp * 1.5, "dim senses were not noisier"
    assert sd_hurt > sd_sharp * 1.5, "an impaired body was not noisier"


def test_nothing_beyond_the_horizon_is_seen():
    terr = Terrain(40, Streams(3).get("t"))
    assert PC.sense_thing(_thing(), terr.at(39, 39), terr.at(0, 0), terr,
                          0, 1.0, 0.0, Streams(1).get("s")) is None


def test_burning_is_seen_as_light_not_as_a_thing():
    terr = Terrain(8, Streams(2).get("t"))
    c = terr.at(4, 4)
    s = Streams(1).get("see")
    grass = O.Thing(9, MATERIALS["dry_grass"], 0.1, 0.5)
    cold = PC.sense_thing(grass, c, c, terr, 0, 1.0, 0.0, s)
    assert "brightness" not in cold.features
    C.try_ignite(grass, C.ignition_energy(grass) * 1.2, at_time=0)
    lit = PC.sense_thing(grass, c, c, terr, 0, 1.0, 0.0, s)
    assert lit.features.get("brightness", 0.0) > 0.0


def test_the_body_is_felt_through_signals_with_no_subject():
    """Interoception without a self (section 40)."""
    s = Streams(1).get("body")
    starving = P.Body()
    starving.fat_kg = starving.mass_kg * 0.04
    cold = P.Body()
    cold.core_temperature_k -= 3.0
    hs = PC.sense_body(starving, 0, s)
    hc = PC.sense_body(cold, 0, s)
    assert hs.subject is None and hs.channel == PC.INTERNAL
    assert hs.features["hunger"] > 0.6
    assert hc.features["cold"] > 0.6
    fed = P.Body()
    P.feed(fed, 0.8 * fed.stomach_capacity_kg, 3.2e6, water_fraction=0.6)
    assert PC.sense_body(fed, 0, s).features["hunger"] < 0.2
    assert PC.sense_body(P.Body(), 0, s).features["hunger"] > 0.3,         "an empty stomach was not felt, though the reserves were full"


# ----------------------------------------------------------------- memory
def test_ordinary_memories_fade_and_arousing_ones_last():
    s = Streams(4).get("m")
    mem = M.Memory()
    dull = mem.encode(1, 0, 0, {"heft": 1.0}, M.OBSERVED, salience=0.0)
    vivid = mem.encode(2, 0, 0, {"heft": 1.0}, M.OBSERVED, salience=1.0)
    mem.decay(90 * DAY, s)
    assert vivid.strength > dull.strength * 2.0
    mem.decay(365 * DAY, s)
    assert dull not in mem.traces, "a dull memory survived a year untouched"


def test_heard_things_come_to_be_remembered_as_seen():
    """
    False memory with nothing planting it. Source fades faster than
    content, and faded sources default toward one's own experience. The
    observer, opening each trace's sealed origin, can count how often the
    agent now believes it saw what it was only told.
    """
    s = Streams(5).get("m")
    mem = M.Memory()
    # Stay under capacity. An earlier version encoded 400 against a cap of
    # 300, lost 100 to eviction at write time, and blamed decay for it.
    n = int(R.get("episodic_capacity")) - 50
    for i in range(n):
        mem.encode(i, 0, 0, {"heft": 1.0 + i * 0.001}, M.TOLD,
                   ground=GroundTruth("trace_origin", {"source": M.TOLD}))
    assert len(mem.traces) == n, "traces were evicted at encoding"
    for _ in range(30):
        mem.decay(DAY, s)
    # Content must outlast source: every trace still held, every source
    # already faded past the point of re-attribution.
    assert len(mem.traces) == n, "content decayed away within 30 days"
    assert max(t.source_strength for t in mem.traces) < 0.1,         "source memory had not faded after 30 days"
    now_seen = sum(1 for t in mem.traces if t.source == M.OBSERVED)
    frac = now_seen / n
    assert 0.5 < frac < 0.9, f"{frac:.2f} of told things now 'seen'"
    truly_told = sum(
        1 for t in mem.traces
        if t.ground.reveal("zimulation.observer.history")["source"] == M.TOLD)
    assert truly_told == n, "the sealed origin was altered"


def test_recall_reconstructs_and_strengthens():
    s = Streams(6).get("m")
    mem = M.Memory()
    tr = mem.encode(1, 0, 0, {"heft": 1.0, "edge_felt": 0.5}, M.OBSERVED)
    mem.decay(20 * DAY, s)
    weak = tr.strength
    for _ in range(50):
        mem.recall(tr, s)
    assert tr.recalls == 50
    assert tr.strength > weak, "retrieval did not strengthen the trace"
    assert tr.features["heft"] != 1.0, "fifty recalls left it unchanged"


def test_similar_episodes_blend_and_keep_their_lineage():
    mem = M.Memory()
    a = mem.encode(5, 0, 0, {"heft": 1.00}, M.OBSERVED,
                   ground=GroundTruth("o", "a"))
    b = mem.encode(5, 10, 10, {"heft": 1.02}, M.OBSERVED,
                   ground=GroundTruth("o", "b"))
    c = mem.encode(6, 0, 0, {"heft": 1.00}, M.OBSERVED)
    mem.consolidate()
    assert len(mem.traces) == 2, "same-subject near-duplicates did not blend"
    host = mem.about(5)[0]
    assert b.id in host.merged_from, "the blend lost its lineage"
    assert c in mem.traces, "a different subject was merged in"


def test_memory_is_deterministic():
    def run(seed):
        s = Streams(seed).get("m")
        mem = M.Memory()
        for i in range(50):
            mem.encode(i % 7, i, i, {"heft": 1.0 + (i % 5) * 0.01},
                       M.TOLD if i % 2 else M.OBSERVED, salience=(i % 3) / 3)
        for _ in range(20):
            mem.decay(3 * DAY, s)
            if mem.traces:
                mem.recall(mem.traces[0], s)
        mem.consolidate()
        return [(t.id, t.source, round(t.strength, 12),
                 tuple(sorted(t.features.items()))) for t in mem.traces]
    assert run(9) == run(9)


# ----------------------------------------------------------------- belief
def test_consistent_evidence_raises_confidence():
    bel = B.Beliefs()
    b, _ = bel.observe("k", 1.0, M.OBSERVED, 0)
    c0 = b.confidence
    for i in range(10):
        bel.observe("k", 1.0 + (i % 2) * 0.01, M.OBSERVED, i)
    assert b.confidence > c0


def test_contradiction_lowers_confidence():
    bel = B.Beliefs()
    b, _ = bel.observe("k", 1.0, M.OBSERVED, 0)
    for i in range(8):
        bel.observe("k", 1.0, M.OBSERVED, i)
    before = b.confidence
    bel.observe("k", 9.0, M.OBSERVED, 99)
    assert b.confidence < before, "a wild contradiction raised confidence"


def test_a_well_founded_belief_moves_less_for_one_contradiction():
    """
    Belief perseverance from arithmetic alone: nothing marks any belief
    as stubborn.
    """
    few, many = B.Beliefs(), B.Beliefs()
    few.observe("k", 1.0, M.OBSERVED, 0)
    many.observe("k", 1.0, M.OBSERVED, 0)
    for i in range(40):
        many.observe("k", 1.0, M.OBSERVED, i)
    _, moved_few = few.observe("k", 3.0, M.OBSERVED, 50)
    _, moved_many = many.observe("k", 3.0, M.OBSERVED, 50)
    assert moved_many < moved_few * 0.5


def test_being_told_counts_for_less_than_seeing():
    seen, told = B.Beliefs(), B.Beliefs()
    seen.observe("k", 1.0, M.OBSERVED, 0)
    told.observe("k", 1.0, M.OBSERVED, 0)
    _, a = seen.observe("k", 2.0, M.OBSERVED, 1)
    _, b = told.observe("k", 2.0, M.TOLD, 1)
    assert b < a, "testimony moved a belief as much as observation"


def test_every_revision_is_traceable():
    bel = B.Beliefs()
    b, _ = bel.observe("k", 1.0, M.OBSERVED, 0, trace_id=11)
    bel.observe("k", 1.5, M.TOLD, 1, trace_id=12)
    bel.observe("k", 1.2, M.INFERRED, 2, trace_id=13)
    assert [p[1] for p in b.provenance] == [11, 12, 13]
    assert [p[0] for p in b.provenance] == [M.OBSERVED, M.TOLD, M.INFERRED]


def test_nothing_is_ever_certain():
    bel = B.Beliefs()
    b, _ = bel.observe("k", 1.0, M.OBSERVED, 0)
    for i in range(5000):
        bel.observe("k", 1.0, M.OBSERVED, i)
    assert b.confidence <= R.get("confidence_ceiling") < 1.0


def test_misattribution_grows_as_source_fades():
    """
    Not a threshold. The longer ago something was heard, the likelier it
    is now remembered as seen: a smooth rise toward the declared bias, not
    a jump at some fixed age of memory. A threshold version produced 0% at
    day 7, 71% at day 14, and nothing further ever.
    """
    s = Streams(8).get("m")
    mem = M.Memory()
    n = int(R.get("episodic_capacity")) - 50
    for i in range(n):
        mem.encode(i, 0, 0, {"heft": 1.0}, M.TOLD)
    seen = {}
    for d in range(1, 61):
        mem.decay(DAY, s)
        seen[d] = sum(t.source == M.OBSERVED for t in mem.traces) / n
    assert 0.0 < seen[3] < seen[14] < seen[60], (
        f"misattribution did not rise smoothly: day3 {seen[3]:.2f}, "
        f"day14 {seen[14]:.2f}, day60 {seen[60]:.2f}")
    bias = R.get("source_default_bias")
    assert abs(seen[60] - bias) < 0.1, (
        f"asymptote {seen[60]:.2f} against declared bias {bias:.2f}")


def test_misattribution_does_not_depend_on_step_size():
    """The engine advances time in irregular jumps; forgetting must not
    care how the interval was chopped up."""
    n = int(R.get("episodic_capacity")) - 50

    def frac(steps, seed):
        s = Streams(seed).get("m")
        mem = M.Memory()
        for i in range(n):
            mem.encode(i, 0, 0, {"heft": 1.0}, M.TOLD)
        for _ in range(steps):
            mem.decay((20 * DAY) // steps, s)
        return sum(t.source == M.OBSERVED for t in mem.traces) / n

    one, many = frac(1, 3), frac(20, 4)
    assert abs(one - many) < 0.12,         f"one 20-day jump gave {one:.2f}, twenty 1-day steps gave {many:.2f}"


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
