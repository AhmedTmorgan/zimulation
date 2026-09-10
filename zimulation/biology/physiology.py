"""
The body.

An agent here is not a point that maximises a utility. It is a mass of
tissue at a temperature, with water in it, energy stored in it, damage
accumulated in it and sleep owed by it. Everything it can do costs
something, and the accounting is what kills it.

## Death is an outcome, not a constant

There is no maximum age. An organism dies when its energy store runs out,
or its core temperature leaves the range tissue tolerates, or it loses too
much water, or accumulated damage passes what a body can carry. Old
organisms die more readily than young ones for one reason: repair capacity
declines with age, so the same insult accumulates instead of clearing.

Zimulation 1 carried a `base_lifespan = 44` for a long time, and when it
was finally removed the model got better in ways that were not anticipated
-- cancer stopped being a scheduled event and became something that
appears only where people live long enough to get it. The lesson is
general enough to state as a rule: any constant that names an outcome is
probably doing the work the model was supposed to do.

## Why thermoregulation is the interesting part

Cold does not kill directly at first. It makes the body spend energy to
stay warm -- shivering can quadruple metabolic rate -- and that spending
competes with everything else the organism needs energy for. A cold winter
therefore shows up as a food problem long before it shows up as a
temperature problem.

That is the whole reason external heat could matter to an organism, and
nothing in this module says so. It says only that heat lost to the
surroundings must be replaced from somewhere.

## The gut

What is swallowed goes to a stomach and is absorbed over hours; water on
its own empties in minutes. The stomach's stretch is felt (fullness), and
an empty stomach is felt as hunger even while the reserves are full, as in
people. This was missing at first and was found by connecting the body to
a mind: hunger was read only from stored fat, so a whole meal moved it by
about a hundredth -- below the senses' own noise -- and eating could never
have been learned from what the body reports.
"""

from __future__ import annotations

from ..core.parameters import REGISTRY as R
from ..core.scheduler import DAY, HOUR, YEAR


