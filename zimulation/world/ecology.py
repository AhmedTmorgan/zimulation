"""
Ecology: what grows, what falls, what lies about, and where water stands.

A world an organism can live in needs food, water, and the raw stuff of
anything it might ever do -- stone, wood, fibre, dry grass. None of it is
placed for anyone. Each kind of matter appears where physical conditions
allow and in proportion to them, and none of it knows who might want it.

## Plants

Edible storage organs (tubers) grow where there is soil, in proportion to
its depth, and only while the ground is warmer than the base temperature
of temperate plant growth (5 C; McMaster & Wilhelm 1997) and moist. A
patch that has been dug regrows toward what its soil can carry, over weeks
of growing weather. Winter stops it and drought stops it: seasonal
scarcity, without anyone writing a season into the food.

## Things lying about

Fallen wood, dry grass and strips of bark accumulate where plants grow.
Lying out, they are wetted toward what they can hold while rain falls and
dried by the air toward the equilibrium moisture of dead fuel between
rains (about 12%; Simard 1968), each at a pace set by its thickness -- the
timelag of fire science, which grows with the square of diameter (Fosberg
1970; the one-hour and ten-hour fuels of Deeming, Burgan & Cohen 1977). A
porous thing is mostly air between thin solid parts, so it is taken to
exchange water like something as thin as its solid fraction of its
diameter -- a modelling choice that lets a bundle of grass behave like its
blades. After rain the grass is dry again within hours and a stick only
after a day or more, and whether anything will burn follows the weather
without a rule saying so. Only combustible matter's moisture is tracked,
because nothing else yet reads it.

The first version tied fuel to the ground's moisture, which in this
climate stays saturated much of the year, so dry grass could burn on only a
handful of days: fire would have been all but ruled out by a modelling
shortcut.

Stones lie where rock is exposed, and flint only in some rocky places,
fixed when the world is made, as geology is. Standing water is where the
terrain holds it.

## An abstraction to keep in view

A cell is 250 metres across, and the things in it stand for what is within
reach of one spot: search is not modelled. Stone and standing water are
kept topped up because at this scale they are, in effect, inexhaustible;
plants and fallen wood are not.

## Time resolution

Stepped a day at a time, an update applies the day's rain first and the
drying after, so fuel is seen as it stands at the day's end -- dry, even on
a wet day, as fine fuel usually is by evening. Anything that acts during
the day must step by the hour and pass rain only for the hours it falls;
measured that way, dry grass could carry a flame in about nine hours of
ten. A first test counted burnable days at daily steps and was true by
construction; it was replaced by the hourly one.
"""

from __future__ import annotations

import math

from ..core.parameters import REGISTRY as R
from ..core.scheduler import DAY, HOUR
from .materials_data import MATERIALS
from .objects import Thing

_TUBER = MATERIALS["tuber"]
_WATER = MATERIALS["water"]
_GRANITE = MATERIALS["granite"]
_FLINT = MATERIALS["flint"]
_WOODS = (MATERIALS["hardwood"], MATERIALS["softwood"])
_GRASS = MATERIALS["dry_grass"]
_BARK = MATERIALS["bark_fibre"]


# ------------------------------------------------------------- conditions
def _land(cell):
    return cell.water_fraction <= 0.0


def soil_fraction(cell):
    return max(0.0, min(1.0, cell.soil_depth_m / R.get("soil_depth_max_m")))


def tuber_capacity_kg(cell):
    """Edible storage organs a cell's soil can carry, within reach of one
    spot."""
    if not _land(cell):
        return 0.0
    return R.get("tuber_capacity_kg") * soil_fraction(cell)


def growing(cell):
    """How strongly plants grow here today: not at all below the base
    temperature, and in proportion to ground moisture above it."""
    if cell.temperature_k <= R.get("plant_growth_base_temperature_k"):
        return 0.0
    return max(0.0, min(1.0, cell.moisture))


def moisture_timelag_s(thing):
    """How long a thing takes to come about two-thirds of the way to the
    ground's moisture: the square of its effective thickness."""
    if thing.length_m <= 0.0 or thing.mass_kg <= 0.0:
        return 0.0
    d = 2.0 * math.sqrt(thing.volume_m3 / (math.pi * thing.length_m))
    d *= 1.0 - thing.material.porosity
    ratio = d / R.get("fuel_timelag_reference_diameter_m")
    return R.get("fuel_timelag_reference_s") * ratio * ratio


def weather_fuel(thing, dt_s, raining):
    """
    Wet a thing lying out toward what it can hold while rain falls, then
    dry it toward the air's equilibrium moisture for the rest of the step,
    each at its own timelag (exact exponential approach).
    """
    lag = max(R.get("division_epsilon"), moisture_timelag_s(thing))
    hold = thing.material.moisture_capacity
    dry = min(hold, R.get("dead_fuel_equilibrium_moisture"))
    wet_s = min(dt_s, R.get("rain_hours_per_wet_day") * HOUR) if raining         else 0.0
    if wet_s > 0.0:
        thing.moisture += (hold - thing.moisture) * (1.0 - math.exp(
            -wet_s / lag))
    rest = dt_s - wet_s
    if rest > 0.0:
        thing.moisture += (dry - thing.moisture) * (1.0 - math.exp(
            -rest / lag))


