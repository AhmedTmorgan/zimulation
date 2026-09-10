# Zimulation 2 — Experimental Protocol

This document defines how Zimulation 2 is run as an experiment rather than
as a story generator. `docs/SCIENTIFIC_CONTRACT.md` remains the higher
law: if this protocol conflicts with the contract, the contract wins.

## 1. What the current baseline can and cannot test

The current implementation contains a physical world, ecology, physiology,
genetics and development, noisy local perception, memory and beliefs,
causal learning, open concept formation, sensorimotor primitives, learned
skills, bounded planning, bodily drives and blind physical affordances.

It does **not** yet contain the social, communication, animal, persistent
culture or metacognitive layers. Therefore the present baseline is allowed
to study only questions such as:

- can a naive organism remain alive without being told what food or water is?
- what useful and false act-outcome beliefs arise from exploration?
- can material procedures arise from low-level interaction rather than an
  unlock tree?
- how strongly do biological priors change early survival and learning?
- does the physical world contain reachable routes to heat, sharp edges,
  binding, movement and ingestion?

It must not yet report results about language, religion, morality,
political authority, historical transmission, collective cognition or
self-awareness. Those outcomes are not measurable until their prerequisite
layers and observer definitions exist.

## 2. The baseline: Culture Zero Warm v1

Runner: `experiments/v2/culture_zero_v1.py`

Purpose: establish that the body-mind-world loop is viable before a severe
thermal bottleneck or social layer is introduced.

Default scenario choices are deliberately not claims about ancestral human
history:

- warm map centre (20 degrees latitude in the simplified climate model);
- one naive adult founder per replicate by default;
- no inherited concepts, skills, language, records or social institutions;
- learning enabled;
- `consummatory_bias = 0` in the strict baseline.

The founder is placed by a deterministic scenario rule near standing water
with nearby land. The agent is not told that the location contains water.
The placement rule exists to avoid making survival depend mostly on whether
a random initial coordinate happens to be kilometres from fluid before
locomotor learning is established.

## 3. Why the first baseline is warm

Cold is scientifically important, but it is a compound problem. A naked
organism may die before there is enough behavioural time to diagnose
whether perception, exploration, causal learning or planning works.

The warm baseline therefore isolates the learning loop first. Once it is
stable, a separate preregistered `cold_bottleneck` experiment will increase
thermal pressure. That later experiment must not contain a year-200 death
rule or any equivalent hidden deadline. Death must arise from energy,
water, tissue and temperature accounting.

## 4. Experimental conditions

The initial pilot family should include at least these conditions, with the
same seed family wherever deterministic pairing is meaningful:

| condition | learning | consummatory prior | purpose |
|---|---:|---:|---|
| CZ-W0 | on | 0 | strict zero-culture baseline |
| CZ-W1 | off | 0 | learning ablation |
| CZ-W2 | on | non-zero experimental value | biological-prior intervention |
| CZ-W3 | off | same non-zero value | separates prior benefit from learned benefit |

The non-zero prior value is a hypothesis parameter, not a fitted constant.
Do not select it after looking for the value that makes survival look most
human. A pilot may map the response surface; a later confirmatory run must
freeze the tested values in advance.

## 5. Pilot, calibration and confirmation are different datasets

### Development runs

Used to find software bugs, impossible physics and broken interfaces.
Results from these runs are never evidence.

### Pilot runs

Used to estimate variance, event frequency, computational cost and whether
an operational definition is measurable. Pilot results may motivate a
hypothesis but may not then be presented as confirmation of that same
hypothesis.

### Confirmatory runs

Hypotheses, seed-family construction, parameter ranges, exclusions,
termination rules and statistics are fixed before the confirmatory batch is
read. When the project reaches publishable hypotheses, these should be
preregistered or submitted as a Registered Report where appropriate.

## 6. Suggested first run ladder

These counts are computational design choices, not scientific constants.
They may be adjusted before confirmatory preregistration.

1. **Smoke:** 8 seeds × 1 simulated day. Detect crashes and impossible
   accounting.
2. **Pilot:** 32 seeds × 5 days per condition. Estimate early survival and
   learning frequencies.
3. **Stability:** 128 seeds × 30 days per condition. Test whether short-run
   remedies persist or reverse.
4. **Extended individual:** only after stability, run longer periods needed
   to validate long-term learning and aging behaviour.

