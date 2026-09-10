"""
Biological parameters.

A declaration module: numbers and provenance, no logic.

The organism modelled here is roughly human in size, metabolism and
thermal behaviour. That is a deliberate starting point for Program A,
which asks what a human-like body with no culture discovers -- not how
such a body evolved. Program B, where these values themselves become
heritable and evolvable, is a separate project and is not attempted yet.

Nothing here encodes a lifespan. Death has to fall out of energy balance,
core temperature, water, injury and the decline of repair with age. A
maximum-age constant would be the single most consequential conclusion a
model could smuggle in, and Zimulation 1 had one for a long time.
"""

from ..core.parameters import REGISTRY as R

# ------------------------------------------------------------- metabolism
R.declare("basal_metabolic_rate_w", "B", "W", 80.0, 55.0, 110.0,
          "resting energy expenditure of an adult of this body mass "
          "(Henry 2005 predictive equations)", "+/-15 W between individuals",
          ["biology.physiology"])

R.declare("mass_metabolic_exponent", "B", "dimensionless", 0.75, 0.6, 1.0,
          "metabolic rate scales with mass to roughly the three-quarter "
          "power (Kleiber's law)", "+/-0.1 and contested",
          ["biology.physiology"])

R.declare("reference_body_mass_kg", "B", "kg", 60.0, 35.0, 95.0,
          "body mass the basal rate is quoted for", "+/-15 kg",
          ["biology.physiology", "biology.development"])

R.declare("activity_multiplier_walking", "B", "dimensionless", 3.5, 2.0, 6.0,
          "energy expenditure while walking, as a multiple of resting",
          "+/-1", ["biology.physiology"])

# Hard work is paid act by act, at the efficiency of muscle
# (behavior/primitives.py); a declared multiplier for it was never read and
# the parameter audit removed it.

R.declare("energy_store_capacity_j_per_kg", "B", "J kg^-1", 3.0e7, 1e7, 5e7,
          "usable energy per kilogram of stored body fat", "+/-20%",
          ["biology.physiology"])

R.declare("fat_fraction_healthy", "B", "dimensionless", 0.18, 0.05, 0.40,
          "body fat as a fraction of mass in a well-fed adult",
          "+/-0.08 by sex and individual", ["biology.physiology"])

R.declare("fat_fraction_lethal", "B", "dimensionless", 0.03, 0.01, 0.06,
          "body fat fraction below which death from starvation follows; "
          "this is what makes starvation a process rather than a flag",
          "+/-0.01", ["biology.physiology"])

# ---------------------------------------------------------------- thermal
R.declare("core_temperature_k", "B", "K", 310.15, 308.0, 312.0,
          "normal human core temperature, 37 C", "+/-0.5 K",
          ["biology.physiology"])

R.declare("core_temperature_lethal_low_k", "B", "K", 297.15, 293.0, 301.0,
          "core temperature below which death from hypothermia follows, "
          "about 24 C", "+/-2 K", ["biology.physiology"])

R.declare("core_temperature_lethal_high_k", "B", "K", 316.15, 314.0, 318.0,
          "core temperature above which death from hyperthermia follows, "
          "about 43 C", "+/-1 K", ["biology.physiology"])

R.declare("body_surface_area_m2", "B", "m^2", 1.8, 1.2, 2.3,
          "skin surface area of an adult (Du Bois formula)", "+/-0.3 m^2",
          ["biology.physiology"])

R.declare("bare_skin_insulation_clo", "B", "clo", 1.1, 0.3, 2.0,
          "total core-to-air resistance of an unclothed resting body: "
          "vasoconstricted tissue plus the still-air boundary layer. An "
          "earlier value of 0.15 counted only added clothing and gave a "
          "resting heat loss of 1173 W against a true figure near 80, so "
          "every body died of hypothermia indoors",
          "+/-0.3 clo, falls sharply with wind", ["biology.physiology"])

R.declare("clo_to_si", "P", "m^2 K W^-1", 0.155, None, None,
          "definition of the clo unit of thermal insulation", "exact",
          ["biology.physiology"])