# ---------------------------------------------------------------- ecology
class Ecology:
    """The growing and lying-about parts of one terrain."""

    __slots__ = ("terrain", "stream", "flint", "pending")

    def __init__(self, terrain, stream):
        self.terrain = terrain
        self.stream = stream
        rocky = [c for c in terrain.all_cells() if _land(c)
                 and c.rock_exposure > R.get("rock_exposure_threshold")]
        self.flint = {(c.x, c.y) for c in rocky
                      if stream.random() < R.get("flint_cell_fraction")}
        self.pending = {}
        for c in terrain.all_cells():
            c.vegetation_kg_m2 = (R.get("vegetation_max_kg_m2")
                                  * soil_fraction(c) if _land(c) else 0.0)
            if _land(c):
                self._grow(c, 0.0, fill=True)
                self._litter(c, 0.0, fill=True)
                self._expose(c, 0.0, fill=True)
            else:
                self._refill(c)

    # -------------------------------------------------------------- items
    def _lay(self, cell, material, mass, length):
        th = Thing(None, material, mass, length, cell.temperature_k,
                   min(material.moisture_capacity,
                       R.get("dead_fuel_equilibrium_moisture")),
                   (cell.x, cell.y))
        cell.things.append(th)
        return th

    def _of(self, cell, materials):
        return [t for t in cell.things
                if t.material in materials and t.burning is None]

    def _accrue(self, key, amount):
        total = self.pending.get(key, 0.0) + amount
        self.pending[key] = total
        return total

    # ------------------------------------------------------------ growing
    def _grow(self, cell, days, fill=False):
        cap = tuber_capacity_kg(cell)
        if cap <= 0.0:
            return
        stock = sum(t.mass_kg for t in self._of(cell, (_TUBER,)))
        item = R.get("tuber_item_kg")
        key = ("tuber", cell.x, cell.y)
        if fill:
            goal = cap * (0.5 + 0.5 * self.stream.random())
            pend = self._accrue(key, max(0.0, goal - stock))
        else:
            pend = self._accrue(key, R.get("tuber_regrowth_per_day")
                                * growing(cell) * max(0.0, cap - stock)
                                * days)
        while pend >= item and stock + item <= cap:
            m = item * (0.5 + self.stream.random())
            self._lay(cell, _TUBER, m, (m / _TUBER.density) ** (1.0 / 3.0))
            pend -= m
            stock += m
        self.pending[key] = pend

    def _litter(self, cell, days, fill=False):
        share = soil_fraction(cell)
        for name, materials in (("stick", _WOODS), ("grass", (_GRASS,)),
                                ("bark", (_BARK,))):
            cap = int(round(R.get(f"{name}_cap") * share))
            have = len(self._of(cell, materials))
            if have >= cap:
                continue
            key = (name, cell.x, cell.y)
            add = (cap - have if fill else
                   self._accrue(key, R.get("litter_regrowth_per_day")
                                * (cap - have) * days))
            n = int(add)
            if not fill:
                self.pending[key] = add - n
            for _ in range(min(n, cap - have)):
                material = materials[int(self.stream.random()
                                         * len(materials))]
                self._lay(cell, material, R.get(f"{name}_item_kg"),
                          R.get(f"{name}_length_m"))

    def _expose(self, cell, days, fill=False):
        kinds = []
        if cell.rock_exposure > R.get("rock_exposure_threshold"):
            kinds.append(("cobble", _GRANITE))
            if (cell.x, cell.y) in self.flint:
                kinds.append(("nodule", _FLINT))
        for name, material in kinds:
            cap = int(R.get(f"{name}_cap"))
            have = len(self._of(cell, (material,)))
            if have >= cap:
                continue
            key = (name, cell.x, cell.y)
            add = (cap - have if fill else
                   self._accrue(key, R.get("stone_exposure_per_day") * days))
            n = int(add)
            if not fill:
                self.pending[key] = add - n
            for _ in range(min(n, cap - have)):
                self._lay(cell, material, R.get(f"{name}_kg"),
                          R.get(f"{name}_length_m"))

    def _refill(self, cell):
        pools = self._of(cell, (_WATER,))
        if not pools:
            pool = self._lay(cell, _WATER, R.get("water_pool_kg"),
                             R.get("cell_size"))
            pool.moisture = 1.0
            return
        for pool in pools:
            pool.mass_kg = R.get("water_pool_kg")
            pool.moisture = 1.0

    # ------------------------------------------------------------- update
    def update(self, dt_s, rain=None):
        """
        Advance growth, litterfall, exposure of stone, water, and the
        moisture of combustible things by dt. Reads each cell's temperature
        and ground moisture as the weather left them; `rain` is the step's
        rain per cell, as climate.step_day returns it.
        """
        days = dt_s / DAY
        rain = rain or {}
        for c in self.terrain.all_cells():
            c.things = [t for t in c.things if t.mass_kg > 0.0]
            raining = rain.get((c.x, c.y), 0.0) > 0.0
            for t in c.things:
                if (t.burning is None and t.material.ignition_point is not None
                        and t.material is not _WATER):
                    weather_fuel(t, dt_s, raining)
            if _land(c):
                self._grow(c, days)
                self._litter(c, days)
                self._expose(c, days)
            else:
                self._refill(c)
