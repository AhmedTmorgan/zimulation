"""
Heritable variation, verified.

    python -m tests.v2.test_genetics
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.biology.params  # noqa: F401  (declares on import)
import zimulation.world.params  # noqa: F401
from zimulation.biology import genetics as G
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.rng import Streams


def test_hexaco_is_actually_hexaco():
    """
    Name the model you are using. Zimulation 1 declared HEXACO and listed
    Neuroticism among the six -- a Big Five construct that HEXACO replaces
    with Emotionality and partly redistributes into low Agreeableness.
    """
    assert G.HEXACO == ("honesty_humility", "emotionality", "extraversion",
                        "agreeableness", "conscientiousness", "openness"), \
        f"not the six HEXACO dimensions: {G.HEXACO}"
    for wrong in ("neuroticism", "stability", "big_five"):
        assert wrong not in G.TRAITS, f"{wrong} in a model called HEXACO"


def test_there_is_no_fitness_anywhere():
    """
    Nothing scores an organism. Selection has to happen through what
    traits do to physiology and behaviour, not through a number that says
    who is better.

    Checked on the AST, so the module's docstring can explain that there
    is no fitness without tripping the check -- an earlier string-based
    version did exactly that.
    """
    import ast
    src = (ROOT / "zimulation" / "biology" / "genetics.py").read_text(
        encoding="utf-8")
    names = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Name):
            names.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            names.add(node.attr.lower())
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name.lower())
    for word in ("fitness", "score", "select", "survival_value"):
        hits = [n for n in names if word in n]
        assert not hits, f"genetics defines or uses {hits}"
    g = G.founder(Streams(1).get("g"))
    assert not hasattr(g, "fitness")


def test_same_stream_same_genome():
    a = G.founder(Streams(42).get("genome"))
    b = G.founder(Streams(42).get("genome"))
    assert a.additive == b.additive and a.phenotype == b.phenotype


def test_heritability_obeys_the_breeders_equation():
    """
    Heritability validated the way breeders measure it: R = h2 * S.

    Select the top and bottom tenth of a population on a trait, breed each
    group within itself, and compare. Offspring regress toward the
    population mean (Galton's finding), and the fraction of the selection
    differential that survives into the next generation estimates h2.

    This is the check that catches a mixing-weight implementation: it can
    produce offspring that resemble their parents while getting the
    realised heritability wrong.
    """
    s = Streams(7).get("breed")
    pop = sorted((G.founder(s) for _ in range(4000)),
                 key=lambda g: g["openness"])
    tenth = len(pop) // 10
    low_parents, high_parents = pop[:tenth], pop[-tenth:]

    def kids_of(parents):
        out = []
        for _ in range(1500):
            m = parents[s.randrange(len(parents))]
            f = parents[s.randrange(len(parents))]
            out.append(G.conceive(m, f, s)["openness"])
        return out

    def mean(xs):
        return sum(xs) / len(xs)

    s_diff = (mean([g["openness"] for g in high_parents])
              - mean([g["openness"] for g in low_parents]))
    r_diff = mean(kids_of(high_parents)) - mean(kids_of(low_parents))
    realised = r_diff / s_diff
    h2 = R.get("trait_heritability")

    assert r_diff > 0.0, "offspring of selected parents did not differ"
    assert r_diff < s_diff, "no regression toward the mean"
    assert abs(realised - h2) < 0.12, (
        f"realised heritability {realised:.2f} against declared {h2:.2f}; "
        f"the transmission model does not implement what it declares")


def test_a_disposition_is_not_what_is_passed_on():
    """
    The environmental deviation is expressed and not transmitted. An
    organism can be far from the mean in phenotype while its breeding
    value sits near it -- which is why a remarkable parent so often has
    unremarkable children.
    """
    s = Streams(5).get("env")
    pop = [G.founder(s) for _ in range(3000)]
    gaps = [abs(g.phenotype["openness"] - g.additive["openness"])
            for g in pop]
    assert max(gaps) > 0.1, "phenotype never departed from breeding value"


def test_variance_does_not_collapse_over_generations():
    """
    The silent failure Zimulation 1 suffered: a model that keeps running,
    keeps producing plausible numbers, and quietly turns its population
    into clones because the non-heritable term was drawn toward a common
    mean. Thirty generations of random mating must leave most of the
    founding variation intact.
    """
    s = Streams(99).get("pop")
    pop = [G.founder(s) for _ in range(200)]
    start = {t: G.population_variance(pop, t) for t in G.HEXACO}
    for _ in range(30):
        nxt = []
        for _ in range(len(pop)):
            m = pop[s.randrange(len(pop))]
            f = pop[s.randrange(len(pop))]
            nxt.append(G.conceive(m, f, s))
        pop = nxt
    for t in G.HEXACO:
        end = G.population_variance(pop, t)
        assert end > start[t] * 0.5, (
            f"{t} variance fell from {start[t]:.4f} to {end:.4f} in 30 "
            f"generations; the population is converging to clones")


def test_physical_traits_stay_within_the_body_plan():
    s = Streams(3).get("phys")
    pop = [G.founder(s) for _ in range(100)]
    for _ in range(20):
        pop = [G.conceive(pop[s.randrange(100)], pop[s.randrange(100)], s)
               for _ in range(100)]
    masses = [g["adult_mass_kg"] for g in pop]
    assert min(masses) >= 30.0 and max(masses) <= 120.0
    assert max(masses) - min(masses) > 5.0, "body size lost all variation"


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
