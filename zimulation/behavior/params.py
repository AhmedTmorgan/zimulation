"""
Parameters of the body acting on the world.

A declaration module: numbers and provenance, no logic.

These set what a body can physically do -- how fast it walks, how hard it
strikes, how much it lifts, how efficiently muscle turns food into work.
They are the ceiling on every primitive action, and through them the
genome and the body's age limit what an agent can even attempt.

They are deliberately about capacity, never about purpose. Nothing here
says what a blow is for, or that striking stone is worth doing.
"""

from ..core.parameters import REGISTRY as R

# ----------------------------------------------------------------- motion
R.declare("walking_speed_m_s", "B", "m s^-1", 1.3, 0.8, 1.8,
          "preferred walking speed of an adult on level ground",
          "+/-0.2 m/s", ["behavior.primitives"])

R.declare("strike_speed_m_s", "B", "m s^-1", 8.0, 3.0, 15.0,
          "peak speed of a hand-held striking stone in a full overarm blow "
          "by an adult of reference strength", "+/-3 m/s",
          ["behavior.primitives"])

R.declare("throw_speed_m_s", "B", "m s^-1", 20.0, 8.0, 35.0,
          "release speed of an overarm throw of a small stone by an adult",
          "+/-6 m/s", ["behavior.primitives"])

R.declare("throw_reference_mass_kg", "B", "kg", 0.4, 0.1, 2.0,
          "mass of a stone the arm throws at full speed; heavier things "
          "leave the hand slower, the arm delivering roughly fixed energy",
          "+/-0.2 kg", ["behavior.primitives"])

R.declare("rub_force_n", "B", "N", 60.0, 10.0, 200.0,
          "sustained downward force on a rubbed or drilled contact",
          "+/-30 N", ["behavior.primitives"])

R.declare("rub_speed_m_s", "B", "m s^-1", 1.5, 0.3, 4.0,
          "relative sliding speed of vigorous rubbing", "+/-0.7 m/s",
          ["behavior.primitives"])

# ---------------------------------------------------------------- effort
R.declare("max_lift_kg", "B", "kg", 40.0, 10.0, 120.0,
          "mass an adult of reference strength can lift and hold briefly",
          "+/-15 kg", ["behavior.primitives"])

R.declare("lift_height_m", "B", "m", 1.0, 0.3, 1.8,
          "height an object is raised when picked up to be held",
          "+/-0.3 m", ["behavior.primitives"])

R.declare("max_push_force_n", "B", "N", 400.0, 100.0, 1200.0,
          "sustained horizontal force an adult can apply shoving or "
          "dragging, roughly half body weight", "+/-150 N",
          ["behavior.primitives"])

R.declare("muscle_efficiency", "B", "dimensionless", 0.22, 0.15, 0.3,
          "mechanical efficiency of human skeletal muscle: the share of "
          "metabolic energy that becomes external work, about a fifth",
          "+/-0.04", ["behavior.primitives"])

R.declare("grasp_capacity", "B", "hands", 2.0, 1.0, 2.0,
          "number of independently grasping hands on this body plan",
          "exact", ["behavior.primitives"])

R.declare("action_duration_s", "B", "s", 1.0, 0.2, 5.0,
          "time for a single reach, grasp, blow or release -- about a "
          "second", "+/-0.5 s", ["behavior.primitives"])

R.declare("manual_stroke_work_j", "B", "J", 10.0, 2.0, 50.0,
          "mechanical work of one deliberate manual stroke -- a cut, a "
          "wrap, a scrape -- about fifty newtons over twenty centimetres",
          "+/-100%", ["behavior.primitives"])

R.declare("vocal_work_j", "B", "J", 1.0, 0.1, 10.0,
          "mechanical work of one loud call; vocalising is cheap next to "
          "moving the body", "+/-100%", ["behavior.primitives"])

# --------------------------------------------------------- cutting, binding
R.declare("cut_leverage", "S", "dimensionless", 2.0, 0.5, 6.0,
          "modelling choice: how many times its own toughness an edge of "
          "full cutting power can overcome at reference strength",
          "modelling choice", ["behavior.primitives"])

R.declare("edge_wear_per_cut", "B", "dimensionless", 0.02, 0.0, 0.2,
          "fraction of edge quality lost per cutting stroke; a fresh flake "
          "dulls with use and has to be replaced or reworked", "+/-100%",
          ["behavior.primitives"])

R.declare("binding_toughness", "S", "dimensionless", 0.7, 0.3, 0.95,
          "modelling choice: toughness a strand needs to hold two things "
          "together under load", "modelling choice",
          ["behavior.primitives"])

R.declare("binding_elasticity", "S", "dimensionless", 0.4, 0.1, 0.9,
          "modelling choice: flexibility a strand needs to be wrapped "
          "round something rather than snapping", "modelling choice",
          ["behavior.primitives"])

# --------------------------------------------------------------- ingestion
R.declare("bite_mass_kg", "B", "kg", 0.05, 0.005, 0.2,
          "mass ingested in one mouthful, tens of grams", "+/-0.03 kg",
          ["behavior.primitives"])

R.declare("bite_duration_s", "B", "s", 10.0, 2.0, 60.0,
          "time to bite, chew and swallow one mouthful", "+/-5 s",
          ["behavior.primitives"])

R.declare("bite_hardness_max", "B", "dimensionless", 0.3, 0.1, 0.6,
          "hardest material a jaw can break into mouthfuls, on the 0..1 "
          "hardness scale; roots and flesh yes, bone and wood no",
          "+/-0.1", ["behavior.primitives"])

R.declare("toxic_damage_per_kg", "S", "dimensionless", 1.0, 0.0, 20.0,
          "modelling choice: tissue damage per kilogram ingested of a "
          "material at full toxicity, in whole-body units",
          "modelling choice", ["behavior.primitives"])

# ---------------------------------------------------------------- rubbing
R.declare("max_stroke_frequency_hz", "B", "Hz", 5.0, 2.0, 8.0,
          "fastest sustained back-and-forth of hand and forearm; rapid "
          "alternating movements run at about five to seven cycles a "
          "second in healthy adults (diadochokinesis norms)",
          "+/-1.5 Hz", ["behavior.primitives"])

R.declare("rub_stroke_m", "B", "m", 0.2, 0.02, 0.5,
          "length of a comfortable back-and-forth rubbing stroke of the "
          "forearm", "+/-0.1 m", ["behavior.primitives"])

R.declare("max_stroke_m", "B", "m", 0.5, 0.2, 0.8,
          "longest rubbing stroke an arm makes without moving the body, "
          "about forearm plus hand", "+/-0.1 m", ["behavior.primitives"])
