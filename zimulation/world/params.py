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

R.declare("surface_emissivity", "P", "dimensionless", 0.9, 0.7, 0.99,
          "longwave emissivity of natural non-metallic surfaces; wood, "
          "stone, soil and skin all lie near 0.9 (standard tables, e.g. "
          "Incropera & DeWitt, Fundamentals of Heat and Mass Transfer)",
          "+/-0.05", ["world.thermal"])

R.declare("boiling_point_water_k", "P", "K", 373.15, 340.0, 380.0,
          "boiling point of water at sea-level pressure; about 3 K lower "
          "per 1000 m of altitude", "exact at 1 atm", ["world.thermal"])

# ------------------------------------------------------------ combustion
# Ignition points and heats of combustion are properties of each material
# (world/materials_data.py, with their sources). Four declarations here
# duplicated them and nothing read them; the parameter audit removed them.

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

R.declare("friction_heat_efficiency", "P", "dimensionless", 0.95, 0.8, 1.0,
          "share of the work done against friction that appears as heat at "
          "the interface; nearly all of it does, a few percent going into "
          "wear and new surface (Bowden & Tabor 1950, The Friction and "
          "Lubrication of Solids). The first value, 0.35, stood in for heat "
          "conducting away from the contact, which world.thermal now "
          "computes explicitly -- keeping it would count that loss twice",
          "+/-0.05", ["world.mechanics", "world.thermal"])

