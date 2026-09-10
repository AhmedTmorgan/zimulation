"""
Cognitive parameters.

A declaration module: numbers and provenance, no logic.

These describe the limits of a mind rather than its contents. Nothing here
says what an agent knows, believes or values; everything here says how
noisy its senses are, how fast it forgets, how much it can hold at once,
and how much weight it gives to different kinds of evidence. Section 15 of
the contract asks for foolishness to emerge from limitation rather than be
declared as a trait, and these are the limitations.

Several are highly uncertain -- forgetting rates in particular vary by an
order of magnitude with the material -- and the uncertainty column says
so rather than implying a precision the literature does not have.

The first hypothesis parameter of the project lives here:
`testimony_trust`. How much an agent weights what it is told against what
it saw is a question the experiment is asking, not a value it assumes.
"""

from ..core.parameters import REGISTRY as R

# ------------------------------------------------------------- perception
R.declare("weber_fraction_magnitude", "B", "dimensionless", 0.08, 0.02, 0.3,
          "just-noticeable difference for judged magnitude such as heft or "
          "size, as a fraction of the magnitude (Weber's law; lifted-weight "
          "fractions near 0.05-0.1)", "+/-0.03", ["cognition.perception"])

R.declare("thermal_sensation_sd_k", "B", "K", 1.5, 0.3, 5.0,
          "spread of felt temperature about the true value; thermal "
          "sensation is relative and adapting, not a thermometer",
          "+/-1 K", ["cognition.perception"])

R.declare("touch_property_sd", "B", "dimensionless", 0.1, 0.02, 0.4,
          "noise on properties judged by handling -- hardness, edge, "
          "wetness -- on their 0..1 scales", "+/-0.05",
          ["cognition.perception"])

R.declare("impairment_noise_gain", "S", "dimensionless", 2.0, 0.0, 6.0,
          "modelling choice: how much a tired, hurting or thirsty body "
          "degrades its own perception, as a noise multiplier at full "
          "impairment", "modelling choice", ["cognition.perception"])

R.declare("interoception_sd", "B", "dimensionless", 0.05, 0.0, 0.3,
          "noise on internal body signals such as hunger and cold; "
          "interoceptive accuracy varies widely between people "
          "(Garfinkel et al. 2015)", "+/-0.04", ["cognition.perception"])

R.declare("cold_signal_scale_k", "B", "K", 2.0, 0.5, 6.0,
          "fall in core temperature at which the cold signal saturates; "
          "mild hypothermia is already felt intensely", "+/-1 K",
          ["cognition.perception"])

R.declare("brightness_saturation_w", "N", "W", 2000.0, 100.0, 20000.0,
          "modelling choice: radiant output at which perceived brightness "
          "saturates; sets how a small flame and a large one differ to the "
          "eye", "order of magnitude", ["cognition.perception"])

# --------------------------------------------------------- attention, memory
R.declare("working_memory_items", "B", "items", 4.0, 2.0, 9.0,
          "working-memory capacity in chunks (Cowan 2001); how many things "
          "an agent can hold in mind at once, and so compare",
          "+/-1", ["cognition.memory"])

R.declare("episodic_capacity", "N", "traces", 300.0, 20.0, 5000.0,
          "modelling choice: cap on stored episodes per agent, a "
          "computational bound standing in for the fact that most "
          "experience is never retained", "order of magnitude",
          ["cognition.memory"])

R.declare("memory_half_life_days", "B", "d", 30.0, 1.0, 365.0,
          "time for an unrehearsed episodic detail to lose half its "
          "accessibility; forgetting curves vary enormously with material "
          "(Ebbinghaus 1885; Rubin & Wenzel 1996)",
          "an order of magnitude either way", ["cognition.memory"])

R.declare("source_half_life_days", "B", "d", 8.0, 0.5, 120.0,
          "time for memory of *where* something was learned to halve. "
          "Source memory fades faster than content (Johnson, Hashtroudi & "
          "Lindsay 1993), and that gap is the engine of misattribution",
          "+/-100%", ["cognition.memory"])

R.declare("arousal_retention_gain", "B", "dimensionless", 3.0, 1.0, 10.0,
          "multiplier on retention for emotionally arousing episodes "
          "(McGaugh 2004); why a burn is remembered and a meal is not",
          "+/-100%", ["cognition.memory"])

