"""
Sensorimotor primitives: everything a body can do, and nothing it can mean.

Zimulation 1 gave its agents actions like farm, herd, preach, ritual and
teach. Each of those already contains a civilisation: to have `farm` as an
option is to have been told that planting is a thing. Section 8 of the
contract replaces them with the acts a body can perform on the world --
move, grasp, strike, rub, throw, cut, bind, eat, call -- and requires that
anything more be composed from sequences of these.

So there is no hunting here, only moving, throwing and striking. No
cooking, only placing one thing near another that happens to be hot. No
tool-making, only striking stone with stone -- and whether what falls off
is ever picked up and used is the open question.

## Every act is paid for and physically gated

Each primitive does work on the world, and the work is paid from the
body's energy store at the efficiency of muscle (about a fifth). Each is
limited by the body's strength, which rises through childhood, peaks, and
declines -- so a child cannot knap a large core and an old body throws
less far, without any rule saying either.

And each has its effect only through the world's own physics. A strike
delivers kinetic energy to `objects.strike`, which decides whether
anything fractures. A rub delivers heat to `objects.rub`; whether
anything catches is decided by the contact's thermal physics and
`combustion.ignite_contact`. No primitive
creates combustion, an edge or a meal by assignment; a test checks that
this module never sets anything burning directly.

## A correction found by building this

The world's fracture threshold was first set so that a hand-sized flint
core needed about 8,400 J to break -- three hundred times the ~25 J of a
real overarm blow. The physics test passed because it injected energy
directly; no arm could ever have done it, which would have closed the one
physical route to a cutting edge. The first test here asks whether a human
arm can knap flint, which is the question that exposed it.

## Signals

`emit_signal` makes a sound carrying a token and a loudness. The token is
whatever the agent chose; the sound has no meaning and this module gives
it none. Meaning, if it arises, is the business of communication and of
the agents themselves (contract section 20).
"""

from __future__ import annotations

import math

from ..biology import physiology as PHY
from ..biology.development import sensory_acuity, strength
from ..cognition import perception as PC
from ..core.parameters import REGISTRY as R
from ..world import combustion as C
from ..world import objects as O
from ..world.space import audible_from, travel_cost_s


class Actor:
    """
    The physical side of an agent: a body, a genome, a place, and what is
    in its hands. Cognition attaches elsewhere; this is only what can act.
    """

    __slots__ = ("id", "body", "genome", "cell", "held")

    def __init__(self, actor_id, body, genome, cell):
        self.id = actor_id
        self.body = body
        self.genome = genome
        self.cell = cell
        self.held = []

    @property
    def capacity(self):
        """Physical capacity relative to a reference adult at peak."""
        return max(0.0, strength(self.genome, self.body))

    @property
    def here(self):
        return (self.cell.x, self.cell.y)


class Act:
    """What a primitive did: how long, how much energy, what changed."""

    __slots__ = ("name", "duration_s", "energy_j", "outcome")

    def __init__(self, name, duration_s, energy_j, outcome):
        self.name = name
        self.duration_s = duration_s
        self.energy_j = energy_j
        self.outcome = outcome

    @property
    def done(self):
        return not self.outcome.get("refused")

    def __repr__(self):
        return f"<Act {self.name} {self.duration_s:.1f}s {self.energy_j:.0f}J>"


class Signal:
    """A sound made on purpose: a token and a loudness, and no meaning."""

    __slots__ = ("token", "emitter", "place", "loudness", "time")

    def __init__(self, token, emitter, place, loudness, time):
        self.token = token
        self.emitter = emitter
        self.place = place
        self.loudness = loudness
        self.time = time


# ----------------------------------------------------------------- helpers
def _refuse(name, why):
    return Act(name, 0, 0.0, {"refused": why})


def _quick():
    return R.get("action_duration_s")


def _charge(actor, mechanical_j):
    """Metabolic cost of external work, drawn from the energy store."""
    metabolic = max(0.0, mechanical_j) / R.get("muscle_efficiency")
    PHY.spend_energy(actor.body, metabolic)
    return metabolic


def _reachable(actor, thing):
    return thing in actor.held or thing.position == actor.here


def _put_down(actor, thing):
    thing.position = actor.here
    if thing not in actor.cell.things:
        actor.cell.things.append(thing)


def _drop_spent(actor):
    """Anything that no longer has mass -- broken up, eaten -- is gone,
    from the hand and from the ground alike. (The first version cleared
    only the hand, so a core struck to pieces stayed lying there with no
    mass, still perceivable.)"""
    actor.held = [t for t in actor.held if t.mass_kg > 0.0]
    actor.cell.things = [t for t in actor.cell.things if t.mass_kg > 0.0]


