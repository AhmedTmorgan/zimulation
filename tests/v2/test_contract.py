"""
Enforcement of docs/SCIENTIFIC_CONTRACT.md.

These tests are the reason the contract is worth writing down. Without
them it is a statement of good intentions, and Zimulation 1 showed how
those decay: the parameter count drifted from a claimed 66 to an actual
~700 over a single session, not through dishonesty but through nobody
counting.

Every test here fails the build. None of them can be satisfied by writing
a comment.

    python -m tests.v2.test_contract
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

PKG = ROOT / "zimulation"
CONTRACT = ROOT / "docs" / "SCIENTIFIC_CONTRACT.md"

#: The observer names phenomena after they happen; that is its job.
OBSERVER = PKG / "observer"

#: Plumbing that holds no model of the world and decides nothing inside it.
#: Each entry needs a reason, and the list stays short: every name added
#: here is a place the contract stops being checked.
INFRASTRUCTURE = {
    # the registry itself - stores parameters, asserts nothing
    "core/parameters.py",
    # deterministic stream plumbing - carries no causal claim
    "core/rng.py",
    # ledger schema and hashing - records history, models nothing
    "core/events.py",
    # the clock - tick arithmetic and queue ordering, no causal claim
    "core/scheduler.py",
}


def _causal_modules():
    """
    Every module that can influence what an agent does.

    Infrastructure is included here: plumbing may hold no model, but it is
    still forbidden from naming conclusions.
    """
    for f in sorted(PKG.rglob("*.py")):
        if OBSERVER in f.parents or f.name == "__init__.py":
            continue
        yield f


def _declaration_modules():
    """
    Files whose entire job is to declare parameters. The numbers have to
    live somewhere, and that somewhere is here, with units and sources
    attached. They are exempt from the literal check and constrained
    instead by test_declaration_modules_only_declare.
    """
    for f in sorted(PKG.rglob("params.py")):
        yield f
    for f in sorted(PKG.rglob("*_data.py")):
        yield f


def _model_modules():
    """
    Causal modules that actually encode a model of the world or a mind --
    the ones whose every number is a claim. Infrastructure is excluded,
    since a slice index is not a statement about reality.
    """
    decl = set(_declaration_modules())
    for f in _causal_modules():
        if f.relative_to(PKG).as_posix() in INFRASTRUCTURE or f in decl:
            continue
        yield f


def _forbidden_words():
    """
    Read the forbidden vocabulary out of the contract itself, so the rule
    and its enforcement cannot drift apart.
    """
    text = CONTRACT.read_text(encoding="utf-8")
    m = re.search(r"FORBIDDEN-VOCABULARY-BEGIN -->\s*```(.*?)```",
                  text, re.S)
    assert m, "contract is missing its forbidden-vocabulary fence"
    words = set()
    for tok in m.group(1).split():
        for part in tok.split("-"):
            if len(part) > 2:
                words.add(part.lower())
    assert len(words) > 30, f"only {len(words)} forbidden words parsed"
    return words


def _word_parts(name):
    """
    Split an identifier into the words a human would read in it.

    snake_case and camelCase both, because `WarParty` must be caught as
    readily as `war_party`. An earlier version split only on non-letters
    and let every CamelCase conclusion through -- `FireMaker`, `GodBelief`,
    `MoralRule` -- which is precisely the naming style a class would use.
    """
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)
    spaced = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", spaced)
    return [p for p in re.split(r"[^A-Za-z]+", spaced.lower()) if p]


def _identifiers(tree):
    """Every name the module defines or reaches for."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            yield node.name, node.lineno
        elif isinstance(node, ast.Name):
            yield node.id, node.lineno
        elif isinstance(node, ast.Attribute):
            yield node.attr, node.lineno
        elif isinstance(node, ast.arg):
            yield node.arg, node.lineno