class Body:
    """
    Physical state of one organism.

    Every field is a physical quantity in SI units, and every one of them
    can kill. `alive` is derived, not set: see `check_viability`.
    """

    __slots__ = ("mass_kg", "fat_kg", "water_kg", "core_temperature_k",
                 "damage", "sleep_debt_s", "age_s", "alive", "cause",
                 "insulation_clo", "activity", "last_update_s",
                 "gut_food_kg", "gut_energy_j", "gut_food_water_kg",
                 "gut_fluid_kg")

    def __init__(self, mass_kg=None, age_s=0.0):
        self.mass_kg = (R.get("reference_body_mass_kg") if mass_kg is None
                        else mass_kg)
        self.fat_kg = self.mass_kg * R.get("fat_fraction_healthy")
        self.water_kg = self.mass_kg * R.get("water_fraction_of_mass")
        self.core_temperature_k = R.get("core_temperature_k")
        self.damage = 0.0
        self.sleep_debt_s = 0.0
        self.age_s = age_s
        self.alive = True
        self.cause = None
        #: insulation from whatever happens to be on or around the body.
        #: Bare skin is the floor. Nothing here knows about clothing; an
        #: object draped over a body raises this number, and whether any
        #: organism ever arranges that is the open question.
        self.insulation_clo = R.get("bare_skin_insulation_clo")
        self.activity = 1.0
        self.last_update_s = 0.0
        #: the stomach: what has been swallowed and not yet absorbed --
        #: food with its energy and bound water, and free water apart
        self.gut_food_kg = 0.0
        self.gut_energy_j = 0.0
        self.gut_food_water_kg = 0.0
        self.gut_fluid_kg = 0.0

    # ------------------------------------------------------------ derived
    @property
    def age_years(self):
        return self.age_s / YEAR

    @property
    def fat_fraction(self):
        return self.fat_kg / max(R.get("division_epsilon"), self.mass_kg)

    @property
    def energy_store_j(self):
        return self.fat_kg * R.get("energy_store_capacity_j_per_kg")

    @property
    def water_fraction_lost(self):
        full = self.mass_kg * R.get("water_fraction_of_mass")
        return max(0.0, (full - self.water_kg) / max(
            R.get("division_epsilon"), full))

    @property
    def stomach_capacity_kg(self):
        """Comfortable stomach capacity, in proportion to body mass."""
        return (R.get("stomach_capacity_kg") * self.mass_kg
                / R.get("reference_body_mass_kg"))

    @property
    def gut_kg(self):
        return self.gut_food_kg + self.gut_fluid_kg

    @property
    def gut_water_kg(self):
        return self.gut_food_water_kg + self.gut_fluid_kg

    @property
    def fullness(self):
        """Stomach distension: what it holds over what it comfortably
        takes."""
        return min(1.0, self.gut_kg / max(R.get("division_epsilon"),
                                          self.stomach_capacity_kg))

    @property
    def pain(self):
        """
        What damage feels like. This is the signal available to the
        organism; `damage` itself is not something a body can read off.
        """
        return min(1.0, self.damage * R.get("pain_per_damage"))

    @property
    def impairment(self):
        """
        How degraded this body's performance is right now.

        Sleep debt, pain and dehydration all reduce what an organism can
        do. Bounded rationality has a physical component, and this is it:
        an exhausted body in pain makes worse decisions because it is
        working with less, not because a trait says it is foolish.
        """
        s = min(1.0, self.sleep_debt_s / max(
            R.get("division_epsilon"),
            R.get("sleep_debt_impairment_h") * HOUR))
        d = min(1.0, self.water_fraction_lost
                / R.get("dehydration_lethal_fraction"))
        base = min(1.0,
                   R.get("impairment_weight_sleep") * s
                   + R.get("impairment_weight_pain") * self.pain
                   + R.get("impairment_weight_thirst") * d)
        # A cooling core takes the mind with it: confusion as shivering
        # begins to fail, stupor by the time it stops (Danzl & Pozos 1994).
        return max(base, 1.0 - shivering_capacity(self))


# ------------------------------------------------------------- metabolism
def shivering_capacity(body):
    """Fraction of full shivering the body can still mount: all of it above
    the core temperature where it begins to fail, none below where it
    stops."""
    full = R.get("shivering_full_core_k")
    stop = R.get("shivering_stop_core_k")
    span = max(R.get("division_epsilon"), full - stop)
    return max(0.0, min(1.0, (body.core_temperature_k - stop) / span))


def resting_rate_w(body):
    """
    Resting metabolic rate, scaled from the reference mass by Kleiber.
    """
    ref_m = R.get("reference_body_mass_kg")
    ratio = max(R.get("division_epsilon"), body.mass_kg / ref_m)
    return (R.get("basal_metabolic_rate_w")
            * ratio ** R.get("mass_metabolic_exponent"))


def heat_loss_w(body, ambient_k, wind_factor=1.0):
    """
    Rate of heat loss from body to surroundings, in watts.

    Conduction through whatever insulates the body, driven by the
    temperature difference. Negative when the surroundings are hotter than
    the body, which is how heat *gain* and therefore hyperthermia work.
    """
    clo = max(R.get("bare_skin_insulation_clo"), body.insulation_clo)
    resistance = clo * R.get("clo_to_si") / max(
        R.get("division_epsilon"), wind_factor)
    gradient = body.core_temperature_k - ambient_k
    return (R.get("body_surface_area_m2") * gradient
            / max(R.get("division_epsilon"), resistance))