R.declare("recall_drift_sd", "B", "dimensionless", 0.04, 0.0, 0.3,
          "fractional change to a remembered detail on each retrieval; "
          "memory is reconstructed at recall and stored back changed "
          "(Bartlett 1932; Nader et al. 2000)", "+/-100%",
          ["cognition.memory"])

R.declare("recall_strengthening", "B", "dimensionless", 0.2, 0.0, 1.0,
          "accessibility gained by a successful retrieval -- the testing "
          "effect (Roediger & Karpicke 2006)", "+/-0.1",
          ["cognition.memory"])

R.declare("merge_similarity", "S", "dimensionless", 0.9, 0.5, 0.999,
          "modelling choice: how alike two episodes of the same thing must "
          "be before they blend into one gist memory",
          "modelling choice", ["cognition.memory"])

R.declare("forget_threshold", "N", "dimensionless", 0.05, 0.001, 0.3,
          "modelling choice: accessibility below which a trace is dropped; "
          "stands in for the practical inaccessibility of weak memories",
          "order of magnitude", ["cognition.memory"])

R.declare("source_default_bias", "B", "dimensionless", 0.7, 0.5, 1.0,
          "probability that a memory whose source has faded is taken as "
          "one's own observation; faded content defaults to 'I saw it' "
          "(source misattribution; the sleeper effect)", "+/-0.15",
          ["cognition.memory"])

# ----------------------------------------------------------------- belief
R.declare("belief_prior_precision", "S", "dimensionless", 1.0, 0.1, 10.0,
          "modelling choice: how much weight a fresh belief's initial "
          "estimate carries against the first evidence",
          "modelling choice", ["cognition.belief"])

R.declare("testimony_trust", "H", "dimensionless", 0.5, 0.0, 1.0,
          "H: how much an agent weights what it is told relative to what "
          "it saw. Under test: does credulity gate the spread of knowledge "
          "and of error alike?", "under test", ["cognition.belief"])

R.declare("inference_weight", "S", "dimensionless", 0.6, 0.0, 1.0,
          "modelling choice: weight of an inferred conclusion relative to "
          "a direct observation", "modelling choice", ["cognition.belief"])

R.declare("record_weight", "S", "dimensionless", 0.8, 0.0, 1.0,
          "modelling choice: weight of evidence read from a durable record",
          "modelling choice", ["cognition.belief"])

R.declare("imitation_weight", "S", "dimensionless", 0.4, 0.0, 1.0,
          "modelling choice: weight of a belief acquired by copying what "
          "others do rather than by being told", "modelling choice",
          ["cognition.belief"])

R.declare("reconstruction_weight", "S", "dimensionless", 0.5, 0.0, 1.0,
          "modelling choice: weight of a detail filled in during recall "
          "rather than retrieved", "modelling choice", ["cognition.belief"])

R.declare("surprise_scale_sd", "S", "sd", 3.0, 1.0, 6.0,
          "modelling choice: how many expected standard deviations away a "
          "datum must fall to count as fully surprising",
          "modelling choice", ["cognition.belief"])

R.declare("surprise_discount", "S", "dimensionless", 0.5, 0.0, 0.95,
          "modelling choice: how much a fully surprising datum cuts a "
          "belief's precision -- how contradiction lowers confidence",
          "modelling choice", ["cognition.belief"])

R.declare("confidence_ceiling", "S", "dimensionless", 0.99, 0.5, 1.0,
          "modelling choice: the most confident any belief can become, so "
          "that no evidence is ever strictly unrevisable",
          "modelling choice", ["cognition.belief"])

R.declare("belief_provenance_cap", "N", "entries", 50.0, 5.0, 1000.0,
          "modelling choice: how many evidence records a belief keeps; a "
          "computational bound, oldest dropped first",
          "order of magnitude", ["cognition.belief"])

# ------------------------------------------------------- causal inference
R.declare("causal_evidence_threshold", "H", "trials", 5.0, 1.0, 100.0,
          "H: how many trials an agent needs before it treats a "
          "contingency as settled. Under test: is superstition the price "
          "of learning fast? Few trials means quick lessons and more "
          "false ones", "under test", ["cognition.causal_inference"])

R.declare("causal_delta_threshold", "S", "dimensionless", 0.15, 0.01, 0.5,
          "modelling choice: how large a difference in outcome rate counts "
          "as an effect rather than noise", "modelling choice",
          ["cognition.causal_inference"])