def _step_toward(terrain, here, target, sign):
    best, score = None, None
    for c in terrain.neighbours(here.x, here.y):
        d = sign * terrain.distance_m(c, target)
        if score is None or d < score:
            best, score = c, d
    return best


# ------------------------------------------------------------------ motion
def move(actor, terrain, to_cell):
    """
    One step to a neighbouring cell. Longer journeys are sequences.

    Walking costs energy above resting, more when laden, and climbing takes
    longer and so costs more still. A body with little strength walks
    slowly; a newborn does not walk at all.
    """
    if to_cell is None or to_cell not in terrain.neighbours(actor.cell.x,
                                                            actor.cell.y):
        return _refuse("move", "not adjacent")
    eps = R.get("division_epsilon")
    speed = R.get("walking_speed_m_s") * min(1.0, actor.capacity)
    if speed <= eps:
        return _refuse("move", "cannot walk")
    duration = travel_cost_s(terrain, actor.cell, to_cell, speed)
    load = sum(t.mass_kg for t in actor.held)
    extra = ((R.get("activity_multiplier_walking") - 1.0)
             * (1.0 + load / max(eps, actor.body.mass_kg)))
    energy = PHY.resting_rate_w(actor.body) * extra * duration
    PHY.spend_energy(actor.body, energy)
    actor.cell = to_cell
    for t in actor.held:
        t.position = actor.here
    return Act("move", duration, energy, {"moved": True})


def approach(actor, terrain, target_cell):
    """Step to whichever neighbour brings the target nearer."""
    return move(actor, terrain,
                _step_toward(terrain, actor.cell, target_cell, 1.0))


def avoid(actor, terrain, target_cell):
    """Step to whichever neighbour takes the target further away."""
    return move(actor, terrain,
                _step_toward(terrain, actor.cell, target_cell, -1.0))


# --------------------------------------------------------------- handling
def grasp(actor, thing):
    """Pick something up, if it is within reach, a hand is free, and the
    body is strong enough to lift it."""
    if len(actor.held) >= int(R.get("grasp_capacity")):
        return _refuse("grasp", "hands full")
    if thing in actor.held or thing.position != actor.here:
        return _refuse("grasp", "out of reach")
    if thing.mass_kg > R.get("max_lift_kg") * actor.capacity:
        return _refuse("grasp", "too heavy")
    energy = _charge(actor, thing.mass_kg * R.get("gravity")
                     * R.get("lift_height_m"))
    actor.held.append(thing)
    if thing in actor.cell.things:
        actor.cell.things.remove(thing)
    return Act("grasp", _quick(), energy, {"held": True})


def release(actor, thing):
    """Let go of something; it stays where the body is."""
    if thing not in actor.held:
        return _refuse("release", "not held")
    actor.held.remove(thing)
    _put_down(actor, thing)
    return Act("release", _quick(), 0.0, {"released": True})


def transfer_object(actor, other, thing):
    """Put a held thing into another body's free hand."""
    if thing not in actor.held:
        return _refuse("transfer_object", "not held")
    if other.cell is not actor.cell:
        return _refuse("transfer_object", "out of reach")
    if len(other.held) >= int(R.get("grasp_capacity")):
        return _refuse("transfer_object", "hands full")
    actor.held.remove(thing)
    other.held.append(thing)
    return Act("transfer_object", _quick(), 0.0, {"transferred": True})


def apply_force(actor, thing, terrain, to_cell):
    """Shove or drag an unheld thing to a neighbouring cell against
    sliding friction. Push and pull are the same act on the world."""
    if thing in actor.held or thing.position != actor.here:
        return _refuse("apply_force", "out of reach")
    if to_cell not in terrain.neighbours(actor.cell.x, actor.cell.y):
        return _refuse("apply_force", "not adjacent")
    need = R.get("friction_coefficient_dry") * thing.mass_kg * R.get("gravity")
    if need > R.get("max_push_force_n") * actor.capacity:
        return _refuse("apply_force", "too heavy")
    distance = terrain.distance_m(actor.cell, to_cell)
    energy = _charge(actor, need * distance)
    if thing in actor.cell.things:
        actor.cell.things.remove(thing)
    actor.cell = to_cell
    _put_down(actor, thing)
    speed = R.get("walking_speed_m_s") * min(1.0, actor.capacity)
    return Act("apply_force",
               distance / max(R.get("division_epsilon"), speed),
               energy, {"moved_thing": True})


