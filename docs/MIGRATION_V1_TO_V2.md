# Migration: Zimulation 1 to 2

## Status

| phase | state |
|---|---|
| 0 — freeze V1 | **done** — tagged `v1.0-legacy`, released |
| 1 — scientific contract | **done** — contract, registry, truth barrier, ledger, clock, 17 tests |
| 2 — physical world | **done** — materials, objects, combustion, space, climate; 20 physics tests |
| 3 — biological agent | **in progress** — physiology and genetics done and verified; development, reproduction pending |
| 4 — learning agent | not started |
| 5 — social layer | not started |
| 6 — communication | not started |
| 7 — animals and disease | not started |
| 8 — persistent culture | not started |
| 9 — metacognition | not started |
| 10 — open-ended research | not started |
| 11 — deep evolution | separate project |

## What V1 got right, and keeps

Determinism, the ground-truth barrier, provenance on every claim,
counterfactual levers, resource bounds, and automatic parameter counting.
These survive into V2 and get stricter.

## Why V1 cannot simply be extended

V1 encodes conclusions as mechanisms. It has a technology tree ending at
`waves`, a doctrine with articles, rulers, war as an action, and a
`religion`-shaped module. Those are the very things V2 is supposed to be
asking about. A model that contains `farming -> pottery -> copper` cannot
answer whether metallurgy was inevitable; it has already answered.

The most concrete illustration is V1's own parameter count. It advertised
66 free parameters. When the manifest was rewritten to count from the code
rather than by hand, the real figure was about 700. That is not a bug in
the counting -- it is what happens when a model grows by adding outcomes.

## Coexistence

V1 lives on in `village/` and stays runnable and reproducible at tag
`v1.0-legacy`. V2 is built alongside in `zimulation/`. Nothing in V2
imports from V1.

`village/` is Arabic-documented and stays that way; it is a frozen record.
V2 is English-canonical per the contract, with Arabic under `docs/ar/`.

## What is deliberately absent from the V2 tree

```
religion.py   war.py     government.py   morality.py
technology_tree.py       philosophy.py   consciousness.py
```

These are outcomes to be detected, not modules to be written.