R.declare("shivering_max_multiplier", "B", "dimensionless", 4.0, 2.0, 6.0,
          "peak metabolic heat production from shivering, as a multiple of "
          "resting; the body's own answer to cold, and the reason cold is "
          "expensive in calories rather than immediately fatal",
          "+/-1", ["biology.physiology"])

R.declare("body_heat_capacity_j_per_k", "B", "J K^-1", 2.1e5, 1e5, 3e5,
          "heat capacity of a whole adult body, mass times specific heat "
          "of tissue", "+/-25%", ["biology.physiology"])

# ------------------------------------------------------------------ water
R.declare("water_fraction_of_mass", "B", "dimensionless", 0.6, 0.45, 0.7,
          "water as a fraction of body mass", "+/-0.05",
          ["biology.physiology"])

R.declare("water_loss_baseline_kg_per_day", "B", "kg", 2.4, 1.5, 4.0,
          "obligatory daily water loss through breath, skin and waste",
          "+/-1 kg", ["biology.physiology"])

R.declare("water_loss_per_k_above_comfort", "B", "kg K^-1", 0.35, 0.05, 1.0,
          "extra daily water lost to sweating per kelvin above thermal "
          "comfort", "+/-0.2", ["biology.physiology"])

R.declare("thermal_comfort_ambient_k", "B", "K", 302.0, 295.0, 306.0,
          "thermal neutrality for a resting *unclothed* body, about 29 C. "
          "Much higher than clothed comfort, and that gap is the whole "
          "reason an uninsulated organism in a temperate winter has an "
          "energy problem at all",
          "+/-2 K", ["biology.physiology"])

R.declare("max_sweat_rate_kg_per_s", "B", "kg s^-1", 4.2e-4, 1e-4, 1e-3,
          "peak sustained sweat rate of an acclimatised adult, about 1.5 "
          "kg/h; this is the ceiling on how much heat a body can shed by "
          "evaporation and therefore what makes heat lethal at all",
          "+/-50%", ["biology.physiology"])

R.declare("dehydration_lethal_fraction", "B", "dimensionless", 0.15,
          0.10, 0.22,
          "loss of body water, as a fraction, at which death follows",
          "+/-0.03", ["biology.physiology"])

# ------------------------------------------------------------------ sleep
R.declare("sleep_need_hours_per_day", "B", "h", 7.5, 4.0, 11.0,
          "daily sleep requirement of an adult", "+/-1.5 h",
          ["biology.physiology"])

R.declare("sleep_debt_impairment_h", "B", "h", 24.0, 8.0, 60.0,
          "accumulated sleep debt at which cognitive and motor performance "
          "is severely degraded", "+/-12 h", ["biology.physiology"])

# --------------------------------------------------------- injury, repair
R.declare("repair_rate_young", "B", "s^-1", 4.0e-6, 1e-7, 1e-4,
          "fraction of accumulated tissue damage repaired per second in a "
          "well-fed young adult, roughly a third per day",
          "+/-100%", ["biology.physiology"])

R.declare("repair_decline_onset_years", "B", "yr", 22.0, 15.0, 35.0,
          "age from which repair capacity begins its decline; below this "
          "age the body is still building",
          "+/-5 yr", ["biology.development"])

R.declare("repair_decline_exponent", "B", "dimensionless", 1.2, 0.8, 2.0,
          "how steeply repair falls with age past onset; this exponent, "
          "not any maximum age, is what makes old bodies die",
          "+/-0.4", ["biology.development"])

R.declare("damage_lethal_threshold", "S", "dimensionless", 1.0, 0.5, 3.0,
          "modelling choice: accumulated damage, in units where one is a "
          "whole body's worth, at which the organism fails",
          "modelling choice", ["biology.physiology"])

R.declare("pain_per_damage", "S", "dimensionless", 1.4, 0.1, 5.0,
          "modelling choice: how strongly accumulated damage registers as "
          "pain, which is the signal the organism can actually act on",
          "modelling choice", ["biology.physiology"])

