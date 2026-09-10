"""
Combustion.

There is no `fire` in this model. There is fuel with an ignition
temperature, oxygen, heat that flows, and mass that is consumed. Whether
anything an observer would call fire ever appears is the question, not the
premise.

What that buys is the whole ladder the contract describes. An agent
cannot "use fire" as an action, because no such action exists. It can move
toward a hot region, place a dry stalk into one, carry a smouldering
branch, or rub two sticks hard enough for long enough. Those are physical
acts with physical consequences, and the difference between the third and
the fifth of them is the difference between transporting combustion and
originating it -- a distinction that took hominins a very long time and
which the observer here can measure rather than assume.

Nothing in this module knows about hearths, cooking, warmth-seeking or
tinder. Those are relations an agent might discover between combustion and
its own body.

## What is modelled

Ignition when a fuel reaches its ignition temperature and oxygen is
sufficient. Mass loss at a rate set by burning surface. Heat released in
proportion to mass consumed and the fuel's enthalpy. Radiant transfer to
nearby objects, which can ignite them in turn. Extinction when fuel runs
out, oxygen drops, or moisture rises past the point where the flame
cannot drive off water fast enough to keep pyrolysing.

Moisture matters twice, and both matter to an agent who has never thought
about any of it: wet fuel needs far more energy to start, and above a
moisture fraction it will not sustain a flame at all.
"""

from __future__ import annotations

from ..core.parameters import REGISTRY as R
from .thermal import add_heat, depth_reaching


class Combusting:
    """
    The state of an object that is currently burning.

    Kept separate from the object so that "is burning" is a fact about the
    world at a moment, not a property baked into a thing. A branch is not
    a torch; it is a branch that happens to be burning.
    """

    __slots__ = ("obj", "started_at", "consumed_kg", "smouldering")

    def __init__(self, obj, started_at):
        self.obj = obj
        self.started_at = started_at
        self.consumed_kg = 0.0
        #: smouldering is flameless surface oxidation: it survives being
        #: carried, and it is how combustion travels without an agent
        #: understanding anything about it
        self.smouldering = False


def ignition_energy(obj):
    """
    Energy in joules to bring this object to its ignition temperature.

    Wet fuel costs more, because the water must be driven off before the
    material can pyrolyse. This is why a rain-soaked branch resists every
    effort and a dry stalk catches at once -- a regularity an agent can
    learn without knowing what water is.
    """
    mat = obj.material
    if mat.ignition_point is None:
        return None
    span = max(0.0, mat.ignition_point - obj.temperature_k)
    base = obj.mass_kg * mat.specific_heat * span
    if span <= 0.0:
        base = 0.0
    wet = 1.0 + (R.get("moisture_ignition_penalty") - 1.0) * obj.moisture
    return base * wet


def can_sustain(obj, oxygen_fraction=None):
    """
    Whether flame can persist in this fuel at all.

    Three ways to fail: it does not burn, it is too wet, or there is not
    enough oxygen. Each is a physical fact with no reference to intent.
    """
    mat = obj.material
    if mat.ignition_point is None:
        return False
    if obj.moisture > R.get("moisture_extinction"):
        return False
    o2 = (R.get("oxygen_fraction_sea_level") if oxygen_fraction is None
          else oxygen_fraction)
    return o2 >= R.get("oxygen_extinction_fraction")


def try_ignite(obj, energy_j, at_time, oxygen_fraction=None):
    """
    Apply energy to an object. Returns a `Combusting` if it catches.

    The caller does not say "light this". It delivers energy -- from
    friction, from a spark, from radiant heat off something already
    burning, from a lightning strike -- and physics decides.
    """
    if obj.burning is not None:
        return obj.burning
    need = ignition_energy(obj)
    if need is None or not can_sustain(obj, oxygen_fraction):
        return None
    if energy_j < need:
        # Not enough to ignite, but the energy is not wasted: it warms the
        # object and, once at the boiling point, drives off its water at
        # the latent heat. The first version spent the same joules twice,
        # warming with them and then evaporating with them too. Attempts
        # in quick succession accumulate; with time between them the
        # object cools (world.thermal), so persistence must be sustained.
        add_heat(obj, energy_j)
        return None
    obj.temperature_k = obj.material.ignition_point
    obj.burning = Combusting(obj, at_time)
    return obj.burning


