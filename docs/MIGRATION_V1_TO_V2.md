# Migration: Zimulation 1 to 2

## Status

| phase | state |
|---|---|
| 0 — freeze V1 | **done** — tagged `v1.0-legacy`, released |
| 1 — scientific contract | **done** — contract, registry, truth barrier, ledger, clock, 17 tests |
| 2 — physical world | **done** — materials, objects, combustion, space, climate; 20 physics tests. Corrected during Phase 4, found by driving the world with a body: fracture threshold was 300x a human blow; nothing cooled; heating skipped the latent heat of water; failed ignition counted energy twice; friction now heats a contact (world/thermal.py). Climate corrected when ecology needed a winter: 45 degrees had averaged 16 C with no day below 5 C, no seasonal lag, sunlight without day length, and a doubled day-night range; now a Budyko energy balance on exact daily sunlight, calibrated at 45 degrees and checked at 15, 30 and 60 (world/climate.py). Ecology added (world/ecology.py): plants by soil and growing weather, fallen wood, grass, bark, stone and water by conditions, fuel wetted by rain and dried by the air. Also corrected: latitude now follows distance (a fixed eight-degree span had put a 4 km map across 890 km of climate), and wood's water capacity follows its density (soaked wood could not be too wet to burn). |
| 3 — biological agent | **done** — physiology, genetics, development, reproduction; 31 biology tests Corrected when body and mind were connected: the body had no gut, so hunger was read only from stored fat and a whole meal moved it below the senses' noise; a stomach, gastric emptying, fullness, a fast hunger signal and thirst that counts swallowed water were added. Also corrected: shivering stayed at full strength at any core temperature, so a bare, fed body lived seventeen days at -1 C; it now fails between 35 and 30 C core and deep hypothermia incapacitates. |
| 4 — learning agent | **done** — perception, memory, belief, causal inference done and verified; concepts (Anderson's rational model) and sensorimotor primitives done and verified; learned skills (reliable state changes chunked from the agent's own acts; stone-breaking found by babbling with real physics) done and verified; bounded satisficing planning over the agent's own experience, every decision's alternatives on record, done and verified. Section 18's counterfactual replay awaits the engine Drives with learned remedies (section 13) and a place memory added (cognition/goals.py, places.py). |
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