# ------------------------------------------------------------- perception
R.declare("impairment_weight_sleep", "S", "dimensionless", 0.5, 0.0, 1.0,
          "modelling choice: how much sleep debt contributes to degraded "
          "performance relative to pain and thirst",
          "modelling choice", ["biology.physiology"])

R.declare("impairment_weight_pain", "S", "dimensionless", 0.3, 0.0, 1.0,
          "modelling choice: contribution of pain to degraded performance",
          "modelling choice", ["biology.physiology"])

R.declare("impairment_weight_thirst", "S", "dimensionless", 0.2, 0.0, 1.0,
          "modelling choice: contribution of dehydration to degraded "
          "performance", "modelling choice", ["biology.physiology"])

R.declare("visual_acuity_decline_onset_years", "B", "yr", 40.0, 30.0, 55.0,
          "age from which near vision and acuity measurably decline",
          "+/-8 yr", ["biology.development"])

R.declare("sensory_decline_per_year", "B", "yr^-1", 0.012, 0.002, 0.05,
          "annual fractional loss of sensory acuity after onset",
          "+/-0.01", ["biology.development"])

# --------------------------------------------------------------- heredity
R.declare("trait_population_sd", "B", "dimensionless", 0.16, 0.05, 0.3,
          "spread of a personality dimension across a population, on a "
          "0..1 population-relative scale; roughly one standard deviation "
          "of a normed score",
          "+/-0.05", ["biology.genetics"])

R.declare("trait_heritability", "B", "dimensionless", 0.45, 0.2, 0.7,
          "heritability of HEXACO dimensions from twin studies, which "
          "cluster between about 0.3 and 0.6 (Vernon et al. 2008; "
          "Lee & Ashton 2004)",
          "+/-0.1 and varies by dimension", ["biology.genetics"])

R.declare("mutation_sd", "N", "dimensionless", 0.02, 0.0, 0.1,
          "modelling choice: small per-generation perturbation standing in "
          "for new variation from mutation and recombination",
          "order of magnitude", ["biology.genetics"])

R.declare("physical_trait_heritability", "B", "dimensionless", 0.7, 0.4, 0.9,
          "heritability of adult body size, which is high in well-fed "
          "populations (Visscher et al. 2006)",
          "+/-0.1", ["biology.genetics"])

R.declare("adult_mass_sd_kg", "B", "kg", 8.0, 2.0, 20.0,
          "spread of adult body mass within a population", "+/-4 kg",
          ["biology.genetics"])

R.declare("adult_mass_min_kg", "B", "kg", 30.0, 20.0, 45.0,
          "smallest viable adult body mass of this body plan", "+/-8 kg",
          ["biology.genetics"])

R.declare("adult_mass_max_kg", "B", "kg", 120.0, 80.0, 180.0,
          "largest adult body mass of this body plan", "+/-30 kg",
          ["biology.genetics"])

R.declare("metabolic_efficiency_sd", "B", "dimensionless", 0.08, 0.01, 0.2,
          "between-individual spread in resting metabolic rate relative to "
          "the value predicted from mass", "+/-0.04", ["biology.genetics"])

R.declare("thermal_tolerance_sd", "B", "dimensionless", 0.08, 0.01, 0.2,
          "between-individual spread in cold and heat tolerance", "+/-0.04",
          ["biology.genetics"])

R.declare("physiology_multiplier_min", "B", "dimensionless", 0.6, 0.3, 0.9,
          "lowest relative value a physiological multiplier can take",
          "+/-0.1", ["biology.genetics"])

R.declare("physiology_multiplier_max", "B", "dimensionless", 1.4, 1.1, 2.0,
          "highest relative value a physiological multiplier can take",
          "+/-0.2", ["biology.genetics"])

# ------------------------------------------------------------ development
R.declare("birth_mass_kg", "B", "kg", 3.3, 2.0, 4.5,
          "mass of a newborn of this body plan at term", "+/-0.5 kg",
          ["biology.development", "biology.reproduction"])

R.declare("maturity_age_years", "B", "yr", 18.0, 14.0, 24.0,
          "age by which body mass approaches its adult value", "+/-3 yr",
          ["biology.development"])

