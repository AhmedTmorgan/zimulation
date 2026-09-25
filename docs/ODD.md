# ODD Description — Zimulation 2

**Status:** living description of the implemented model on the active V2
research branch. This document describes what exists, not what the long-term
roadmap hopes to add.

**Scope of this revision:** physical world, ecology, biological organism,
perception, learning, concept formation, primitive action, learned skills,
bounded planning, bodily drives, open physical affordances and perceptually
grounded categorisation. Social interaction, emergent communication,
animals, persistent culture and metacognition are not yet part of the active
scientific model.

This document follows the ODD structure: Overview, Design concepts and
Details.

---

# 1. Overview

## 1.1 Purpose and patterns

Zimulation 2 asks whether human-like macroscopic phenomena can eventually
arise from lower-level biological, cognitive, environmental and social
mechanisms without those phenomena being implemented as named causal
shortcuts.

The current model is earlier than that final question. Its immediate purpose
is to establish a defensible body-mind-world loop in which an organism:

1. encounters a locally observable physical environment;
2. experiences bodily needs without being told their solutions;
3. performs low-level sensorimotor acts;
4. observes consequences through noisy senses;
5. forms its own categories;
6. learns uncertain act-outcome relationships;
7. stores reusable action sequences;
8. plans with its own learned experience;
9. may survive or die as a consequence of physical and physiological
   processes.

The model is currently checked for patterns at three levels.

### Physical plausibility

Examples include seasonal temperature structure, thermoregulation, object
cooling, frictional heating, combustion, fracture, rain/fuel moisture and
body energy/water accounting.

### Cognitive plausibility

Examples include noisy perception, source-memory decay, false attribution,
bounded memory, category formation, uncertain causal learning, false
remedies and satisficing planning.

### Interface plausibility

A physically possible route must also be behaviourally reachable. For
example, it is insufficient for frictional ignition to exist in
`world/thermal.py`; an agent must be capable of attempting rubbing without
being told why.

No target historical trajectory is a calibration pattern.

## 1.2 Entities, state variables and scales

### World / terrain

The world is a finite spatial grid of local cells. Relevant cell state
includes position, elevation, soil, moisture, water fraction, temperature,
vegetation/ecological stocks and physical objects.

Agents do not have access to the complete grid.

### Physical objects

Objects are quantities of material with physical state rather than named
artifact types. State includes mass, length/geometry, material, temperature,
moisture, integrity, edge geometry/quality, position, attachment and any
active combustion state.

There is no causal `axe`, `pot`, `spear` or technology class.

### Materials

Materials carry physical/biological properties such as density, hardness,
toughness, brittleness/grain behaviour, thermal properties, combustion
properties, nutritional energy and toxicity where relevant.

Material names exist in the world implementation and observer tests. They
are not supplied as perceptual category names to agents.

### Organisms

Each active agent contains:

- a physical body;
- a genome/body-plan parameterisation;
- spatial position and held objects;
- individual deterministic random streams;
- learned concepts;
- learned skill procedures;
- learned remedies for bodily drives;
- remembered places;
- bounded decision/planning state.

### Body state

The physiological model includes body mass, energy/fat store, water,
internal temperature, damage, sleep debt, age, insulation, activity and gut
contents. Viability is derived from these states; there is no maximum-age
death switch.

### Cognitive categories

Concepts are opaque agent-created categories. A concept stores statistical
summaries of perceived features and outcomes plus provenance. The agent is
not given an ontology of food, stone, tool, danger or technology.

### Skills

A skill is a learned sequence of primitive actions that has repeatedly
produced a state transition with sufficient reliability. Skills have no
predefined semantic names.

### Time

The engine is event-driven. World processes operate at their required
resolution rather than through one universal annual tick. Current important
scales include individual actions, hourly ecology/weather effects, daily
weather generation, physiology over action intervals and age in continuous
seconds/years.

## 1.3 Process overview and scheduling

A deterministic scheduler orders events by simulation time and priority.

### World process

At hourly world events, ecology is advanced. On the first hourly event of a
new day, regional daily weather is generated and local cell conditions are
updated consistently with the climate model.

### Agent process

When an agent receives a turn:

1. its current local state is surveyed through permitted sensory routes;
2. interoceptive signals are sampled;
3. the most urgent current drive is selected;
4. an ongoing behavioural bout may continue;
5. if the agent knows a candidate remedy, bounded exploration/exploitation
   selects whether to use it;
6. planning may compose previously learned state transitions;
7. otherwise a physically available action is explored;
8. the selected primitive changes the physical world only through its
   relevant physical submodel;
9. the body advances through the elapsed time;
10. learned consequences, procedures and decisions are recorded;
11. the next turn is scheduled after the action duration.

World/physics tasks and organism tasks have explicit scheduler priorities so
same-time events are deterministic.

---

# 2. Design concepts

## 2.1 Basic principles

The binding design rule is:

> **Encode conditions, never conclusions.**

High-level human outcomes are forbidden as causal shortcuts. A world may
contain heat and combustion but an agent is not given a concept of fire. A
world may contain a sharp piece of matter but the agent is not given a tool
class.

The second principle is epistemic separation:

> An agent acts on what it can perceive, remember, infer or receive through
> an explicit causal route — never on observer ground truth.

## 2.2 Emergence

At the current stage, the model supports emergence only at relatively low
levels:

- learned perceptual categories;
- learned act-outcome expectations;
- false remedies/superstitious associations;
- reliable sensorimotor procedures;
- selected material transformations.

Language, religion-like belief systems, political structures, moral norms,
historical traditions, collective cognition and explicit self-models are
future observer-level phenomena and must not be claimed from the current
model.

## 2.3 Adaptation

Current organisms adapt within a lifetime through learning rather than by
optimising an explicit fitness function.

They can change:

- which acts they expect to relieve a drive;
- which categories they maintain;
- which action sequences become reusable skills;
- which locations are expected to contain useful kinds;
- which plans are attempted.

Genetic inheritance exists as a biological mechanism, but population-scale
selection is not yet the active experiment because generational social and
reproductive behaviour is not integrated into the running population loop.

## 2.4 Objectives

There is no scalar utility, civilisation score or fitness score.

Immediate behaviour is organised around biologically grounded signals such
as hunger, thirst, thermal discomfort, pain and rest, plus a bounded
curiosity mechanism. What action solves a drive is not supplied.

Planning pursues state goals learned from prior experience and satisfices;
it does not globally optimise all future consequences.

## 2.5 Learning

Several learning systems coexist.

### Instrumental act-outcome learning

Repeated action bouts are associated with changes in bodily signals. Small
samples are treated with finite-sample uncertainty rather than as known
population variances.

### Category learning

Perceived features are grouped by a rational/Bayesian-style categorisation
model. Outcomes can make a category useful or useless but do not directly
dictate membership.

### Skill learning

Repeated action sequences are compressed into procedures when the observed
transition is reliable and not rendered redundant by a shorter known route.

### Causal learning

The causal-inference layer distinguishes predictive association from
controlled intervention where information permits. It can form incorrect
causal beliefs when controls are absent.

## 2.6 Prediction

Agents predict consequences from their learned categories, act-outcome
experience and skill operators. Prediction is bounded by individual
experience and uncertainty.

The observer may compare these predictions with ground truth; the agent may
not.

## 2.7 Sensing

Perception is local, partial and noisy.

Current channels include sight, touch, sound and interoception. Physical
magnitudes are sensed with noise whose scale depends on acuity and bodily
impairment.

A key active-baseline rule is that object categorisation is recomputed from
current perception. Python object identity is not an epistemic channel.
Nearby objects do not provide tactile properties for free; handling can add
information unavailable to sight.

## 2.8 Interaction

At present, agents interact directly with physical matter and indirectly
with shared resource depletion. A full agent-agent social interaction model
is not yet implemented.

Primitive body-world interactions include movement, grasp/release,
force application, throwing, striking, rubbing, separation/cutting,
combination/binding, ingestion, looking, touching, listening, signal
emission and rest where the integration stage makes them behaviourally
reachable.

A primitive defines what a body can attempt, not what the attempt means.

## 2.9 Stochasticity

Stochastic processes use deterministic named random streams derived from the
simulation seed. Streams are separated so adding an unrelated mechanism is
less likely to perturb existing random sequences.

The reproducibility contract is:

`version + scenario + parameters + seed -> identical event ledger`

## 2.10 Collectives