def test_no_conclusion_vocabulary():
    """
    Causal code may not name a conclusion.

    The world may contain combustion; the agent may not contain `fire`.
    The world may contain asymmetric resource control; the agent may not
    contain `power` or a role called `king`. If a phenomenon has a name in
    the engine, the engine is no longer asking whether it emerges.
    """
    bad = _forbidden_words()
    hits = []
    for f in _causal_modules():
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for name, line in _identifiers(tree):
            for part in _word_parts(name):
                if part in bad:
                    hits.append(f"{f.relative_to(ROOT)}:{line} -> {name}")
    assert not hits, (
        "conclusion vocabulary in causal code:\n  " + "\n  ".join(hits[:20]))


def test_causal_code_cannot_read_ground_truth():
    """
    The barrier holds under execution, not just by inspection.
    """
    from zimulation.observer.truth import GroundTruth, TruthLeak, causal

    real = GroundTruth("ignition_source", "lightning")

    # The observer may look, and the look is recorded.
    assert real.reveal("zimulation.observer.emergence") == "lightning"

    # Causal code may not, by any route.
    with causal():
        for attempt, fn in (
            ("read .value", lambda: real.value),
            ("reveal()", lambda: real.reveal("zimulation.observer.x")),
            ("compare", lambda: real == "lightning"),
            ("truthiness", lambda: bool(real)),
        ):
            try:
                fn()
            except TruthLeak:
                pass
            else:
                raise AssertionError(f"ground truth leaked via {attempt}")


def test_non_observer_modules_cannot_reveal():
    """Even outside a causal block, only observer code may reveal."""
    from zimulation.observer.truth import GroundTruth, TruthLeak

    g = GroundTruth("true_population", 412)
    try:
        g.reveal("zimulation.cognition.belief")
    except TruthLeak:
        pass
    else:
        raise AssertionError("a cognition module was allowed to read truth")


def test_every_causal_number_is_declared():
    """
    No undeclared constants in causal code.

    Structural literals (0, 1, -1, 2 and small indices) are exempt; every
    other number must come from the registry. This is the check Zimulation
    1 never had, and its absence is why that model's real parameter count
    was four times what it advertised.
    """
    exempt = {0, 1, 2, -1, 0.0, 1.0, 0.5, 100, 3, 4}
    hits = []
    for f in _model_modules():
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue
            v = node.value
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            if v in exempt:
                continue
            hits.append(f"{f.relative_to(ROOT)}:{node.lineno} -> {v}")
    assert not hits, (
        f"{len(hits)} undeclared constants in causal code:\n  "
        + "\n  ".join(hits[:20])
        + "\n(declare them in zimulation/core/parameters.py)")


def test_declaration_modules_only_declare():
    """
    A params.py or *_data.py may contain declarations and nothing else.

    This is the price of exempting them from the literal check. If a
    declaration file could branch or compute, it would be the obvious
    place to hide a mechanism -- numbers with a little logic wrapped
    around them, in the one file nobody audits for logic.
    """
    hits = []
    for f in _declaration_modules():
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue          # the table itself
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Expr)):
                # a bare Expr must be a call or a docstring, nothing else
                if isinstance(node, ast.Expr) and not isinstance(
                        node.value, (ast.Call, ast.Constant)):
                    hits.append(f"{f.relative_to(ROOT)}:{node.lineno} "
                                f"-> {type(node.value).__name__}")
                continue
            hits.append(f"{f.relative_to(ROOT)}:{node.lineno} "
                        f"-> {type(node).__name__}")
    joined = chr(10) + "  "
    assert not hits, (
        "declaration modules must contain only declarations:"
        + joined + joined.join(hits))


