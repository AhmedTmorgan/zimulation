"""
Objects.

An object is a quantity of a material with a shape, a temperature and a
history of damage. It has no type and no name. There is no `axe`, no
`pot`, no `spear`: there is a 0.4 kg piece of flint with an acute edge,
which severs things because of its hardness and its geometry, and which
would do so equally well if nobody had a word for it.

This is the load-bearing choice of the whole rebuild. A model with an
`axe` class has already decided that axes are worth having. This one has
decided only that matter has properties.
"""

from __future__ import annotations

import math

from ..core.parameters import REGISTRY as R
from . import thermal as TH


class Thing:
    """
    A physical object.

    `edge_angle_rad` is the geometry of its sharpest working edge and
    `edge_quality` how cleanly that edge is formed. Together with the
    material's hardness they decide whether it cuts. No other flag says so.
    """

    __slots__ = ("id", "material", "mass_kg", "length_m", "temperature_k",
                 "moisture", "integrity", "edge_angle_rad", "edge_quality",
                 "burning", "position", "attached_to")

    def __init__(self, obj_id, material, mass_kg, length_m,
                 temperature_k=None, moisture=0.0, position=None):
        self.id = obj_id
        self.material = material
        self.mass_kg = mass_kg
        self.length_m = length_m
        self.temperature_k = (R.get("ambient_temperature")
                              if temperature_k is None else temperature_k)
        self.moisture = moisture
        self.integrity = 1.0
        #: a blunt lump has no meaningful edge; a right angle is no edge
        self.edge_angle_rad = math.pi / 2.0
        self.edge_quality = 0.0
        self.burning = None
        self.position = position
        self.attached_to = None

    @property
    def volume_m3(self):
        return self.mass_kg / self.material.density

    @property
    def surface_area_m2(self):
        """
        Surface of an equivalent cylinder of the object's length.

        Shape is approximated because only one consequence matters here:
        thin extended things burn faster than compact ones of equal mass.
        That is the reason kindling behaves as kindling, and it needs no
        concept of kindling to be true.
        """
        v = self.volume_m3
        if self.length_m <= 0.0 or v <= 0.0:
            return 0.0
        radius = math.sqrt(v / (math.pi * self.length_m))
        return 2.0 * math.pi * radius * (radius + self.length_m)

    @property
    def cutting_power(self):
        """
        How well this object severs other material.

        Hardness times edge quality, penalised by a blunt angle. Nothing
        here is a knife; some things simply cut better than others.
        """
        sharp = 1.0 - (self.edge_angle_rad / (math.pi / 2.0))
        return self.material.hardness * self.edge_quality * max(0.0, sharp)

    def __repr__(self):
        b = " burning" if self.burning else ""
        return (f"<Thing {self.id} {self.material.name} "
                f"{self.mass_kg:.2f}kg{b}>")


def strike(striker, target, energy_j, stream):
    """
    One object hits another. Returns any fragments produced.

    A brittle target struck hard enough fractures, and a fine-grained
    brittle material fractures into pieces with acute edges. That is the
    whole mechanism: no knapping skill, no recipe, no unlock. An agent
    that happens to strike flint with granite gets sharp fragments, and
    may or may not ever notice what it has.
    """
    # Which of the two gives way is decided by brittleness, not softness.
    #
    # An earlier version swapped so that the *softer* object took the
    # damage, which sounds right and is wrong: struck with a granite
    # hammer, it is the flint that shatters, and flint is the harder of
    # the two. Hardness decides which surface indents; brittleness decides
    # which body cracks. Getting this backwards closed off the one path by
    # which an edge can exist in this world at all.
    if target.material.brittle:
        pass
    elif striker.material.brittle:
        striker, target = target, striker
    elif striker.material.hardness < target.material.hardness:
        striker, target = target, striker

    threshold = R.get("fracture_energy_scale") * target.mass_kg
    if energy_j < threshold or not target.material.brittle:
        target.integrity = max(0.0, target.integrity - energy_j
                               / (threshold * R.get("blunt_damage_divisor")))
        return []

    n = 2 + int(min(R.get("max_fragments"), energy_j / threshold))
    fragments = []
    total = target.mass_kg
    remaining = total
    for i in range(n):
        if i < n - 1:
            share = remaining * stream.uniform(
                R.get("fragment_share_low"), R.get("fragment_share_high"))
        else:
            share = remaining
        remaining -= share
        if share <= 0.0:
            continue
        f = Thing(None, target.material, share,
                  target.length_m * (share / total) ** (1.0 / 3.0),
                  target.temperature_k, target.moisture, target.position)
        # Conchoidal fracture in fine-grained material leaves an acute
        # edge; coarse material merely crumbles.
        quality = (R.get("conchoidal_edge_quality") * target.material.grain
                   * stream.uniform(R.get("edge_quality_low"), 1.0))
        f.edge_quality = quality
        f.edge_angle_rad = (math.pi / 2.0) * (1.0 - quality)
        fragments.append(f)
    target.mass_kg = 0.0
    target.integrity = 0.0
    return fragments


def rub(a, b, normal_force_n, speed_m_s, dt_s, stream, stroke_m=0.0,
        env_k=None):
    """
    Two objects rubbed together for dt seconds, the contact sweeping back
    and forth over stroke_m. Returns (heat_j, the softer object, contact),
    where contact records how hot the interface got (world.thermal).

    Friction work becomes heat at the interface. How it divides between
    the two bodies, how hot the contact gets, and how much each body warms
    while losing heat to its surroundings are thermal physics. Whether the
    contact ever reaches an ignition temperature depends on force, speed,
    duration, stroke, moisture and material, which is why originating
    combustion this way is difficult and why succeeding is a meaningful
    event rather than a button press.
    """
    from .combustion import friction_energy
    env = R.get("ambient_temperature") if env_k is None else env_k
    soft = a if a.material.hardness <= b.material.hardness else b
    mu = R.get("friction_coefficient_dry")
    heat = friction_energy(normal_force_n, speed_m_s, dt_s, mu)
    heat *= stream.uniform(R.get("friction_jitter_low"),
                           R.get("friction_jitter_high"))
    contact = TH.rub_contact(a, b, heat, dt_s, stroke_m, env)
    return heat, soft, contact