def throw(actor, thing, terrain, toward_cell):
    """
    Launch a held thing toward a place. The arm delivers roughly fixed
    energy, so heavy things leave the hand slower; range is that of the
    best launch angle. Nothing decides what the throw is for.
    """
    if thing not in actor.held:
        return _refuse("throw", "not held")
    ref = R.get("throw_reference_mass_kg")
    speed = (R.get("throw_speed_m_s") * actor.capacity
             * math.sqrt(min(1.0, ref / max(R.get("division_epsilon"),
                                            thing.mass_kg))))
    reach = speed * speed / R.get("gravity")
    energy = _charge(actor, 0.5 * thing.mass_kg * speed * speed)
    dest, gone = actor.cell, 0.0
    while True:
        nxt = _step_toward(terrain, dest, toward_cell, 1.0)
        if nxt is None:
            break
        step = terrain.distance_m(dest, nxt)
        if (gone + step > reach or terrain.distance_m(nxt, toward_cell)
                >= terrain.distance_m(dest, toward_cell)):
            break
        dest, gone = nxt, gone + step
    actor.held.remove(thing)
    thing.position = (dest.x, dest.y)
    dest.things.append(thing)
    return Act("throw", _quick(), energy,
               {"landed": (dest.x, dest.y), "range_m": reach})


# ---------------------------------------------------- acting on matter
def strike(actor, striker, target, stream):
    """
    Hit one thing with another held in the hand. The blow's kinetic energy
    goes to the world's fracture physics, which alone decides whether
    anything breaks and what edges result.
    """
    if striker not in actor.held:
        return _refuse("strike", "striker not held")
    if not _reachable(actor, target) or target is striker:
        return _refuse("strike", "out of reach")
    speed = R.get("strike_speed_m_s") * actor.capacity
    impact = 0.5 * striker.mass_kg * speed * speed
    energy = _charge(actor, impact)
    fragments = O.strike(striker, target, impact, stream)
    for f in fragments:
        _put_down(actor, f)
    _drop_spent(actor)
    return Act("strike", _quick(), energy,
               {"fragments": len(fragments), "impact_j": impact})


def rub(actor, a, b, duration_s, stream, now=0, stroke_m=None):
    """
    Rub one held thing against another for a while, the hand moving back
    and forth over a stroke. Friction heats the contact; whether anything
    catches is for the thermal and combustion physics to decide, never
    this function.

    An arm cannot oscillate faster than a few strokes a second, so a short
    stroke is a slow one; a long stroke is fast but spreads its heat along
    the track. That trade-off belongs to the body and the world. Nothing
    here says which stroke works.
    """
    if a not in actor.held or not _reachable(actor, b) or a is b:
        return _refuse("rub", "out of reach")
    stroke = R.get("rub_stroke_m") if stroke_m is None else stroke_m
    stroke = min(max(0.0, stroke), R.get("max_stroke_m"))
    force = R.get("rub_force_n") * actor.capacity
    speed = min(R.get("rub_speed_m_s") * actor.capacity,
                2.0 * stroke * R.get("max_stroke_frequency_hz"))
    heat, _, contact = O.rub(a, b, force, speed, duration_s, stream,
                             stroke_m=stroke, env_k=actor.cell.temperature_k)
    work = force * R.get("friction_coefficient_dry") * speed * duration_s
    energy = _charge(actor, work)
    ember = C.ignite_contact(contact, now)
    if ember is not None:
        _put_down(actor, ember)
    return Act("rub", duration_s, energy,
               {"heat_j": heat, "contact_k": contact.peak_k,
                "burning": ember is not None, "ember": ember})


def separate(actor, cutter, target, stream):
    """
    Draw an edge through something. It parts only if the edge's cutting
    power, backed by the body's strength, exceeds the material's toughness
    -- so a flake parts flesh and a blunt stone does not. Each stroke dulls
    the edge a little.
    """
    if cutter not in actor.held:
        return _refuse("separate", "cutter not held")
    if not _reachable(actor, target) or target is cutter:
        return _refuse("separate", "out of reach")
    energy = _charge(actor, R.get("manual_stroke_work_j"))
    power = cutter.cutting_power * actor.capacity * R.get("cut_leverage")
    cutter.edge_quality *= 1.0 - R.get("edge_wear_per_cut")
    if power <= target.material.toughness or target.mass_kg <= 0.0:
        return Act("separate", _quick(), energy, {"separated": False})
    half = target.mass_kg * 0.5
    piece = O.Thing(None, target.material, half, target.length_m * 0.5,
                    target.temperature_k, target.moisture, actor.here)
    target.mass_kg -= half
    target.length_m *= 0.5
    _put_down(actor, piece)
    return Act("separate", _quick(), energy, {"separated": True})


