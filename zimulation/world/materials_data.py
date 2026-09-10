"""
Material property table.

A data module: numbers and their provenance, no logic. The contract test
enforces that separation, because a table that can compute is where a
mechanism would hide.

Every value is order-of-magnitude faithful rather than precise. What has
to be right is the *ordering* and the rough ratios -- that flint is harder
and far more brittle than hardwood, that fat carries roughly twice the
combustion energy per kilogram that wood does, that dry grass ignites
below the temperature hardwood needs. Those are the relations an agent
could discover by handling the stuff. Four significant figures would be
false precision implying measurements nobody made.

Nothing here says what a material is for.

Units: density kg/m^3, temperature K, specific heat J/(kg K), thermal
conductivity W/(m K), energies J/kg. Dimensionless scores are ordinal on
0..1: their ordering is meaningful, their ratios are not.
"""

from .materials import Material

#: Where these numbers come from. A table of this size is a few hundred
#: claims about the world, and claims need sources. Ordinal scores say so
#: rather than borrowing the authority of a measurement.
SOURCES = {
    "density": "standard reference values for the substance class",
    "specific_heat": "standard reference values",
    "conductivity": "standard reference values near room temperature",
    "melting_point": "standard reference values",
    "ignition_point": "piloted ignition temperatures; Babrauskas 2003 for "
                      "cellulosic materials",
    "combustion_enthalpy": "heats of combustion, standard reference values",
    "nutritive_energy": "metabolisable energy content of foodstuffs",
    "hardness": "modelling choice: ordinal 0..1, ranked on the Mohs "
                "ordering for minerals and indentation resistance for "
                "organic materials; ratios are not physical",
    "toughness": "modelling choice: ordinal 0..1 resistance to crack "
                 "propagation, ranked not measured",
    "grain": "modelling choice: ordinal 0..1 fineness of fracture, which "
             "sets which solids take a predictable edge",
    "elasticity": "modelling choice: ordinal 0..1 recoverable deformation",
    "moisture_capacity": "largest mass fraction of water held, wet basis "
                         "(water over total mass). For wood, from the maximum "
                         "moisture content at full saturation, (1.54 - G) / "
                         "(1.54 G) on a dry basis for specific gravity G "
                         "(Simpson 1993, USDA Forest Products Laboratory "
                         "FPL-RN-0243): 0.41 for hardwood, 0.61 for softwood. "
                         "Earlier values of 0.30 and 0.35 sat at or below the "
                         "flame's extinction moisture, so soaked wood could "
                         "never be too wet to burn. Other materials: "
                         "modelling choice",
    "porosity": "modelling choice: ordinal void fraction",
    "toxicity": "modelling choice: ordinal harm on ingestion",
}

MATERIALS = {

    # ---------------------------------------------------------------- stone
    "flint": Material(
        "flint", density=2600.0, hardness=0.82, toughness=0.18, grain=0.95,
        elasticity=0.05, conductivity=1.6, specific_heat=800.0,
        melting_point=1900.0),

    "granite": Material(
        "granite", density=2700.0, hardness=0.75, toughness=0.45, grain=0.30,
        elasticity=0.05, conductivity=2.9, specific_heat=790.0,
        melting_point=1500.0),

    "sandstone": Material(
        "sandstone", density=2300.0, hardness=0.45, toughness=0.30,
        grain=0.20, elasticity=0.04, conductivity=1.7, specific_heat=920.0,
        melting_point=1700.0, porosity=0.20),

    # --------------------------------------------------------- plant matter
    "hardwood": Material(
        "hardwood", density=750.0, hardness=0.38, toughness=0.72, grain=0.55,
        elasticity=0.30, conductivity=0.16, specific_heat=1700.0,
        ignition_point=570.0, combustion_enthalpy=1.6e7,
        moisture_capacity=0.41, porosity=0.35),

    "softwood": Material(
        "softwood", density=450.0, hardness=0.22, toughness=0.55, grain=0.60,
        elasticity=0.35, conductivity=0.12, specific_heat=1700.0,
        ignition_point=560.0, combustion_enthalpy=1.6e7,
        moisture_capacity=0.61, porosity=0.55),

    "dry_grass": Material(
        "dry_grass", density=80.0, hardness=0.03, toughness=0.10, grain=0.40,
        elasticity=0.60, conductivity=0.05, specific_heat=1500.0,
        ignition_point=520.0, combustion_enthalpy=1.5e7,
        moisture_capacity=0.55, porosity=0.90),

    "bark_fibre": Material(
        "bark_fibre", density=300.0, hardness=0.10, toughness=0.80,
        grain=0.70, elasticity=0.55, conductivity=0.09, specific_heat=1600.0,
        ignition_point=580.0, combustion_enthalpy=1.5e7,
        moisture_capacity=0.40, porosity=0.60),

    "tuber": Material(
        "tuber", density=1050.0, hardness=0.08, toughness=0.25, grain=0.15,
        elasticity=0.20, conductivity=0.50, specific_heat=3400.0,
        moisture_capacity=0.70, porosity=0.15, nutritive_energy=3.2e6),

    # -------------------------------------------------------- animal matter
    "bone": Material(
        "bone", density=1900.0, hardness=0.55, toughness=0.50, grain=0.45,
        elasticity=0.15, conductivity=0.35, specific_heat=1300.0,
        nutritive_energy=1.0e6),

    "hide": Material(
        "hide", density=1000.0, hardness=0.06, toughness=0.85, grain=0.30,
        elasticity=0.70, conductivity=0.15, specific_heat=3000.0,
        ignition_point=610.0, combustion_enthalpy=1.8e7,
        moisture_capacity=0.45),

    "muscle": Material(
        "muscle", density=1050.0, hardness=0.05, toughness=0.40, grain=0.25,
        elasticity=0.35, conductivity=0.49, specific_heat=3500.0,
        moisture_capacity=0.75, nutritive_energy=6.5e6),

    "fat": Material(
        "fat", density=900.0, hardness=0.02, toughness=0.15, grain=0.10,
        elasticity=0.25, conductivity=0.20, specific_heat=2300.0,
        ignition_point=620.0, combustion_enthalpy=3.7e7,
        nutritive_energy=3.7e7),

    # ----------------------------------------------------------------- other
    "clay": Material(
        "clay", density=1750.0, hardness=0.15, toughness=0.35, grain=0.05,
        elasticity=0.45, conductivity=1.1, specific_heat=880.0,
        melting_point=1600.0, moisture_capacity=0.50, porosity=0.40),

    "water": Material(
        "water", density=1000.0, hardness=0.0, toughness=0.0, grain=0.0,
        elasticity=1.0, conductivity=0.60, specific_heat=4186.0,
        melting_point=273.15),
}
