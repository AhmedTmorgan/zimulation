"""
Perception: the only door through which the world gets into a mind.

Everything an agent will ever know about its world arrives here first, as
a noisy, local, partial reading. That makes this module the front line of
the ground-truth barrier, and it is built around three restrictions.

**Local only.** A percept is of something within sight, sound or reach.
Nothing here can take the terrain as a whole; the functions receive the
one cell being looked at and the one being looked from. Contract section
49 forbids global queries, and a test checks that no cognition module
calls the observer-only `all_cells`.

**Properties, never names.** Handling a lump of flint yields heft,
hardness and edge -- not the string "flint". Seeing something burn yields
brightness and warmth -- not a concept of fire. Any category an agent
eventually holds has to be built from these readings.

**Noise that has causes.** Magnitudes follow Weber's law: the error scales
with what is being judged. Senses dim with age (development's
`sensory_acuity`) and with a body's own state -- a tired, hurting, thirsty
body perceives worse. That is one physical root of bounded rationality,
and none of it is a trait called foolishness.

Temperature is felt relative to thermal neutrality, not read off in
kelvin. Warm and cold are departures from comfort, which is how thermal
sensation actually works and why the same room feels different to a body
coming in from the snow.

Interoception -- hunger, thirst, cold, pain, sleepiness -- arrives on its
own channel with no subject. The body is not yet anything the agent has a
concept of; section 40 forbids beginning with an explicit self, and the
distinction between body and world is carried here by the channel alone.
"""

from __future__ import annotations

from ..core.parameters import REGISTRY as R
from ..core.scheduler import HOUR

SIGHT = "sight"
SOUND = "sound"
TOUCH = "touch"
INTERNAL = "internal"


class Percept:
    """
    One reading of the world or the body.

    `subject` is an opaque handle -- an object id or a place -- never the
    object itself, so that nothing downstream can reach through a percept
    to properties the senses did not report.
    """

    __slots__ = ("time", "channel", "subject", "features", "place")

    def __init__(self, time, channel, subject, features, place):
        self.time = time
        self.channel = channel
        self.subject = subject
        self.features = features
        self.place = place

    def __repr__(self):
        return f"<Percept {self.channel} {self.subject} {sorted(self.features)}>"


def _unit(x):
    return max(0.0, min(1.0, x))


def _noise_scale(acuity, impairment):
    """How much worse than ideal this observer's senses are right now."""
    return ((1.0 + R.get("impairment_noise_gain") * impairment)
            / max(R.get("division_epsilon"), acuity))


def _relative(value, rel_sd, stream):
    """A magnitude judged with Weber-law error: proportional to itself."""
    return value * max(0.0, stream.gauss(1.0, rel_sd))


def _felt_warmth(temperature_k, scale, stream):
    """Temperature as departure from thermal neutrality, with noise."""
    return (temperature_k - R.get("thermal_comfort_ambient_k")
            + stream.gauss(0.0, R.get("thermal_sensation_sd_k") * scale))


def _radiant_power_w(thing):
    """Output of a burning thing -- what reaches the eye and skin."""
    return (R.get("burn_rate_coefficient") * thing.surface_area_m2
            * thing.material.combustion_enthalpy)


def sense_thing(thing, thing_cell, viewer_cell, terrain, time, acuity,
                impairment, stream, touching=False):
    """
    Perceive one object. Returns a Percept, or None if it cannot be sensed.

    By sight: apparent size, and brightness if it is burning. By touch:
    heft, hardness, edge, wetness and warmth as well. Hardness and edge are
    unavailable to the eye -- a sharp flake and a dull pebble can look
    alike, and telling them apart takes handling.
    """
    scale = _noise_scale(acuity, impairment)
    weber = R.get("weber_fraction_magnitude") * scale
    feel = R.get("touch_property_sd") * scale
    features = {}

    if touching:
        channel = TOUCH
        features["heft"] = _relative(thing.mass_kg, weber, stream)
        features["hardness_felt"] = _unit(
            thing.material.hardness + stream.gauss(0.0, feel))
        features["edge_felt"] = _unit(
            thing.cutting_power + stream.gauss(0.0, feel))
        features["wetness_felt"] = _unit(
            thing.moisture + stream.gauss(0.0, feel))
        features["warmth_felt"] = _felt_warmth(thing.temperature_k, scale,
                                               stream)
    else:
        from ..world.space import visible_from
        if not visible_from(terrain, viewer_cell, thing_cell):
            return None
        channel = SIGHT
        features["apparent_size"] = _relative(thing.volume_m3, weber, stream)

    if thing.burning is not None:
        # Light and heat reach the eye and skin. Nothing names their cause.
        glow = _radiant_power_w(thing) / R.get("brightness_saturation_w")
        features["brightness"] = _unit(glow + stream.gauss(0.0, feel))

    return Percept(time, channel, thing.id, features,
                   (thing_cell.x, thing_cell.y))


def sense_ambient(cell, temperature_k, time, acuity, impairment, stream):
    """The feel of the place a body is in: warmth, wet ground, water."""
    scale = _noise_scale(acuity, impairment)
    feel = R.get("touch_property_sd") * scale
    return Percept(time, TOUCH, ("place", cell.x, cell.y), {
        "warmth_felt": _felt_warmth(temperature_k, scale, stream),
        "ground_wetness": _unit(cell.moisture + stream.gauss(0.0, feel)),
        "standing_water": _unit(cell.water_fraction
                                + stream.gauss(0.0, feel)),
    }, (cell.x, cell.y))


def sense_body(body, time, stream):
    """
    Interoception: the body's own signals.

    These are signals, not readings of physiology. The organism feels
    hunger, not a fat fraction; pain, not a damage total. The mapping from
    one to the other is fixed by the body, and the organism never sees the
    quantity underneath.

    Hunger has a fast part, which nutrients in the stomach quiet -- water
    fills it and does not (Williams et al. 2003) -- as well as the slow
    part of depleted reserves; thirst counts water already swallowed, as
    people's does; fullness is the stomach's stretch. Without these a meal moved
    the hunger signal by about a hundredth, below this function's own
    noise, and eating could never have been learned from the body.
    """
    sd = R.get("interoception_sd")
    drop = R.get("core_temperature_k") - body.core_temperature_k
    scale_k = R.get("cold_signal_scale_k")
    full_water = body.mass_kg * R.get("water_fraction_of_mass")
    short = max(0.0, full_water - body.water_kg - body.gut_water_kg)
    raw = {
        "hunger": (1.0 - body.fat_fraction / R.get("fat_fraction_healthy")
                   + R.get("emptiness_hunger_weight")
                   * (1.0 - body.satiety)),
        "thirst": short / max(R.get("division_epsilon"), full_water
                              * R.get("dehydration_lethal_fraction")),
        "fullness": body.fullness,
        "cold": drop / scale_k,
        "heat": -drop / scale_k,
        "pain": body.pain,
        "sleepiness": body.sleep_debt_s / (R.get("sleep_debt_impairment_h")
                                           * HOUR),
    }
    feats = {k: _unit(_unit(v) + stream.gauss(0.0, sd))
             for k, v in raw.items()}
    return Percept(time, INTERNAL, None, feats, None)