def burn_step(obj, dt_s, oxygen_fraction=None):
    """
    Advance a burning object by dt seconds.

    Returns (heat_released_j, extinguished). Mass is consumed from the
    object, so combustion destroys what it feeds on -- which is the whole
    reason maintaining it requires adding fuel, and the reason maintenance
    is a distinguishable stage from mere use.
    """
    c = obj.burning
    if c is None:
        return 0.0, False
    if not can_sustain(obj, oxygen_fraction) or obj.mass_kg <= 0.0:
        obj.burning = None
        return 0.0, True

    rate = R.get("burn_rate_coefficient") * obj.surface_area_m2
    if c.smouldering:
        rate *= R.get("smoulder_rate_fraction")
    consumed = min(obj.mass_kg, rate * dt_s)
    obj.mass_kg -= consumed
    c.consumed_kg += consumed

    heat = consumed * obj.material.combustion_enthalpy
    if obj.mass_kg <= 0.0:
        obj.burning = None
        return heat, True
    return heat, False


def radiant_reach(heat_release_w):
    """
    How far this release can ignite something else.

    A crude proxy for a view-factor calculation: hotter sources reach
    further. What matters for the experiment is only that combustion can
    spread between adjacent objects, so that a burn can propagate through
    a fuel bed and so that an agent's own gathered pile behaves the way a
    pile of sticks behaves.
    """
    base = R.get("radiant_ignition_distance")
    scale = max(0.0, heat_release_w) ** R.get("radiant_reach_exponent")
    return base * scale


def spread(source_obj, neighbours, dt_s, at_time, oxygen_fraction=None):
    """
    Radiant ignition of nearby objects by one that is burning.

    `neighbours` is a sequence of (object, distance_m). Returns the list
    that caught. Nothing here consults intent, ownership or purpose: a
    burning branch ignites a dry stalk beside it whether the stalk was
    placed there by an agent, by a river, or by nothing at all.
    """
    c = source_obj.burning
    if c is None:
        return []
    power = (R.get("burn_rate_coefficient") * source_obj.surface_area_m2
             * source_obj.material.combustion_enthalpy)
    reach = radiant_reach(power)
    caught = []
    for obj, dist in neighbours:
        if obj is source_obj or obj.burning is not None or dist > reach:
            continue
        fall = (1.0 - dist / reach) ** 2
        delivered = power * fall * dt_s * R.get("radiant_capture_fraction")
        if try_ignite(obj, delivered, at_time, oxygen_fraction) is not None:
            caught.append(obj)
    return caught


def friction_energy(normal_force_n, speed_m_s, dt_s, friction_coefficient):
    """
    Heat delivered at a rubbed interface.

    Work is force times distance; a share of it stays as heat in the
    contact zone rather than conducting away. This is the only route by
    which an agent's own muscles can originate combustion, and it is
    deliberately hard: the numbers are such that idle rubbing does nothing
    and sustained, forceful, fast rubbing on dry fine fuel can just
    succeed.
    """
    work = normal_force_n * friction_coefficient * speed_m_s * dt_s
    return work * R.get("friction_heat_efficiency")


def ignite_contact(contact, at_time, oxygen_fraction=None):
    """
    Whether a rubbed contact left a smouldering mass of heated surface.

    Where the contact passed a combustible surface's ignition temperature,
    the material heated past that point -- a thin disc under the contact,
    as deep as the heat front carried the ignition temperature -- becomes a
    separate small object, smouldering. Returns it, or None. It is small
    and flameless; left alone it burns out, and whether it ever becomes
    anything more depends on what it is put beside.
    """
    from .objects import Thing
    if not contact.dry or contact.peak_k <= contact.start_k:
        return None
    bodies = contact.bodies
    order = sorted(range(len(bodies)), key=lambda i: (
        bodies[i].material.ignition_point is None,
        bodies[i].material.ignition_point or 0.0, i))
    for i in order:
        body = bodies[i]
        mat = body.material
        if mat.ignition_point is None or contact.peak_k < mat.ignition_point:
            continue
        if not can_sustain(body, oxygen_fraction):
            continue
        fraction = ((mat.ignition_point - contact.start_k)
                    / (contact.peak_k - contact.start_k))
        depth = depth_reaching(fraction, mat, contact.duration_s)
        mass = min(body.mass_kg, mat.density * contact.areas[i] * depth)
        if mass <= 0.0:
            continue
        ember = Thing(None, mat, mass, depth, contact.peak_k, 0.0,
                      body.position)
        lit = try_ignite(ember, 0.0, at_time, oxygen_fraction)
        if lit is None:
            continue
        body.mass_kg -= mass
        lit.smouldering = True
        return ember
    return None
