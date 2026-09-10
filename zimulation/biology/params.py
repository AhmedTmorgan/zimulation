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

R.declare("activity_multiplier_hard_effort", "B", "dimensionless", 7.0,
          4.0, 12.0,
          "expenditure during sustained hard physical work, as a multiple "
          "of resting", "+/-2", ["biology.physiology"])

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
