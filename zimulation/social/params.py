"""
Parameters of social interaction -- what bodies do to each other.

A declaration module: numbers and provenance, no logic.

These set what can physically happen between two agents' bodies. Giving
is placing a thing near another. Striking a body is applying force to
tissue. Proximity warmth is the reduced radiative loss from huddling.
None of these say what the interaction is for.
"""

from ..core.parameters import REGISTRY as R

R.declare("agent_perception_noise", "B", "dimensionless", 0.15, 0.01, 0.5,
          "noise in perceiving another agent's body features, comparable "
          "to the Weber fraction for object properties; estimated",
          "+/-100%", ["cognition.perception"])

R.declare("give_duration_s", "S", "s", 2.0, 0.5, 10.0,
          "modelling choice: time to place a held object near another "
          "agent's body", "modelling choice", ["behavior.primitives"])

R.declare("body_strike_damage_per_j", "B", "damage/J", 0.001, 0.0001, 0.01,
          "tissue damage per joule of blunt force to a body; a full adult "
          "blow of 25 J produces about 0.025 damage -- a bruise, not a "
          "killing blow", "+/-100%", ["behavior.primitives"])

R.declare("flinch_drop_threshold_j", "B", "J", 5.0, 1.0, 50.0,
          "impact above which a struck body drops what it was holding, "
          "the startle and pain causing the hands to open; any adult blow "
          "exceeds this", "+/-100%", ["behavior.primitives"])

R.declare("proximity_warmth_fraction", "P", "dimensionless", 0.15, 0.0, 0.5,
          "fraction of radiative heat loss reduced by each warm body in "
          "the same place, from huddling studies (Daanen & Van Marken "
          "Lichtenbelt 2016); capped at full shielding",
          "+/-0.1", ["core.engine"])

R.declare("agent_apparent_size_m3_per_kg", "S", "m^3/kg", 0.001, 0.0001, 0.01,
          "modelling choice: converts body mass to apparent volume for "
          "visual size estimation of another agent; approximate",
          "modelling choice", ["cognition.perception"])

R.declare("animate_noise_scale", "S", "dimensionless", 0.1, 0.01, 0.5,
          "modelling choice: noise scale for the animate feature when "
          "perceiving another agent; an animate body is approximately 1.0 "
          "with this much noise",
          "modelling choice", ["cognition.perception"])