Do not launch century-scale social runs merely because the scheduler can
advance that far. Long duration is useful only after the processes acting
inside that duration are validated.

## 7. Required metadata for every result

Every row or run bundle must include, directly or through a manifest:

- repository commit SHA;
- protocol name and version;
- simulation seed;
- scenario choices;
- parameter hash and full parameter manifest;
- detector/observer version when detectors are used;
- simulated start and end time;
- termination reason;
- ledger head/hash;
- software/runtime version used for the official batch.

Two results with different parameter hashes are not silently pooled.

## 8. Primary outcomes for Culture Zero Warm v1

The first baseline reports measurements, not a civilisation score.

Primary descriptive outcomes:

- survival / termination;
- cause of death;
- action count;
- number and persistence of learned remedies;
- false-remedy burden;
- number of active learned concepts;
- number of learned sensorimotor skills;
- resource and physiological state where needed for diagnostic analysis.

No single one of these is a success score. An agent with many concepts is
not automatically better than one with few; concepts matter only when they
improve prediction or behaviour under the relevant test.

## 9. Object identity rule

Active cognition must never use a Python object pointer or a ground-truth
object id to know that two encounters are the same individual object.

At the current stage the baseline is intentionally stricter: there is no
persistent individual-object identity in the active mind. Objects are
classified anew from current perception. Nearby things provide visual
features; handling can provide tactile features. An explicit later
object-continuity system may infer persistence from spatiotemporal and
perceptual evidence, but it must be uncertain and independently tested.

This prevents a severe hidden advantage: perfectly recognising a changed,
moved or damaged object forever because the host runtime knows it is the
same allocation.

## 10. Discovery rule

A discovery is not the first time code executes a primitive.

For an observer to later classify a discovered procedure, evidence should
include at least:

1. an agent generated the relevant primitive sequence without being given
   its purpose;
2. the sequence produced a measurable state change through ordinary world
   physics;
3. the agent's own experience made the sequence more likely to be repeated
   or stored;
4. when cultural discovery is claimed later, the procedure persists across
   individuals through an explicit social transmission route.

Thus a random successful friction event is not yet "discovery of fire".
It is a physical event. Stable deliberate reproduction and later cultural
transmission are progressively stronger observer classifications.

## 11. Negative results are retained

Never discard a seed because:

- everyone dies;
- learning makes survival worse;
- a false remedy dominates;
- useful material procedures never appear;
- the population later fails to produce a target phenomenon.

Exclude only runs that violate a preregistered technical criterion, such as
corrupted state, broken determinism or a numerical failure. Report the
number and reason for every exclusion.

## 12. No anthropomorphic interpretation from one seed

A single ledger can be used to debug or illustrate a mechanism. It cannot
establish a general claim.

Statements such as "the agent became superstitious" or "the society chose
cooperation" must eventually map to preregistered observer measurements and
population-level statistics. Narrative summaries are generated only after
measurement.

## 13. Advancement gate to the social layer

Phase 5 should not become the active scientific baseline until all of the
following are true:

- the full CI contract is green;
- all currently available physical primitives are either behaviourally
  reachable or explicitly documented as awaiting a representation that is
  not yet available;
- active object categorisation has no perfect host-object identity;
- the warm baseline can run a seed batch reproducibly and emit complete
  metadata;
- parameter documentation is regenerated and has no declared-but-unused
  causal parameter;
- the observer can reconstruct important physical and learning events
  without changing history;
- no result was tuned to resemble known human history.

## 14. Next protocols, in order

After the gate above:

1. **Social Contact v1:** repeated co-presence, transfer, harm, care,
   reputation and attachment prerequisites, but no named institutions.
2. **Signal Zero v1:** biologically possible vocal/gestural signals with no
   supplied semantics.
3. **Cultural Transmission v1:** imitation and teaching of discovered
   procedures; no language assumed.
4. **Cold Bottleneck v1:** harsh thermal ecology with multiple physically
   possible solutions and no scripted extinction deadline.
5. **Persistent History v1:** only after durable symbolic records can
   actually emerge.
6. **Metacognition v1:** confidence, error monitoring and self-model tests;
   never a boolean `consciousness` variable.

Each protocol receives its own versioned runner and preregistered observer
metrics. Do not turn one giant run into evidence for every question at once.