R.declare("fracture_energy_scale", "N", "J kg^-1", 25.0, 5.0, 200.0,
          "impact energy per kilogram of target at which a brittle solid "
          "fractures; collapses a fracture-mechanics problem into one "
          "number. A hand-held hard-hammer blow delivers tens of joules "
          "(half m v squared for a stone near a kilogram at several metres "
          "a second), enough to detach flakes from a hand-sized flint core "
          "(Cotterell & Kamminga 1987 on the mechanics of flaking). The "
          "first value, 1.4e4 J/kg, put a 0.6 kg core at 8,400 J -- some "
          "three hundred times what any arm delivers -- so no body could "
          "ever have knapped; the physics test passed only because it "
          "injected the energy directly",
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

# ----------------------------------------------------------------- climate
R.declare("axial_tilt_degrees", "P", "degrees", 23.4, 0.0, 45.0,
          "obliquity of the ecliptic; the sole origin of seasons here",
          "the real value drifts by ~2 degrees over 40 kyr",
          ["world.climate"])

R.declare("map_centre_latitude_degrees", "P", "degrees", 45.0, -70.0, 70.0,
          "latitude of the middle of the map; sets how hard the winters "
          "are and therefore how much pressure cold applies",
          "a scenario choice, varied across experiments",
          ["world.climate"])

R.declare("meters_per_degree_latitude", "P", "m", 111195.0, 110500.0,
          111700.0,
          "length of one degree of latitude on a sphere of the Earth's mean "
          "radius, 6371 km. Replaces a declared eight-degree span that took "
          "no account of the map's size", "+/-0.5% with latitude on the "
          "real ellipsoid", ["world.climate"])

R.declare("solar_constant_w_m2", "P", "W m^-2", 1361.0, 1355.0, 1367.0,
          "total solar irradiance at one astronomical unit (Kopp & Lean "
          "2011, Geophysical Research Letters 38:L01706)", "+/-0.5 W m^-2",
          ["world.climate"])

R.declare("planetary_albedo", "P", "dimensionless", 0.30, 0.25, 0.35,
          "fraction of sunlight the planet reflects (Stephens et al. 2015, "
          "Reviews of Geophysics 53:141)", "+/-0.01", ["world.climate"])

R.declare("olr_intercept_w_m2", "P", "W m^-2", 203.3, 190.0, 215.0,
          "outgoing longwave radiation at 0 C in the linear fit A + B T to "
          "satellite data (North, Cahalan & Coakley 1981, Reviews of "
          "Geophysics 19:91)", "+/-5 W m^-2", ["world.climate"])

R.declare("olr_slope_w_m2_k", "P", "W m^-2 K^-1", 2.09, 1.5, 2.3,
          "increase of outgoing longwave per kelvin in the same fit "
          "(North, Cahalan & Coakley 1981)", "+/-0.2", ["world.climate"])

R.declare("heat_transport_w_m2_k", "P", "W m^-2 K^-1", 3.8, 2.0, 5.0,
          "Budyko's meridional transport coefficient: heat moves toward the "
          "planetary mean at C (T - Tplanet) (Budyko 1969, Tellus 21:611)",
          "+/-1", ["world.climate"])

R.declare("surface_heat_capacity_j_m2_k", "B", "J m^-2 K^-1", 2.38e7, 2.0e6,
          3.0e8,
          "effective heat capacity of ground and lower air, about six "
          "metres of water. Calibrated together with the seasonal exchange "
          "so that land at 45 degrees lags the sun by a month (warmest "
          "month July, not June, as on the northern continents; e.g. "
          "Hartmann 2016, Global Physical Climatology). Larger values give "
          "oceanic climates -- smaller swings, later seasons", "calibrated, "
          "+/-50%", ["world.climate"])

R.declare("seasonal_exchange_w_m2_k", "B", "W m^-2 K^-1", 2.48, 0.0, 10.0,
          "seasonal exchange of heat between a land surface and the ocean "
          "air that reaches it; zero is a purely continental column. "
          "Calibrated with the heat capacity so that land at 45 degrees "
          "swings about 28 K between its coldest and warmest months, as "
          "mid-continental climates do (Bucharest 25, Minneapolis 32). The "
          "ranges at 15, 30 and 60 degrees are then checks, not targets",
          "calibrated, +/-1", ["world.climate"])

R.declare("diurnal_lag_s", "P", "s", 9000.0, 3600.0, 14400.0,
          "delay of the daily temperature maximum near the ground after "
          "solar noon, two to three hours (Oke 1987, Boundary Layer "
          "Climates)", "+/-1 h", ["world.climate"])

R.declare("celsius_zero_k", "P", "K", 273.15, None, None,
          "zero of the Celsius scale in kelvin; the longwave fit above is "
          "in Celsius", "exact", ["world.climate"])

R.declare("diurnal_swing_k", "P", "K", 8.0, 1.0, 25.0,
          "day-to-night temperature range near the ground, peak to trough "
          "(the first version applied it as an amplitude, doubling it)",
          "+/-6 K", ["world.climate"])

R.declare("lapse_rate_k_per_m", "P", "K m^-1", 0.0065, 0.004, 0.010,
          "environmental lapse rate in the lower atmosphere", "+/-0.002",
          ["world.climate"])

R.declare("water_thermal_damping", "P", "dimensionless", 0.6, 0.0, 1.0,
          "how much standing water suppresses the local diurnal swing, "
          "owing to the heat capacity of water", "+/-0.2",
          ["world.climate"])

R.declare("weather_noise_k", "P", "K", 3.5, 0.0, 12.0,
          "day-to-day departure from the seasonal expectation", "+/-2 K",
          ["world.climate"])

R.declare("mean_precipitation_m_per_day", "P", "m", 0.0027, 0.0001, 0.02,
          "mean daily precipitation depth in a temperate zone, ~1 m/yr",
          "+/-100% by region", ["world.climate"])

R.declare("rain_day_fraction", "P", "dimensionless", 0.3, 0.02, 0.9,
          "share of days on which measurable rain falls; the rest are dry, "
          "because rain is episodic and that is what lets fuel dry out",
          "+/-0.15", ["world.climate"])

R.declare("orographic_gain_per_m", "P", "m^-1", 0.0006, 0.0, 0.005,
          "extra precipitation per metre of elevation as air is lifted",
          "+/-100%", ["world.climate"])

R.declare("moisture_saturation_depth_m", "P", "m", 0.02, 0.001, 0.2,
          "rainfall depth that takes dry ground to saturated", "+/-100%",
          ["world.climate"])

R.declare("evaporation_threshold_k", "P", "K", 273.15, 250.0, 300.0,
          "below freezing, ground moisture does not evaporate", "exact",
          ["world.climate"])

R.declare("evaporation_per_k_per_day", "N", "K^-1", 0.004, 0.0005, 0.05,
          "modelling choice: fraction of ground moisture lost per kelvin "
          "above freezing per day; collapses a surface energy balance "
          "into one rate",
          "order of magnitude", ["world.climate"])

# --------------------------------------------------------------- spatial
R.declare("sea_level_fraction", "S", "dimensionless", 0.28, 0.0, 0.8,
          "modelling choice: share of the map below the waterline; sets "
          "how much of the world is standing water",
          "modelling choice", ["world.space"])

R.declare("elevation_relief_m", "P", "m", 900.0, 50.0, 6000.0,
          "vertical relief between the lowest and highest ground on a map "
          "of this extent", "+/-100%", ["world.space"])

R.declare("water_depth_scale_m", "P", "m", 40.0, 2.0, 300.0,
          "depth below the waterline at which a cell counts as fully "
          "water rather than shallows", "+/-100%", ["world.space"])

R.declare("soil_depth_max_m", "P", "m", 1.2, 0.1, 5.0,
          "soil depth on flat well-drained ground", "+/-100%",
          ["world.space"])

R.declare("slope_soil_loss_m", "N", "m", 60.0, 5.0, 400.0,
          "modelling choice: local relief over which soil is stripped to "
          "nothing; collapses erosion into one number",
          "order of magnitude", ["world.space"])

R.declare("slope_rock_exposure_m", "N", "m", 80.0, 5.0, 400.0,
          "modelling choice: local relief at which bare rock is fully "
          "exposed; sets where knappable stone can be found at all",
          "order of magnitude", ["world.space"])

R.declare("terrain_smoothing_passes", "S", "dimensionless", 4.0, 0.0, 12.0,
          "modelling choice: how much the elevation noise is smoothed, "
          "which sets whether the map is rugged or rolling",
          "modelling choice", ["world.space"])

R.declare("eye_height_m", "B", "m", 1.6, 0.5, 2.2,
          "standing eye height of an adult of this body plan", "+/-0.2 m",
          ["world.space"])

R.declare("sight_line_tolerance_m", "N", "m", 2.0, 0.0, 20.0,
          "modelling choice: slack in the line-of-sight test, standing in "
          "for vegetation and small-scale relief the grid cannot resolve",
          "order of magnitude", ["world.space"])

R.declare("climb_cost_multiplier", "P", "dimensionless", 7.0, 2.0, 20.0,
          "horizontal-equivalent cost of vertical ascent on foot; a metre "
          "climbed costs roughly seven walked (Naismith-type rule)",
          "+/-50%", ["world.space"])

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

# ---------------------------------------------------------------- ecology
R.declare("plant_growth_base_temperature_k", "B", "K", 278.15, 273.15,
          283.15,
          "base temperature for temperate plant growth, 5 C, as used in "
          "growing-degree-day models (McMaster & Wilhelm 1997, "
          "Agricultural and Forest Meteorology 87:291)", "+/-3 K",
          ["world.ecology"])

R.declare("vegetation_max_kg_m2", "P", "kg m^-2", 1.6, 0.2, 6.0,
          "standing plant biomass at the deepest soil, that of temperate "
          "grassland; woodland carries several times more (Whittaker & "
          "Likens 1975, Primary Productivity of the Biosphere)",
          "+/-100%", ["world.ecology"])

R.declare("tuber_capacity_kg", "N", "kg", 4.0, 0.5, 50.0,
          "modelling choice: edible storage organs within reach of one spot "
          "in a cell of the deepest soil -- an abstraction of search, so "
          "that a patch is soon dug out and moving on is worth something",
          "order of magnitude", ["world.ecology"])

R.declare("tuber_regrowth_per_day", "N", "d^-1", 0.03, 0.001, 0.3,
          "modelling choice: fraction of a patch's shortfall regrown per "
          "day of full growing weather, so a dug patch recovers over one "
          "to two months", "order of magnitude", ["world.ecology"])

R.declare("tuber_item_kg", "N", "kg", 0.2, 0.05, 1.0,
          "modelling choice: typical mass of one wild tuber; wild edible "
          "tubers run from tens of grams to over a kilogram (e.g. Vincent "
          "1985, World Archaeology 17:131)", "order of magnitude",
          ["world.ecology"])

R.declare("stick_cap", "N", "items", 6.0, 0.0, 50.0,
          "modelling choice: fallen sticks within reach at the deepest "
          "soil", "order of magnitude", ["world.ecology"])

R.declare("stick_item_kg", "N", "kg", 0.3, 0.05, 3.0,
          "modelling choice: mass of a fallen stick", "order of magnitude",
          ["world.ecology"])

R.declare("stick_length_m", "N", "m", 0.8, 0.2, 3.0,
          "modelling choice: length of a fallen stick", "order of magnitude",
          ["world.ecology"])

R.declare("grass_cap", "N", "items", 6.0, 0.0, 50.0,
          "modelling choice: handfuls of dry grass within reach at the "
          "deepest soil", "order of magnitude", ["world.ecology"])

R.declare("grass_item_kg", "N", "kg", 0.02, 0.002, 0.2,
          "modelling choice: mass of a handful of dry grass",
          "order of magnitude", ["world.ecology"])

R.declare("grass_length_m", "N", "m", 0.3, 0.05, 1.0,
          "modelling choice: length of a handful of dry grass",
          "order of magnitude", ["world.ecology"])

R.declare("bark_cap", "N", "items", 2.0, 0.0, 20.0,
          "modelling choice: loose strips of bark within reach at the "
          "deepest soil", "order of magnitude", ["world.ecology"])

R.declare("bark_item_kg", "N", "kg", 0.02, 0.002, 0.2,
          "modelling choice: mass of a strip of bark", "order of magnitude",
          ["world.ecology"])

R.declare("bark_length_m", "N", "m", 0.8, 0.1, 3.0,
          "modelling choice: length of a strip of bark",
          "order of magnitude", ["world.ecology"])

R.declare("litter_regrowth_per_day", "N", "d^-1", 0.1, 0.001, 1.0,
          "modelling choice: fraction of the shortfall of fallen wood, dry "
          "grass and bark restored per day", "order of magnitude",
          ["world.ecology"])

R.declare("fuel_timelag_reference_s", "P", "s", 3600.0, 1800.0, 7200.0,
          "the one-hour timelag of fine dead fuel: time to come about "
          "two-thirds of the way to equilibrium moisture (Deeming, Burgan "
          "& Cohen 1977, National Fire-Danger Rating System)", "+/-50%",
          ["world.ecology"])

R.declare("fuel_timelag_reference_diameter_m", "P", "m", 0.003, 0.001,
          0.0064,
          "diameter typical of one-hour fuels, which are thinner than 0.64 "
          "cm (Deeming et al. 1977); timelag grows with diameter squared, "
          "as diffusion does (Fosberg 1970)", "+/-50%", ["world.ecology"])

R.declare("rock_exposure_threshold", "S", "dimensionless", 0.5, 0.0, 1.0,
          "modelling choice: rock exposure above which loose stones lie "
          "about", "modelling choice", ["world.ecology"])

R.declare("flint_cell_fraction", "S", "dimensionless", 0.25, 0.0, 1.0,
          "modelling choice: share of rocky places that carry flint; a "
          "geological condition drawn once when the world is made",
          "modelling choice", ["world.ecology"])

R.declare("cobble_cap", "N", "items", 3.0, 0.0, 20.0,
          "modelling choice: loose cobbles within reach on rocky ground",
          "order of magnitude", ["world.ecology"])

R.declare("cobble_kg", "N", "kg", 0.8, 0.1, 5.0,
          "modelling choice: mass of a hand-sized cobble",
          "order of magnitude", ["world.ecology"])

R.declare("cobble_length_m", "N", "m", 0.12, 0.05, 0.4,
          "modelling choice: size of a hand-sized cobble",
          "order of magnitude", ["world.ecology"])

R.declare("nodule_cap", "N", "items", 3.0, 0.0, 20.0,
          "modelling choice: loose flint nodules within reach where flint "
          "occurs", "order of magnitude", ["world.ecology"])

R.declare("nodule_kg", "N", "kg", 0.6, 0.1, 5.0,
          "modelling choice: mass of a flint nodule", "order of magnitude",
          ["world.ecology"])

R.declare("nodule_length_m", "N", "m", 0.12, 0.05, 0.4,
          "modelling choice: size of a flint nodule", "order of magnitude",
          ["world.ecology"])

R.declare("stone_exposure_per_day", "N", "items d^-1", 0.2, 0.0, 5.0,
          "modelling choice: loose stones come to hand again per day where "
          "some have been taken", "order of magnitude", ["world.ecology"])

R.declare("water_pool_kg", "N", "kg", 1000.0, 10.0, 1.0e6,
          "modelling choice: water within reach at a shore, kept topped up "
          "because at this scale standing water is not drunk dry",
          "order of magnitude", ["world.ecology"])

R.declare("dead_fuel_equilibrium_moisture", "P", "kg kg^-1", 0.12, 0.04, 0.25,
          "moisture that dead fine fuel settles to in temperate air between "
          "rains, typically 8 to 20 percent with humidity (Simard 1968, "
          "Canadian Forest Fire Research Institute report FF-X-14; the "
          "equilibrium moisture of fire-danger rating)", "+/-0.05",
          ["world.ecology"])

R.declare("rain_hours_per_wet_day", "N", "h", 4.0, 0.5, 24.0,
          "modelling choice: hours of rain on a wet day, during which fuel "
          "lying out wets toward what it can hold", "order of magnitude",
          ["world.ecology"])