def thermoregulate(body, ambient_k, dt_s, wind_factor=1.0,
                   external_heat_w=0.0):
    """
    Balance heat produced against heat lost over dt seconds.

    Returns the extra metabolic energy spent staying warm, in joules.

    `external_heat_w` is heat arriving from the surroundings -- from
    another body close by, from sunlight, from something burning nearby.
    The parameter has no opinion about its source. An organism that ends
    up near a heat source spends less of its own energy, and if anything
    ever learns to arrange that on purpose, the observer will see it in
    the energy accounting before it sees it in behaviour.
    """
    basal = resting_rate_w(body)
    produced = basal * body.activity + external_heat_w
    lost = heat_loss_w(body, ambient_k, wind_factor)

    deficit = lost - produced
    extra_j = 0.0

    if deficit < 0.0:
        # Producing more than the surroundings will take. The body sheds
        # the surplus by evaporating water, which costs water rather than
        # energy -- the reason heat kills by dehydration as readily as by
        # temperature, and the reason working hard in still warm air is
        # dangerous in a way that resting in it is not.
        surplus = -deficit
        latent = R.get("latent_heat_vaporisation_water")
        ceiling_w = R.get("max_sweat_rate_kg_per_s") * latent
        shed = min(surplus, ceiling_w)
        body.water_kg = max(0.0, body.water_kg - shed * dt_s / latent)
        deficit = -(surplus - shed)

    if deficit > 0.0:
        # Shivering: the body burns more to close the gap, up to a limit --
        # and the limit falls as the core itself cools. Shivering is full
        # down to about 35 C and gone by about 30 C (Mallet 2002; Danzl &
        # Pozos 1994), which is why deep hypothermia runs away. The first
        # version shivered at full strength at any core temperature, so a
        # bare, fed body at -1 C settled at a 29 C core and lived seventeen
        # days until its fat ran out.
        ceiling = (basal * (R.get("shivering_max_multiplier") - 1.0)
                   * shivering_capacity(body))
        shiver = min(deficit, ceiling)
        extra_j = shiver * dt_s
        produced += shiver
        deficit = lost - produced

    # Whatever the body cannot balance changes its core temperature.
    body.core_temperature_k -= (deficit * dt_s
                                / R.get("body_heat_capacity_j_per_k"))
    return extra_j


def spend_energy(body, joules):
    """
    Draw energy from the store. Returns what could not be supplied.

    A body that cannot pay is not immediately dead: it is in deficit, and
    the deficit shows up as lost mass. Starvation is a process.
    """
    have = body.energy_store_j
    if joules <= have:
        body.fat_kg -= joules / R.get("energy_store_capacity_j_per_kg")
        return 0.0
    body.fat_kg = 0.0
    return joules - have


def stomach_room(body):
    """How much more the stomach will take, in kilograms."""
    return max(0.0, body.stomach_capacity_kg - body.gut_kg)


def feed(body, mass_kg, energy_per_kg, water_fraction=0.0):
    """
    Swallow material. It goes to the stomach, not straight into the body;
    digest() moves it on. Returns the energy swallowed.

    Nothing here knows what food is. It takes a mass of some material, the
    energy an organism can extract from it and the water it holds -- all
    properties of the material. Whether a given thing is worth eating is
    discoverable, and getting it wrong is possible. Whatever carries energy
    or bulk empties at the pace of a meal; water alone empties far faster.
    The stomach takes only what fits.
    """
    take = min(max(0.0, mass_kg), stomach_room(body))
    if take <= 0.0:
        return 0.0
    water = take * max(0.0, min(1.0, water_fraction))
    if energy_per_kg > 0.0 or water < take:
        body.gut_food_kg += take
        body.gut_energy_j += take * max(0.0, energy_per_kg)
        body.gut_food_water_kg += water
    else:
        body.gut_fluid_kg += take
    return take * max(0.0, energy_per_kg)


def digest(body, dt_s):
    """
    Empty the stomach for dt seconds: energy passes to the store and water
    to the body, each compartment at its own measured pace. Emptying is
    exponential and exact over any step. Returns the energy absorbed.
    """
    food = 1.0 - 0.5 ** (dt_s / R.get("gastric_half_time_food_s"))
    fluid = 1.0 - 0.5 ** (dt_s / R.get("gastric_half_time_fluid_s"))
    energy = body.gut_energy_j * food
    water = body.gut_food_water_kg * food + body.gut_fluid_kg * fluid
    body.gut_energy_j -= energy
    body.gut_food_water_kg -= body.gut_food_water_kg * food
    body.gut_food_kg -= body.gut_food_kg * food
    body.gut_fluid_kg -= body.gut_fluid_kg * fluid
    body.fat_kg += energy / R.get("energy_store_capacity_j_per_kg")
    body.water_kg += water
    return energy