R.declare("contingency_prior_count", "S", "trials", 2.0, 0.1, 20.0,
          "modelling choice: pseudo-count smoothing every rate toward the "
          "prior -- how firmly a mind holds its assumption before evidence",
          "modelling choice", ["cognition.causal_inference"])

R.declare("baseline_prior_rate", "S", "dimensionless", 0.1, 0.0, 1.0,
          "modelling choice: what an agent with no comparison assumes "
          "happens anyway. Set low, a mind without controls credits every "
          "outcome to its own action -- the illusion of control "
          "(Langer 1975)", "modelling choice",
          ["cognition.causal_inference"])

R.declare("causal_window_s", "S", "s", 21600.0, 1.0, 604800.0,
          "modelling choice: how long after a candidate cause an outcome "
          "may follow and still be linked to it; long enough to connect "
          "eating to later sickness (Garcia & Koelling 1966)",
          "modelling choice", ["cognition.causal_inference"])

# --------------------------------------------------------------- concepts
R.declare("concept_coupling", "S", "probability", 0.5, 0.01, 0.99,
          "modelling choice: prior probability that two experiences belong "
          "to the same category -- the coupling parameter of Anderson's "
          "rational model of categorisation (Anderson 1991, Psychological "
          "Review 98:409). 0.5 is the neutral value: even prior odds of "
          "'the same as this one' and 'something new', a Chinese-restaurant "
          "concentration of one. Anderson's fits ran lower, near 0.3, but "
          "in this continuous model that made a mind whose sense of scale "
          "was still coarse file forty readings it could not tell apart as "
          "forty different kinds -- found by the counterexample test. Low "
          "values posit new kinds readily; high values lump",
          "modelling choice", ["cognition.concepts"])

R.declare("concept_prior_strength", "S", "pseudo-observations", 1.0, 0.1,
          20.0,
          "modelling choice: how many experiences' worth of weight the "
          "agent's overall sense of a feature's mean and spread carries "
          "when judging a young category (the kappa0 = nu0 of a "
          "normal-inverse-chi-squared prior; Anderson 1991 used 1)",
          "modelling choice", ["cognition.concepts"])

R.declare("concept_capacity", "N", "categories", 60.0, 5.0, 1000.0,
          "modelling choice: cap on categories one agent maintains; a "
          "computational bound, the least useful giving way first",
          "order of magnitude", ["cognition.concepts"])

R.declare("concept_min_examples", "S", "examples", 5.0, 2.0, 50.0,
          "modelling choice: how many members a category needs before its "
          "usefulness is judged", "modelling choice",
          ["cognition.concepts"])

R.declare("concept_min_predictive_value", "S", "dimensionless", 0.01,
          0.0001, 0.2,
          "modelling choice: how much knowing a category must improve "
          "outcome prediction for it to be kept; a category that predicts "
          "nothing is dissolved", "modelling choice",
          ["cognition.concepts"])

R.declare("counterexample_deviation", "S", "dimensionless", 0.4, 0.05, 1.0,
          "modelling choice: how far a member's outcome must depart from "
          "its category's before it counts as a counterexample",
          "modelling choice", ["cognition.concepts"])

R.declare("concept_example_cap", "N", "examples", 30.0, 3.0, 500.0,
          "modelling choice: how many example and counterexample records "
          "a category keeps; a computational bound", "order of magnitude",
          ["cognition.concepts"])

# --------------------------------------------------------------- planning
R.declare("planning_horizon_steps", "H", "steps", 4.0, 1.0, 20.0,
          "H: how many steps ahead an agent can imagine. Under test: do "
          "short horizons produce avoidable decision loss and repeated "
          "failure (section 15)? The default matches working memory",
          "under test", ["cognition.planning"])

R.declare("planning_budget_nodes", "N", "situations", 60.0, 5.0, 5000.0,
          "modelling choice: how many imagined situations one planning "
          "episode may examine -- limited computation (section 15); a "
          "bound, not a measured quantity", "order of magnitude",
          ["cognition.planning"])

R.declare("plan_aspiration", "S", "probability", 0.6, 0.05, 0.99,
          "modelling choice: predicted chance at which a plan is good "
          "enough and search stops -- satisficing (Simon 1956, "
          "Psychological Review 63:129)", "modelling choice",
          ["cognition.planning"])
