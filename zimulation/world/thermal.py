"""
Heat: how things warm, dry and cool, and how a rubbed contact gets hot.

Three errors in the first physics motivated this module. Each was found by
driving the world with a body instead of injecting numbers.

- Nothing ever cooled. Heat put into a stick stayed there for ever, so a
  minute of rubbing a day for a fortnight would eventually have lit it.
  Objects now exchange heat with their surroundings by convection and
  radiation (Newton's law, radiation linearised), solved exactly over any
  time step.

- Heating a damp thing ignored the latent heat of its water. A stick at 30%
  moisture was rubbed to its ignition point still holding all of it, and
  the failed-ignition path spent the same joules twice -- once warming,
  once evaporating. Heat now warms a thing to the boiling point, then
  drives its water off at the latent heat, and only then warms it further.
  Energy is conserved, and a test checks it to rounding error.

- With cooling in place, heating a whole stick evenly would have closed the
  route to friction ignition altogether: a thin stick loses heat about as
  fast as an arm puts it in, levelling off near 370 K. Real friction
  ignition works because the heat is concentrated at the contact and wood
  conducts it away slowly. The contact is now two semi-infinite solids
  sharing a constant surface flux (Carslaw & Jaeger 1959, Conduction of
  Heat in Solids): the contact temperature rises with the square root of
  time and falls with the sum of the two materials' thermal effusivities,
  sqrt(k rho c). That one quantity is why wood on wood can glow and stone
  on stone cannot -- stone's effusivity is five to eight times wood's --
  without anything having to say so.

A contact that slides back and forth spreads its heat along the track it
sweeps, and the time-averaged flux over the track is used (the limit of a
fast-moving source). How far and how fast an arm can stroke is the body's
business, not this module's.

## Measured (ten seeds; an adult body; dry softwood on hardwood)

The shortest unbroken bout that leaves an ember at the best stroke is 132
to 225 seconds (mean 166), costing the body 24 to 41 kJ. A single minute
never suffices, and ten one-minute bouts an hour apart light nothing.
After two minutes the contact reaches 456 K with a 2 cm stroke, 544 K at
15 cm and 369 K at 50 cm: the arm's oscillation limit and the spreading of
heat along the track make a best stroke that no rule names. Ten-minute
bouts leave embers of 0.5 to 0.7 g.

## Known simplifications

Dust is not modelled. In practice an ember forms from abraded dust that
collects in a notch, and that is part of why friction fire takes practice;
here the ember is the surface material heated past its ignition point.

Each continuous bout is computed from the bulk temperatures at its start,
so any pause forfeits the contact's heat. This errs toward making fire
harder, not easier.

Moisture resists less than it does in practice. Only the water within the
heated layer is charged its latent heat, whereas real damp wood keeps
wicking water to the contact and its dust will not ember; wood much above
fifteen percent moisture rarely yields an ember at all. Fuel wetter than
the extinction moisture never embers here.

Evaporation below the boiling point -- slow drying in air -- is not
modelled.

A lone ember here lasts about half an hour, burning itself away; a real
one left alone dies within minutes, losing heat faster than it smoulders.
Combustion has no critical-size extinction yet, so this errs toward giving
an agent more time to carry an ember to fuel than reality would.
"""

from __future__ import annotations

import math

from ..core.parameters import REGISTRY as R


# ------------------------------------------------------------ properties
def heat_capacity(thing):
    """J/K: the material's specific heat times the thing's mass."""
    return max(R.get("division_epsilon"),
               thing.mass_kg * thing.material.specific_heat)


def effusivity(material):
    """sqrt(k rho c): how strongly a surface draws heat from a contact."""
    return math.sqrt(material.conductivity * material.density
                     * material.specific_heat)


def diffusivity(material):
    """k / (rho c), m^2 s^-1: how fast heat soaks into a material."""
    return material.conductivity / (material.density
                                    * material.specific_heat)


def cross_section(thing):
    """Area of the end of a thing treated as a rod: volume over length."""
    return thing.volume_m3 / max(R.get("division_epsilon"), thing.length_m)


# ------------------------------------------------------ warming, drying
def drive_off_water(thing, kg):
    """Remove up to kg of held water; the thing ends lighter and drier."""
    water = thing.moisture * thing.mass_kg
    kg = min(max(0.0, kg), water)
    if kg <= 0.0:
        return 0.0
    thing.mass_kg -= kg
    left = water - kg
    thing.moisture = (left / thing.mass_kg
                      if left > 0.0 and thing.mass_kg > 0.0 else 0.0)
    return kg


def add_heat(thing, joules):
    """
    Deliver heat, conserving energy. It warms the thing up to the boiling
    point; water still held pins it there until the latent heat has driven
    that water off; only then does it warm further. Negative heat cools it.
    Returns the mass of water driven off.
    """
    if joules <= 0.0:
        thing.temperature_k += joules / heat_capacity(thing)
        return 0.0
    boil = R.get("boiling_point_water_k")
    if thing.moisture > 0.0 and thing.temperature_k < boil:
        warm = min(joules,
                   (boil - thing.temperature_k) * heat_capacity(thing))
        thing.temperature_k += warm / heat_capacity(thing)
        joules -= warm
    driven = 0.0
    if thing.moisture > 0.0 and joules > 0.0:
        latent = R.get("latent_heat_vaporisation_water")
        driven = drive_off_water(thing, joules / latent)
        joules -= driven * latent
    thing.temperature_k += joules / heat_capacity(thing)
    return driven