def lose_water(body, ambient_k, dt_s):
    """Obligatory losses, plus sweating when hot."""
    per_day = R.get("water_loss_baseline_kg_per_day")
    comfort = R.get("thermal_comfort_ambient_k")
    if ambient_k > comfort:
        per_day += ((ambient_k - comfort)
                    * R.get("water_loss_per_k_above_comfort"))
    body.water_kg = max(0.0, body.water_kg - per_day * (dt_s / DAY))


def accumulate_sleep_debt(body, dt_s, sleeping):
    if sleeping:
        body.sleep_debt_s = max(0.0, body.sleep_debt_s - dt_s)
    else:
        need = R.get("sleep_need_hours_per_day") * HOUR
        body.sleep_debt_s += dt_s * (need / DAY)


def injure(body, severity):
    """Add damage. Severity is in whole-body units, so 1.0 is fatal."""
    body.damage = min(R.get("damage_lethal_threshold") * 2.0,
                      body.damage + severity)


def repair_capacity(body, nourished):
    """
    Fraction of damage repaired per second.

    Declines with age past onset, and a starving body barely repairs at
    all. This decline is the only reason old organisms are frailer than
    young ones -- there is no age term anywhere else.
    """
    rate = R.get("repair_rate_young")
    onset = R.get("repair_decline_onset_years")
    age = body.age_years
    if age > onset:
        decline = 1.0 + (age - onset) ** R.get("repair_decline_exponent")
        rate /= decline
    return rate * max(0.0, min(1.0, nourished))


def repair(body, dt_s, nourished):
    body.damage = max(0.0, body.damage
                      - repair_capacity(body, nourished) * dt_s)


def check_viability(body):
    """
    Is this body still working? Sets `cause` when it is not.

    Every branch here is a physical limit being exceeded. None of them is
    an age.
    """
    if not body.alive:
        return False
    if body.fat_fraction < R.get("fat_fraction_lethal"):
        body.alive, body.cause = False, "energy_exhausted"
    elif body.core_temperature_k < R.get("core_temperature_lethal_low_k"):
        body.alive, body.cause = False, "core_temperature_low"
    elif body.core_temperature_k > R.get("core_temperature_lethal_high_k"):
        body.alive, body.cause = False, "core_temperature_high"
    elif body.water_fraction_lost > R.get("dehydration_lethal_fraction"):
        body.alive, body.cause = False, "water_exhausted"
    elif body.damage >= R.get("damage_lethal_threshold"):
        body.alive, body.cause = False, "tissue_damage"
    return body.alive


def step(body, dt_s, ambient_k, activity=1.0, sleeping=False,
         wind_factor=1.0, external_heat_w=0.0, nourished=1.0):
    """
    Advance a body by dt seconds. Returns the energy it could not supply.

    The order matters and is physical: produce and lose heat, pay for it,
    pay for activity, lose water, accrue or discharge sleep debt, repair
    what can be repaired, then see whether the result is still alive.
    """
    if not body.alive:
        return 0.0
    body.activity = activity
    body.age_s += dt_s

    digest(body, dt_s)
    extra = thermoregulate(body, ambient_k, dt_s, wind_factor,
                           external_heat_w)
    basal_j = resting_rate_w(body) * activity * dt_s
    unmet = spend_energy(body, basal_j + extra)

    lose_water(body, ambient_k, dt_s)
    accumulate_sleep_debt(body, dt_s, sleeping)
    repair(body, dt_s, nourished)
    check_viability(body)
    return unmet