def test_declared_parameters_have_real_sources():
    """
    Every parameter says where its value came from, and a modelling guess
    must admit to being one rather than borrowing the authority of a
    citation.
    """
    import zimulation.world.params  # noqa: F401  (declares on import)
    from zimulation.core.parameters import REGISTRY

    assert len(REGISTRY.all()) > 15, "world parameters did not register"
    thin = []
    for name, p in REGISTRY.all().items():
        if len(p.source) < 20:
            thin.append(f"{name}: {p.source!r}")
        if p.category in ("N", "S") and not any(
                w in p.source.lower() for w in
                ("choice", "stands in", "lumps", "collapses", "order of",
                 "approximation", "sets the", "how ")):
            thin.append(f"{name}: category {p.category} should say why "
                        f"this value rather than cite authority")
    joined = chr(10) + "  "
    assert not thin, "weak parameter sources:" + joined + joined.join(thin)


def test_data_tables_carry_sources():
    """
    A property table is hundreds of claims about the world. Each column
    needs a source, and an ordinal score must admit to being one rather
    than borrowing the authority of a measurement.
    """
    import importlib
    missing = []
    for f in _declaration_modules():
        if not f.name.endswith("_data.py"):
            continue
        mod = importlib.import_module(
            "zimulation." + f.relative_to(PKG).with_suffix("").as_posix()
            .replace("/", "."))
        sources = getattr(mod, "SOURCES", None)
        if not sources:
            missing.append(f"{f.name}: no SOURCES mapping")
            continue
        for col, why in sources.items():
            if len(why) < 20:
                missing.append(f"{f.name}:{col}: source too thin")
    assert not missing, "data tables without provenance: " + ", ".join(missing)


def test_parameter_registry_refuses_bad_declarations():
    """A registry that accepts anything is not an audit."""
    from zimulation.core.parameters import Registry, ParameterError

    r = Registry()
    r.declare("ignition_temperature_wood", "P", "K", 560.0, 470.0, 650.0,
              "Babrauskas 2003, piloted ignition of dry softwood", "+/-40 K",
              ["world.combustion"])

    for label, kw in (
        ("no source", dict(name="a", category="P", units="m", default=1.0,
                           source="")),
        ("TODO source", dict(name="b", category="P", units="m", default=1.0,
                             source="TODO")),
        ("default outside range", dict(name="c", category="P", units="m",
                                       default=9.0, low=0.0, high=2.0,
                                       source="ref")),
        ("claim without units", dict(name="d", category="B", units=None,
                                     default=1.0, source="ref")),
        ("unknown category", dict(name="e", category="Z", units="m",
                                  default=1.0, source="ref")),
    ):
        try:
            r.declare(**kw)
        except ParameterError:
            pass
        else:
            raise AssertionError(f"registry accepted: {label}")

    try:
        r.get("never_declared")
    except ParameterError:
        pass
    else:
        raise AssertionError("registry served an undeclared parameter")

    # The hash must move when a value moves, or results are not comparable.
    before = r.hash()
    r.set("ignition_temperature_wood", 600.0)
    assert r.hash() != before, "parameter hash did not change with the value"


def test_no_pretrained_models_anywhere():
    """
    No LLM, embedding or human-text corpus may touch agent cognition.
    Doing so would import the very things the experiment is testing for.
    """
    banned = ("openai", "anthropic", "transformers", "torch", "tensorflow",
              "sentence_transformers", "gensim", "spacy", "nltk",
              "huggingface", "llama", "gpt", "bert", "word2vec", "glove")
    hits = []
    for f in sorted(PKG.rglob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""]
            for m in mods:
                head = m.split(".")[0].lower()
                if head in banned:
                    hits.append(f"{f.relative_to(ROOT)}:{node.lineno} -> {m}")
    assert not hits, "pretrained model imported: " + ", ".join(hits)


def test_contract_document_exists_and_is_binding():
    """The contract is part of the build, not a wiki page."""
    text = CONTRACT.read_text(encoding="utf-8")
    for required in ("Encode conditions, never conclusions",
                     "ground-truth barrier",
                     "Determinism",
                     "does **not** fail because"):
        assert required.lower() in text.lower(), \
            f"contract is missing its section on: {required}"


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