# ---------------------------------------------------------------- cooling
def loss_coefficient(thing, env_k):
    """W/K lost to the surroundings: convection plus linearised radiation."""
    t, e = thing.temperature_k, env_k
    radiative = (R.get("surface_emissivity") * R.get("stefan_boltzmann")
                 * (t * t + e * e) * (t + e))
    return ((R.get("convective_coefficient") + radiative)
            * thing.surface_area_m2)


def heat_steadily(thing, joules, dt_s, env_k):
    """
    Deliver heat at a steady rate over dt while the thing exchanges heat
    with its surroundings. The exact solution of Newton's law with a
    constant source gives what is retained, which then passes through
    add_heat so that held water takes its latent heat.
    """
    if dt_s <= 0.0:
        return add_heat(thing, joules)
    c = heat_capacity(thing)
    k = max(R.get("division_epsilon"), loss_coefficient(thing, env_k))
    t0 = thing.temperature_k
    steady = env_k + (joules / dt_s) / k
    t1 = steady + (t0 - steady) * math.exp(-k * dt_s / c)
    return add_heat(thing, c * (t1 - t0))


def exchange_heat(thing, env_k, dt_s):
    """Let a thing relax toward its surroundings for dt. Burning things
    are governed by combustion instead."""
    if thing.burning is not None:
        return 0.0
    return heat_steadily(thing, 0.0, dt_s, env_k)


# ---------------------------------------------------------------- contact
class Contact:
    """What one bout of rubbing did at the interface."""

    __slots__ = ("bodies", "areas", "start_k", "peak_k", "duration_s",
                 "dry")

    def __init__(self, bodies, areas, start_k, peak_k, duration_s, dry):
        self.bodies = bodies
        self.areas = areas
        self.start_k = start_k
        self.peak_k = peak_k
        self.duration_s = duration_s
        self.dry = dry


def profile(u):
    """
    Temperature below a surface under constant flux, as a fraction of the
    surface rise, at depth u = z / (2 sqrt(alpha t)) (Carslaw & Jaeger).
    Falls from one at the surface toward zero.
    """
    return math.exp(-u * u) - u * math.sqrt(math.pi) * math.erfc(u)


def depth_reaching(fraction, material, duration_s):
    """How deep, in metres, the material was heated past the given
    fraction of the surface rise."""
    if fraction >= 1.0:
        return 0.0
    lo, hi = 0.0, 3.0
    eps = R.get("division_epsilon")
    while hi - lo > eps:
        mid = 0.5 * (lo + hi)
        if profile(mid) > fraction:
            lo = mid
        else:
            hi = mid
    return 2.0 * lo * math.sqrt(diffusivity(material) * duration_s)


def rub_contact(a, b, heat_j, dt_s, stroke_m, env_k):
    """
    Where a bout of friction heat goes, and how hot the contact gets.

    The heat divides between the two bodies in proportion to their
    effusivities, which is what keeps both surfaces at one temperature. The
    contact face of the thinner body is its end; the thicker body is heated
    along the whole track the contact sweeps. If the contact would pass the
    boiling point, the water in each heated surface layer must first be
    driven off. The rest of the heat warms each body as a whole, which
    meanwhile loses heat to its surroundings.
    """
    eps = R.get("division_epsilon")
    dt = max(0.0, dt_s)
    ea, eb = effusivity(a.material), effusivity(b.material)
    ca, cb = cross_section(a), cross_section(b)
    tip = min(ca, cb)
    swept = tip + 2.0 * math.sqrt(tip / math.pi) * max(0.0, stroke_m)
    areas = (tip, swept) if ca <= cb else (swept, tip)
    start = (ea * a.temperature_k + eb * b.temperature_k) / (ea + eb)
    rise = (2.0 * heat_j / (max(eps, dt) * swept)
            * math.sqrt(dt / math.pi) / (ea + eb))
    boil = R.get("boiling_point_water_k")
    latent = R.get("latent_heat_vaporisation_water")
    hot = start + rise > boil
    wet = 0.0
    for body, e, area in ((a, ea, areas[0]), (b, eb, areas[1])):
        into = heat_j * e / (ea + eb)
        driven = 0.0
        if hot and body.moisture > 0.0:
            depth = math.sqrt(diffusivity(body.material) * dt)
            water = body.moisture * body.material.density * area * depth
            wet = max(wet, water * latent / max(eps, into))
            driven = drive_off_water(body, min(water, into / latent))
        heat_steadily(body, into - driven * latent, dt, env_k)
    if wet >= 1.0:
        peak = max(start, boil)
    elif wet > 0.0:
        peak = max(boil, start + rise * math.sqrt(1.0 - wet))
    else:
        peak = start + rise
    return Contact((a, b), areas, start, peak, dt, wet < 1.0)