def _binds(thing):
    m = thing.material
    return (m.toughness >= R.get("binding_toughness")
            and m.elasticity >= R.get("binding_elasticity"))


def combine(actor, a, b):
    """
    Wrap one thing round another. It holds only if one of them is a
    strand tough and flexible enough to bind -- fibre does, dry grass
    snaps. What the combination is good for is not this function's affair.
    """
    if not (_reachable(actor, a) and _reachable(actor, b)) or a is b:
        return _refuse("combine", "out of reach")
    energy = _charge(actor, R.get("manual_stroke_work_j"))
    binder = a if _binds(a) else (b if _binds(b) else None)
    if binder is None:
        return Act("combine", _quick(), energy, {"combined": False})
    binder.attached_to = b if binder is a else a
    return Act("combine", _quick(), energy, {"combined": True})


def consume(actor, thing):
    """
    Take one mouthful into the stomach, if it has room. The body later
    gains whatever energy the material holds for an organism -- which may
    be none -- and at once suffers whatever its toxicity does. Only what a
    jaw can break can be eaten at all.
    """
    if not _reachable(actor, thing):
        return _refuse("consume", "out of reach")
    if thing.material.hardness > R.get("bite_hardness_max"):
        return _refuse("consume", "too hard to bite")
    bite = min(thing.mass_kg, R.get("bite_mass_kg"))
    if bite <= 0.0:
        return _refuse("consume", "nothing left")
    bite = min(bite, PHY.stomach_room(actor.body))
    if bite <= 0.0:
        return _refuse("consume", "stomach full")
    gained = PHY.feed(actor.body, bite, thing.material.nutritive_energy,
                      water_fraction=thing.moisture)
    if thing.material.toxicity > 0.0:
        PHY.injure(actor.body, thing.material.toxicity * bite
                   * R.get("toxic_damage_per_kg"))
        PHY.check_viability(actor.body)
    thing.mass_kg -= bite
    _drop_spent(actor)
    return Act("consume", R.get("bite_duration_s"), 0.0,
               {"ingested_kg": bite, "energy_j": gained})


# ---------------------------------------------------------------- senses
def _acuity(actor):
    return sensory_acuity(actor.body.age_years)


def touch(actor, thing, stream, now=0):
    """Handle something and feel it: heft, hardness, edge, wet, warm."""
    if not _reachable(actor, thing):
        return _refuse("touch", "out of reach")
    p = PC.sense_thing(thing, actor.cell, actor.cell, None, now,
                       _acuity(actor), actor.body.impairment, stream,
                       touching=True)
    return Act("touch", _quick(), 0.0, {"percept": p})


def look(actor, thing, thing_cell, terrain, stream, now=0):
    """Look at something, if it can be seen from here."""
    p = PC.sense_thing(thing, thing_cell, actor.cell, terrain, now,
                       _acuity(actor), actor.body.impairment, stream)
    if p is None:
        return _refuse("look", "not visible")
    return Act("look", _quick(), 0.0, {"percept": p})


# --------------------------------------------------------------- signals
def emit_signal(actor, token, loudness, now=0):
    """Make a sound carrying a chosen token. It means nothing."""
    loud = max(0.0, min(1.0, loudness))
    energy = _charge(actor, R.get("vocal_work_j") * loud)
    return Act("emit_signal", _quick(), energy,
               {"signal": Signal(token, actor.id, actor.here, loud, now)})


def listen(actor, terrain, signals):
    """Whichever of these sounds reach this body from where it stands."""
    heard = []
    for s in signals:
        src = terrain.at(*s.place)
        if src is not None and audible_from(terrain, src, actor.cell,
                                            s.loudness):
            heard.append(s)
    return Act("listen", _quick(), 0.0, {"heard": heard})


def rest(actor, duration_s):
    """Do nothing in particular for a while."""
    return Act("rest", duration_s, 0.0, {"resting": True})


#: The whole repertoire. Every name is something a body does to the world;
#: none is something a culture does. Carrying is moving with something in
#: hand; placing is releasing; pushing and pulling are applying force.
PRIMITIVES = {
    "move": move, "approach": approach, "avoid": avoid, "carry": move,
    "look": look, "listen": listen, "touch": touch,
    "grasp": grasp, "release": release, "place": release,
    "transfer_object": transfer_object,
    "push": apply_force, "pull": apply_force, "apply_force": apply_force,
    "throw": throw, "strike": strike, "rub": rub,
    "separate": separate, "combine": combine, "consume": consume,
    "emit_signal": emit_signal, "rest": rest,
}