No explicit social collective exists in the current active model. Later
collectives must arise from relationships and interaction networks rather
than from predefined tribe/nation/institution labels.

## 2.11 Observation

The observer is architecturally separate from causal cognition.

The event ledger is append-only and hash-chained. It records structured
physical, learning and decision events. Ground-truth access is guarded and
cannot be used on a causal path.

Observer algorithms must be pure functions of recorded/replayable history;
changing an observer must never change the simulated history.

---

# 3. Details

## 3.1 Initialization

The active Culture Zero warm baseline is defined in
`experiments/v2/culture_zero_v1.py` and `docs/EXPERIMENT_PROTOCOL.md`.

It begins with:

- a generated physical terrain/ecology;
- biological organisms;
- no inherited agent concepts;
- no learned skills;
- no language;
- no technology tree;
- no political role;
- no religious doctrine;
- no historical narrative.

The initial warm baseline uses a scenario-selected latitude and deterministic
access to a shoreline region to test the body-learning loop without making
initial geographic bad luck the dominant source of death.

## 3.2 Input data

The causal model does not ingest a historical trajectory.

Externally constrained quantities are declared in the parameter registry
with units, source and uncertainty. Physical and biological data tables also
carry provenance. Structural and numerical choices are labelled as such
rather than borrowing empirical authority.

Current documentation is generated/maintained in `docs/PARAMETERS.md`.

## 3.3 Submodels

### Terrain and climate

Terrain supplies local spatial geometry, elevation, water/soil structure and
visibility/travel relationships. Climate derives seasonal and daily
conditions from a simplified energy-balance structure and scenario
latitude.

### Ecology

Ecology grows and replenishes biological/resource material according to
local environmental conditions and updates fuel moisture with weather.
Ecology contains no knowledge of agent goals.

### Materials and objects

Material properties determine fracture, cutting, binding, heating,
combustion, nutrition and toxicity. Objects carry state and geometry, not
artifact roles.

### Thermal physics and combustion

Heat transfer, cooling, frictional contact heating, moisture costs,
ignition, smouldering/flaming behaviour and fuel consumption are physical
processes. An action cannot set an object burning by assignment.

### Physiology

The body accounts for basal/activity energy, thermoregulation, hydration,
gut absorption, sleep, damage and viability. Body state generates noisy
interoceptive signals.

### Genetics and development

The genome samples heritable biological dispositions/body-plan variation.
Development changes body capacity across age without semantic age switches
for cultural behaviour.

### Reproduction

The reproduction module currently models physiological consequences after
an insemination event, including fecundity, gestation, lactation and birth.
The active engine does **not** yet decide when or why such an interaction
occurs; therefore generational population dynamics are not claimed as
implemented.

### Perception

Perception transforms world/body states into limited sensory feature sets.
Agents receive properties through senses rather than world category names.

### Memory and belief

Episodes decay and may lose source information; recall can reconstruct and
strengthen traces. Beliefs preserve evidence provenance and confidence.

### Concepts

Agents construct statistical categories from perceived feature structure.
Category identities are opaque tokens.

### Skills

Repeated reliable action sequences can become stored procedures; unused
procedures fade.

### Planning

Planning uses operators learned from the agent's own experience, with finite
horizon and computation budget, and stops at an aspiration threshold rather
than globally maximising.

### Drives and arbitration

Bodily signals compete for behavioural priority. Learned remedies compete
against exploration. Blind affordances determine which physical attempts
are available from the current body/world arrangement.

---

# 4. Known omissions that bound interpretation

The following are deliberately **not yet implemented** in the active model:

- social relationship dynamics;
- attachment/reputation/cooperation/aggression between agents;
- semantics or emergent communication conventions;
- cultural transmission between agents;
- animal agents/ecosystems beyond material ecology;
- disease transmission beyond existing physiological/material mechanisms;
- population-scale mate choice and reproductive behaviour;
- observer emergence classifiers for language, authority, religion-like
  systems, moral norms or historical distortion;
- metacognition, Theory of Mind and explicit self-model experiments.

Any paper, report or public result must interpret the model within these
bounds.

# 5. Versioning rule

Any change that alters entities, scheduling, causal mechanisms,
initialization or parameter semantics requires review of this ODD document.
A stale ODD description is a reproducibility defect, not a documentation
cosmetic issue.