R.declare("growth_steepness_per_year", "S", "yr^-1", 0.35, 0.1, 1.0,
          "modelling choice: a single logistic stands in for infant "
          "growth plus the adolescent spurt; this sets how sharp it is",
          "modelling choice", ["biology.development"])

R.declare("max_growth_kg_per_year", "B", "kg yr^-1", 8.0, 3.0, 15.0,
          "peak rate of mass gain during the adolescent growth spurt",
          "+/-3 kg/yr", ["biology.development"])

R.declare("tissue_energy_cost_j_per_kg", "B", "J kg^-1", 2.2e7, 1.0e7, 3.5e7,
          "energy to deposit a kilogram of new mixed tissue, including the "
          "cost of synthesis (Butte 2000, energy requirements of growth)",
          "+/-30%", ["biology.development"])

R.declare("strength_peak_age_years", "B", "yr", 27.0, 20.0, 35.0,
          "age of peak muscular strength", "+/-5 yr",
          ["biology.development"])

R.declare("strength_decline_per_year", "B", "yr^-1", 0.01, 0.003, 0.03,
          "fraction of peak strength lost per year past the peak, "
          "averaged across later life", "+/-0.005", ["biology.development"])

R.declare("strength_floor_fraction", "S", "dimensionless", 0.25, 0.05, 0.6,
          "modelling choice: the least strength an aged body retains, so "
          "that decline flattens rather than reaching zero",
          "modelling choice", ["biology.development"])

R.declare("sensory_floor_fraction", "S", "dimensionless", 0.2, 0.0, 0.6,
          "modelling choice: the least sensory acuity an aged body "
          "retains", "modelling choice", ["biology.development"])

# ----------------------------------------------------------- reproduction
R.declare("reproductive_maturity_fraction", "B", "dimensionless", 0.85,
          0.6, 0.98,
          "fraction of the growth curve at which reproduction becomes "
          "possible; menarche and spermarche both fall near the end of "
          "the adolescent spurt (Frisch 1978)",
          "+/-0.08", ["biology.reproduction"])

R.declare("conception_probability_per_event", "B", "dimensionless", 0.04,
          0.005, 0.3,
          "probability that a single insemination leads to conception, "
          "averaged over the cycle (Wilcox et al. 1995)",
          "+/-0.02", ["biology.reproduction"])

R.declare("fertility_decline_onset_years", "B", "yr", 35.0, 28.0, 42.0,
          "age from which female fecundity declines (Menken et al. 1986)",
          "+/-4 yr", ["biology.reproduction"])

R.declare("fertility_end_years", "B", "yr", 50.0, 44.0, 56.0,
          "age of reproductive senescence; this ends fertility, not life, "
          "and is the one age-indexed biological limit the model keeps",
          "+/-4 yr", ["biology.reproduction"])

R.declare("fat_fraction_ovulation_low", "B", "dimensionless", 0.12,
          0.08, 0.17,
          "body fat fraction below which ovulation ceases "
          "(Frisch & McArthur 1974)", "+/-0.03", ["biology.reproduction"])

R.declare("fat_fraction_ovulation_high", "B", "dimensionless", 0.20,
          0.15, 0.26,
          "body fat fraction above which ovulation is unimpaired by body "
          "condition (Frisch & McArthur 1974)", "+/-0.03",
          ["biology.reproduction"])

R.declare("lactation_suppression", "B", "dimensionless", 0.85, 0.3, 0.99,
          "fraction of fecundity suppressed while nursing -- lactational "
          "amenorrhea, the main birth-spacing mechanism in forager "
          "populations (Konner & Worthman 1980)",
          "+/-0.1", ["biology.reproduction"])

R.declare("lactation_duration_years", "B", "yr", 2.5, 0.5, 4.5,
          "duration of nursing in forager populations", "+/-1 yr",
          ["biology.reproduction"])

R.declare("gestation_days", "B", "d", 266.0, 250.0, 285.0,
          "duration of human gestation from conception", "+/-10 d",
          ["biology.reproduction"])

