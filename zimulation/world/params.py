"""
Physical parameters of the world.

This is a declaration module: it contains numbers and nothing else. No
functions, no branches, no logic. The contract test enforces that, because
a declaration file that can compute is a place for a mechanism to hide.

Every entry carries units and a source. Where the source is a real
measurement the category is P; where it is a modelling choice the category
is S or N and the source says so plainly rather than dressing a guess as
a citation.

The values are order-of-magnitude faithful rather than precise. A world
that gets the ratio of wood to stone density right, and the fact that dry
wood ignites near 570 K while stone does not ignite at all, supports the
question being asked. Four significant figures would be false precision.
"""

from ..core.parameters import REGISTRY as R

# --------------------------------------------------------------- thermal
R.declare("ambient_temperature", "P", "K", 288.0, 200.0, 330.0,
          "global mean surface temperature, ~15 C", "+/-20 K by climate",
          ["world.thermal", "world.combustion"])

R.declare("stefan_boltzmann", "P", "W m^-2 K^-4", 5.670374419e-8,
          None, None,
          "SI defining constant", "exact",
          ["world.thermal"])

R.declare("convective_coefficient", "N", "W m^-2 K^-1", 12.0, 2.0, 50.0,
          "modelling choice: one lumped number stands in for a "
          "boundary-layer calculation, order of magnitude only",
          "order of magnitude", ["world.thermal"])

# ------------------------------------------------------------ combustion
R.declare("ignition_temperature_dry_plant", "P", "K", 570.0, 470.0, 650.0,
          "piloted ignition of dry cellulosic material (Babrauskas 2003)",
          "+/-50 K by species and thickness",
          ["world.combustion"])

R.declare("ignition_temperature_fat", "P", "K", 620.0, 550.0, 700.0,
          "animal fat autoignition is higher than dry plant matter",
          "+/-60 K", ["world.combustion"])

R.declare("combustion_enthalpy_plant", "P", "J kg^-1", 1.6e7, 1.2e7, 2.0e7,
          "heat of combustion of dry wood, ~16 MJ/kg", "+/-20%",
          ["world.combustion"])

R.declare("combustion_enthalpy_fat", "P", "J kg^-1", 3.7e7, 3.0e7, 4.2e7,
          "heat of combustion of animal fat, ~37 MJ/kg", "+/-15%",
          ["world.combustion"])

R.declare("burn_rate_coefficient", "N", "kg s^-1 m^-2", 0.011, 0.001, 0.05,
          "mass loss per unit burning surface; lumps pyrolysis and "
          "diffusion into one rate",
          "order of magnitude", ["world.combustion"])

R.declare("moisture_ignition_penalty", "P", "dimensionless", 2.6, 1.0, 6.0,
          "energy multiplier to ignite wet fuel: water must be driven off "
          "before pyrolysis begins",
          "+/-50%", ["world.combustion"])

R.declare("moisture_extinction", "P", "kg kg^-1", 0.35, 0.15, 0.60,
          "fuel moisture fraction above which flame cannot sustain",
          "+/-0.1, varies with fuel geometry", ["world.combustion"])

R.declare("oxygen_fraction_sea_level", "P", "dimensionless", 0.209,
          0.16, 0.23,
          "atmospheric oxygen by volume", "small",
          ["world.combustion"])

R.declare("oxygen_extinction_fraction", "P", "dimensionless", 0.16,
          0.12, 0.18,
          "limiting oxygen concentration below which flaming ceases",
          "+/-0.02", ["world.combustion"])

R.declare("radiant_ignition_distance", "N", "m", 0.9, 0.1, 5.0,
          "distance within which a burning object can ignite a neighbour; "
          "stands in for a view-factor calculation",
          "order of magnitude", ["world.combustion"])

R.declare("latent_heat_vaporisation_water", "P", "J kg^-1", 2.26e6,
          None, None,
          "enthalpy of vaporisation of water at 100 C", "exact enough",
          ["world.combustion"])

R.declare("division_epsilon", "N", "dimensionless", 1e-9, 1e-12, 1e-6,
          "modelling choice: guard against division by zero for massless "
          "or degenerate objects; carries no physical meaning",
          "none", ["world.combustion", "world.objects"])

R.declare("smoulder_rate_fraction", "P", "dimensionless", 0.12, 0.02, 0.4,
          "flameless surface oxidation consumes fuel far more slowly than "
          "flaming combustion; this is why an ember outlives a flame and "
          "can be carried",
          "+/-100%", ["world.combustion"])

R.declare("radiant_reach_exponent", "N", "dimensionless", 0.25, 0.0, 0.5,
          "modelling choice: how ignition reach grows with release rate; "
          "stands in for a view-factor and flame-height calculation",
          "order of magnitude", ["world.combustion"])

