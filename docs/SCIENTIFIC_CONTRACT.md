# The Scientific Contract

This document is binding. Code that violates it does not get merged,
however well it runs or however interesting its output looks.

## 1. The question

> What is the minimum set of biological, cognitive, physical, ecological
> and social mechanisms from which human-like culture, technology,
> cooperation, exploitation, language, power, belief, historical memory,
> collective cognition, self-awareness and philosophy can emerge without
> being explicitly programmed?

Zimulation 2 does not reproduce human history. It builds conditions under
which something resembling human history may — or may not — appear.

## 2. The rule that overrides every other consideration

**Encode conditions, never conclusions.**

The engine may encode the conditions under which a phenomenon *can* exist.
It must never encode that the phenomenon *must* emerge.

Before any feature is merged, one question is asked:

> Am I implementing a mechanism that permits a phenomenon, or am I
> secretly implementing the phenomenon itself?

If the second: it does not merge. This overrides convenience, narrative
quality, visual impressiveness and feature count.

### Worked examples

| The world may contain | The agent must not contain |
|---|---|
| combustion, ignition thresholds, heat transfer | a concept `fire` |
| asymmetric control of resources | a concept `power`, a role `king` |
| emitted and perceived signals | concepts `language`, `truth`, `lie` |
| selective attachment and its rewards | a variable `love` |
| remembered harm and anticipated threat | a variable `hate` |
| materials with hardness and edge geometry | an artifact type `axe` |
| pathogens, toxins, dose-response | a disease name known to agents |

## 3. Forbidden vocabulary in causal code

The following may not appear as identifiers in any causal module. They may
appear **only** in `zimulation/observer/`, where they name post-hoc
classifications of things that already happened.

<!-- FORBIDDEN-VOCABULARY-BEGIN -->
```
religion deity god worship ritual doctrine clergy sacred shrine prayer
king ruler chief monarch govern government state polity law legislate
war raid army battle warrior conquest
moral morality good evil sin virtue righteous wicked
love hate lie deceive deception propaganda betray
farm farming agriculture crop harvest domesticate livestock
fire technology science philosophy medicine
civilization tribe nation ethnicity race caste
marriage family-institution property ownership money currency trade-institution
```
<!-- FORBIDDEN-VOCABULARY-END -->


The list above is the single source of truth. It is parsed directly out of
this file by `tests/v2/test_contract.py::test_no_conclusion_vocabulary`,
which walks the AST of every causal module and fails on any matching
identifier, attribute, function or class name. Contract and enforcement
therefore cannot drift apart: editing the fence edits the test.

Matching is on whole word-parts, so `combustion` is fine while `fire_at`
is not, and `warmth` is fine while `war_party` is not.

## 4. The ground-truth barrier

The observer may know the true state of the universe. Agents may not.

No field marked ground truth may be read by any code that can influence an
agent's behaviour. This is stricter than V1's `truth` flag: it is enforced
structurally, by making ground truth reachable only through an API that
records every access and refuses to serve callers on the causal path.

## 5. Determinism

```
version + scenario + parameters + seed  ->  identical event ledger
```

Byte-identical. A changed observer, detector or report must never change
history. Detectors are pure functions of the ledger.

## 6. Provenance

Every belief, memory, statement, concept, artifact, skill and historical
claim carries a traceable ancestry: where it came from, through whom, and
with what confidence. A claim without provenance is a bug.

## 7. Parameters

Every number in causal code belongs to exactly one category:

| | meaning |
|---|---|
| **P** | physical — externally constrained |
| **B** | biological — externally constrained |
| **H** | hypothesis — deliberately under test |
| **S** | structural — model architecture choice |
| **N** | numerical — computational approximation, no causal claim |

Each requires name, category, units, default, allowed range, source,
uncertainty, and the modules that use it. Undeclared constants in causal
code fail the build.

V1 ended with roughly seven hundred hand-chosen numbers, most of them
never declared. That failure is the reason this section exists.

## 8. Calibration

Parameters are never tuned until history "looks human". Calibration
targets and validation targets are separate sets, fixed in advance.

## 9. What counts as failure

A run does **not** fail because language, religion, science, government or
fire never appear, or because the population dies out. Those are results.

A run fails only if:

- its rules are violated
- the observer leaks truth into agent cognition
- determinism breaks
- physical accounting breaks
- the experiment cannot be reproduced

## 10. What this project does not claim

It does not reconstruct actual human history. It is not evidence that any
real religion, institution or moral system arose by the mechanism shown
here. It does not prove historical records false. It does not produce
subjective experience, and no measurement in it may be reported as
consciousness. It is not predictive of humanity until externally
validated.

A successful run shows that a mechanism is **sufficient within the model**
to produce a phenomenon. It does not show that the same mechanism caused
that phenomenon in the world.

## 11. Two programs, not one

**Program A — Cultural Genesis.** Roughly human-like biology and
cognition, zero culture. Studies emergence of technology, language, norms,
authority, belief, transmission, science, self-concepts.

**Program B — Deep Evolution.** Cognitive capacity itself becomes
heritable and evolvable. Only this can address how human-like cognition
arose.

Program B is not attempted until Program A is scientifically stable.

## 12. No pretrained language models inside agents

No LLM, embedding trained on human text, or external corpus may touch
agent cognition. Doing so imports human language, religion, history,
science and morality into an experiment whose entire purpose is to see
whether those things arise. LLMs may summarise results for researchers,
outside the simulation.