R.declare("gestation_extra_power_w", "B", "W", 15.0, 8.0, 30.0,
          "average extra energy expenditure of pregnancy, about 290 kcal "
          "per day (Butte & King 2005)", "+/-5 W",
          ["biology.reproduction"])

R.declare("lactation_extra_power_w", "B", "W", 25.0, 15.0, 40.0,
          "extra energy expenditure of lactation, about 500 kcal per day",
          "+/-8 W", ["biology.reproduction"])

R.declare("sex_ratio_male_fraction", "B", "dimensionless", 0.512, 0.48, 0.54,
          "fraction of births that are male (the secondary sex ratio)",
          "+/-0.01", ["biology.reproduction"])

R.declare("birth_complication_probability", "B", "dimensionless", 0.05,
          0.01, 0.2,
          "probability of a serious obstetric complication in a healthy "
          "mother without medical care", "+/-0.03",
          ["biology.reproduction"])

R.declare("birth_complication_severity_low", "S", "dimensionless", 0.3,
          0.0, 1.0,
          "modelling choice: least tissue damage a complication inflicts, "
          "in units of the lethal threshold",
          "modelling choice", ["biology.reproduction"])

R.declare("birth_complication_severity_high", "S", "dimensionless", 1.3,
          0.5, 3.0,
          "modelling choice: greatest such damage. With the range and the "
          "complication rate this implies maternal mortality near 1.5% "
          "per birth for a healthy mother, which is the pre-modern figure "
          "-- derived here, not declared", "modelling choice",
          ["biology.reproduction"])

# -------------------------------------------------------------------- gut
R.declare("stomach_capacity_kg", "B", "kg", 1.5, 0.8, 4.0,
          "comfortable stomach capacity of an adult of reference mass, "
          "about a litre and a half; maximal distension reaches about four "
          "(Geliebter 1988, Physiology & Behavior 44:665). Scaled in "
          "proportion to body mass, a modelling choice for the young",
          "+/-0.5 kg", ["biology.physiology"])

R.declare("gastric_half_time_food_s", "B", "s", 5400.0, 1800.0, 14400.0,
          "half-time of gastric emptying for a mixed solid meal, about an "
          "hour and a half (scintigraphic norms, Tougas et al. 2000, "
          "American Journal of Gastroenterology 95:1456)",
          "+/-45 min", ["biology.physiology"])

R.declare("gastric_half_time_fluid_s", "B", "s", 900.0, 300.0, 3600.0,
          "half-time of gastric emptying for water, ten to twenty minutes "
          "(Hunt & Spurrell 1951, Journal of Physiology 113:157)",
          "+/-5 min", ["biology.physiology"])

R.declare("emptiness_hunger_weight", "S", "dimensionless", 0.5, 0.0, 1.0,
          "modelling choice: how strongly an empty stomach is felt as "
          "hunger, standing for the short-term signals -- ghrelin rising "
          "before meals and falling after them (Cummings et al. 2001, "
          "Diabetes 50:1714) -- that make a well-nourished person hungry "
          "within hours of eating", "modelling choice",
          ["cognition.perception"])

# ------------------------------------------------------------ hypothermia
R.declare("shivering_full_core_k", "B", "K", 308.15, 306.0, 310.0,
          "core temperature down to which shivering stays at full strength, "
          "about 35 C, the threshold of mild hypothermia (Mallet 2002, "
          "QJM 95:775)", "+/-1 K", ["biology.physiology"])

R.declare("shivering_stop_core_k", "B", "K", 303.15, 301.0, 305.0,
          "core temperature below which shivering ceases and stupor sets "
          "in, about 30 C (Danzl & Pozos 1994, New England Journal of "
          "Medicine 331:1756)", "+/-1.5 K", ["biology.physiology"])

R.declare("satiety_meal_energy_j", "B", "J", 2.5e6, 1.0e6, 5.0e6,
          "energy in the stomach at which short-term hunger is fully "
          "quieted, about that of an ordinary meal (some 600 kcal). "
          "Nutrients reaching the gut, not the stomach's stretch, suppress "
          "the hunger signal ghrelin (Williams et al. 2003, Endocrinology "
          "144:2765)", "+/-50%", ["cognition.perception"])