R.declare("radiant_capture_fraction", "N", "dimensionless", 0.02, 0.001, 0.2,
          "modelling choice: the share of a radiant source that a "
          "neighbouring object absorbs; order of magnitude only",
          "order of magnitude", ["world.combustion"])

# ------------------------------------------------------------- materials
R.declare("brittle_hardness_threshold", "S", "dimensionless", 0.6, 0.0, 1.0,
          "modelling choice: how hard a solid must be before failing by "
          "fracture is the relevant mode; sets which stones take an edge",
          "modelling choice", ["world.materials"])

R.declare("brittle_toughness_threshold", "S", "dimensionless", 0.4, 0.0, 1.0,
          "modelling choice: the toughness below which cracks run rather "
          "than blunt; with the hardness threshold this decides which "
          "materials can be worked to a cutting edge at all",
          "modelling choice", ["world.materials"])

# ------------------------------------------------------------- mechanics
R.declare("gravity", "P", "m s^-2", 9.81, 9.7, 9.9,
          "standard surface gravity", "negligible",
          ["world.mechanics"])

R.declare("friction_heat_efficiency", "N", "dimensionless", 0.35, 0.05, 0.8,
          "modelling choice: the share of rubbing work that stays as heat "
          "in the contact zone; order of magnitude, not measured",
          "order of magnitude", ["world.mechanics"])

R.declare("fracture_energy_scale", "N", "J kg^-1", 1.4e4, 1e3, 1e5,
          "impact energy per unit mass at which a brittle solid fractures; "
          "collapses a fracture-mechanics problem into one number",
          "order of magnitude", ["world.mechanics"])

R.declare("conchoidal_edge_quality", "S", "dimensionless", 0.85, 0.0, 1.0,
          "how sharp an edge a brittle fine-grained solid yields when "
          "fractured; structural choice about how edge geometry is scored",
          "modelling choice", ["world.mechanics"])

R.declare("max_fragments", "S", "dimensionless", 6.0, 2.0, 20.0,
          "modelling choice: cap on pieces from one fracture, so a single "
          "hard strike cannot flood the world with objects",
          "modelling choice", ["world.objects"])

R.declare("blunt_damage_divisor", "N", "dimensionless", 10.0, 2.0, 50.0,
          "modelling choice: how much sub-threshold impact energy a solid "
          "absorbs as damage rather than fracture; order of magnitude",
          "order of magnitude", ["world.objects"])

R.declare("fragment_share_low", "N", "dimensionless", 0.15, 0.05, 0.4,
          "modelling choice: smallest share of remaining mass one fragment "
          "takes; sets how evenly a fracture divides",
          "order of magnitude", ["world.objects"])

R.declare("fragment_share_high", "N", "dimensionless", 0.5, 0.3, 0.9,
          "modelling choice: largest such share; order of magnitude",
          "order of magnitude", ["world.objects"])

R.declare("edge_quality_low", "N", "dimensionless", 0.4, 0.0, 1.0,
          "modelling choice: worst edge a conchoidal fracture yields, so "
          "that not every strike produces a usable piece",
          "order of magnitude", ["world.objects"])

R.declare("friction_coefficient_dry", "P", "dimensionless", 0.45, 0.2, 0.8,
          "kinetic friction between dry wood surfaces", "+/-0.2",
          ["world.objects"])

R.declare("friction_jitter_low", "N", "dimensionless", 0.85, 0.5, 1.0,
          "modelling choice: lower bound of stroke-to-stroke variation in "
          "heat delivered by rubbing; order of magnitude",
          "order of magnitude", ["world.objects"])

R.declare("friction_jitter_high", "N", "dimensionless", 1.15, 1.0, 2.0,
          "modelling choice: upper bound of that variation; order of "
          "magnitude only",
          "order of magnitude", ["world.objects"])

# --------------------------------------------------------------- spatial
R.declare("cell_size", "S", "m", 250.0, 10.0, 5000.0,
          "side length of one spatial cell; sets the grain of locality",
          "modelling choice", ["world.space"])

R.declare("visibility_clear_day", "P", "m", 8000.0, 1000.0, 40000.0,
          "horizon-limited sighting distance for a large feature on flat "
          "terrain in clear air",
          "+/-100% with weather and elevation", ["world.space"])

R.declare("sound_audible_distance", "P", "m", 200.0, 20.0, 2000.0,
          "distance at which a loud human vocalisation remains audible "
          "above ambient noise in open terrain",
          "+/-100% with terrain and wind", ["world.space"])
