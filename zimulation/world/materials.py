"""
Materials.

A material is a bundle of measured properties. Nothing here knows what a
material is *for*: flint has no notion of blades, hide has no notion of
clothing, dry grass has no notion of tinder. Usefulness is a relation
between properties and a situation, and it is the agent's problem to
discover, not ours to encode.

This is the difference the contract turns on. Zimulation 1 had a
technology tree in which `stone` unlocked `copper`; a model like that has
already decided that stone leads to metal. Here there is only hardness,
brittleness, grain, conductivity and melting point, and whether anything
follows from them is an open question.

Property names are physical throughout. `toughness` is resistance to crack
propagation; `hardness` is resistance to indentation. A material can be
hard and brittle at once -- which is precisely why flint takes an edge and
why that edge chips.
"""

from __future__ import annotations

from ..core.parameters import REGISTRY


class Material:
    """
    Measured properties of a substance.

    Densities are kg/m^3, temperatures K, specific heat J/(kg K), thermal
    conductivity W/(m K). Dimensionless scores are on 0..1 and are ordinal:
    they are meant to get the ordering and rough ratios right, not to
    support engineering calculation.
    """

    __slots__ = ("name", "density", "hardness", "toughness", "grain",
                 "elasticity", "conductivity", "specific_heat",
                 "melting_point", "ignition_point", "combustion_enthalpy",
                 "moisture_capacity", "porosity", "nutritive_energy",
                 "toxicity")

    def __init__(self, name, density, hardness, toughness, grain,
                 elasticity, conductivity, specific_heat,
                 melting_point=None, ignition_point=None,
                 combustion_enthalpy=0.0, moisture_capacity=0.0,
                 porosity=0.0, nutritive_energy=0.0, toxicity=0.0):
        self.name = name
        self.density = density
        self.hardness = hardness
        self.toughness = toughness
        #: fine grain fractures predictably; coarse grain crumbles
        self.grain = grain
        self.elasticity = elasticity
        self.conductivity = conductivity
        self.specific_heat = specific_heat
        self.melting_point = melting_point
        #: None means it does not burn at any temperature reachable here
        self.ignition_point = ignition_point
        self.combustion_enthalpy = combustion_enthalpy
        self.moisture_capacity = moisture_capacity
        self.porosity = porosity
        #: energy an organism can extract, J/kg; zero for stone and wood
        self.nutritive_energy = nutritive_energy
        self.toxicity = toxicity

    @property
    def combustible(self):
        return self.ignition_point is not None

    @property
    def brittle(self):
        """
        Hard and not tough: fails by fracture rather than deformation.

        This single relation is why some stones can be worked to an edge
        and others cannot, and nothing in the model needs to say so.

        The two thresholds are declared rather than written here: they
        decide which materials can hold a cutting edge at all, which is
        far too consequential to leave as a literal in a predicate.
        """
        return (self.hardness > REGISTRY.get("brittle_hardness_threshold")
                and self.toughness < REGISTRY.get("brittle_toughness_threshold"))

    def __repr__(self):
        return f"<Material {self.name}>"


def brittle_materials(table):
    """Materials that fracture rather than deform. Discoverable, not told."""
    return [m for m in table.values() if m.brittle]


def combustible_materials(table):
    return [m for m in table.values() if m.combustible]
