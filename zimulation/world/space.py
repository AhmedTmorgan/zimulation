"""
Space, and the limits it puts on knowing.

Every cell holds physical quantities only: how high it is, how deep the
soil, how much standing water, how much living plant matter, how much bare
rock is exposed. There are no biome names. "Marsh" and "upland" are things
an observer may say afterwards about a cell with standing water and low
elevation; the world itself knows only the numbers.

The reason to be strict about that is not tidiness. A grid labelled with
biomes has already sorted the world into human categories, and an agent
living on it inherits that sorting for free. A grid of elevations and
water fractions makes an agent do its own sorting, or fail to.

## Locality is the point

Section 49 of the contract forbids any agent from querying global state.
This module is where that is made true rather than promised: an agent gets
`visible_from` and `audible_from`, both of which fall off with distance,
terrain and elevation. There is no function here that returns the world.

Knowledge of a distant place must therefore physically travel -- carried
by someone who walked there and back, or told by someone who did. That
constraint is what makes cultural transmission worth studying at all. If
everyone could see everything, there would be nothing for testimony to do
and no way for history to be wrong.
"""

from __future__ import annotations

import math

from ..core.parameters import REGISTRY as R


class Cell:
    """
    One patch of ground. Physical quantities, no categories.

    `vegetation_kg_m2` is standing plant biomass, which is simultaneously
    food for something, fuel for combustion, and cover. Nothing marks
    which of those it is: that depends entirely on what encounters it.
    """

    __slots__ = ("x", "y", "elevation_m", "soil_depth_m", "water_fraction",
                 "vegetation_kg_m2", "rock_exposure", "moisture",
                 "temperature_k", "things")

    def __init__(self, x, y, elevation_m, soil_depth_m, water_fraction,
                 vegetation_kg_m2, rock_exposure):
        self.x = x
        self.y = y
        self.elevation_m = elevation_m
        self.soil_depth_m = soil_depth_m
        self.water_fraction = water_fraction
        self.vegetation_kg_m2 = vegetation_kg_m2
        self.rock_exposure = rock_exposure
        #: ground moisture, distinct from standing water: what plants draw
        #: on. Fuel lying here is wetted by rain and dried by the air on its
        #: own timelag (world.ecology); tying it to this, which stays
        #: saturated much of the year, left dry grass unburnable most days
        self.moisture = water_fraction
        self.temperature_k = R.get("ambient_temperature")
        self.things = []

    def __repr__(self):
        return (f"<Cell {self.x},{self.y} elev={self.elevation_m:.0f}m "
                f"veg={self.vegetation_kg_m2:.2f}kg/m2>")


class Terrain:
    """
    A square grid of cells, generated deterministically from a stream.

    The generator is deliberately simple: smoothed noise for elevation,
    water pooling in low ground, soil accumulating where it is flat and
    low. Vegetation is not made here: world.ecology grows it (the
    first version of this docstring said it followed soil and moisture,
    and every cell was given none). It is not a geological
    model and does not pretend to be. What it has to deliver is a world
    with places that differ from one another, so that moving is worth
    something and so that local knowledge is genuinely partial.
    """

    __slots__ = ("size", "cells", "cell_size_m")

    def __init__(self, size, stream):
        self.size = size
        self.cell_size_m = R.get("cell_size")
        self.cells = []
        raw = self._noise(size, stream)
        sea = R.get("sea_level_fraction")
        heights = sorted(v for row in raw for v in row)
        water_line = heights[int(len(heights) * sea)]
        relief = R.get("elevation_relief_m")

        for y in range(size):
            row = []
            for x in range(size):
                h = (raw[y][x] - water_line) * relief
                if h < 0.0:
                    water = min(1.0, -h / R.get("water_depth_scale_m"))
                    h = 0.0
                else:
                    water = 0.0
                slope = self._slope(raw, x, y, size) * relief
                soil = max(0.0, R.get("soil_depth_max_m")
                           * (1.0 - slope / R.get("slope_soil_loss_m"))
                           * (1.0 - water))
                rock = min(1.0, slope / R.get("slope_rock_exposure_m"))
                row.append(Cell(x, y, h, soil, water, 0.0, rock))
            self.cells.append(row)

    def _noise(self, size, stream):
        """Smoothed value noise. Deterministic given the stream."""
        raw = [[stream.random() for _ in range(size)] for _ in range(size)]
        for _ in range(int(R.get("terrain_smoothing_passes"))):
            nxt = []
            for y in range(size):
                row = []
                for x in range(size):
                    tot = n = 0.0
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            i, j = x + dx, y + dy
                            if 0 <= i < size and 0 <= j < size:
                                tot += raw[j][i]
                                n += 1.0
                    row.append(tot / n)
                nxt.append(row)
            raw = nxt
        return raw

    def _slope(self, raw, x, y, size):
        here = raw[y][x]
        worst = 0.0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                i, j = x + dx, y + dy
                if 0 <= i < size and 0 <= j < size:
                    worst = max(worst, abs(raw[j][i] - here))
        return worst

    def at(self, x, y):
        if 0 <= x < self.size and 0 <= y < self.size:
            return self.cells[y][x]
        return None

    def neighbours(self, x, y, radius=1):
        out = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                c = self.at(x + dx, y + dy)
                if c is not None:
                    out.append(c)
        return out

    def distance_m(self, a, b):
        """
        Ground distance including the climb.

        Elevation counts because walking uphill costs more, which is what
        makes some routes preferred and some places effectively far away
        despite being close.
        """
        flat = math.hypot(a.x - b.x, a.y - b.y) * self.cell_size_m
        rise = abs(a.elevation_m - b.elevation_m)
        return math.hypot(flat, rise)

    def all_cells(self):
        """
        Every cell. For world generation and for the observer only.

        Nothing on an agent's path may call this. The contract test cannot
        see intent, so this is a place where review has to do the work:
        if this appears inside cognition or behaviour, it is a bug.
        """
        return [c for row in self.cells for c in row]


def visible_from(terrain, viewer_cell, target_cell, clarity=1.0):
    """
    Whether one cell can be seen from another.

    Distance limits it, and so does what lies between: a ridge blocks
    sight of what is behind it. Height helps, which is why high ground is
    worth something without anything having to say so.
    """
    d = terrain.distance_m(viewer_cell, target_cell)
    reach = R.get("visibility_clear_day") * clarity
    if d > reach:
        return False
    if d <= terrain.cell_size_m:
        return True

    # Sample the ground between the two and see whether anything rises
    # above the sight line.
    steps = max(2, int(d / terrain.cell_size_m))
    eye = viewer_cell.elevation_m + R.get("eye_height_m")
    top = target_cell.elevation_m
    for i in range(1, steps):
        f = i / steps
        x = int(round(viewer_cell.x + (target_cell.x - viewer_cell.x) * f))
        y = int(round(viewer_cell.y + (target_cell.y - viewer_cell.y) * f))
        c = terrain.at(x, y)
        if c is None:
            continue
        line = eye + (top - eye) * f
        if c.elevation_m > line + R.get("sight_line_tolerance_m"):
            return False
    return True


def audible_from(terrain, source_cell, listener_cell, loudness=1.0):
    """
    Whether a sound made in one cell reaches another.

    Far shorter than sight, and it does not care about ridges. This
    asymmetry matters: a signal can be heard by someone who cannot be
    seen, which is the physical basis on which communication at a
    distance could ever be worth more than gesture.
    """
    d = terrain.distance_m(source_cell, listener_cell)
    return d <= R.get("sound_audible_distance") * loudness


def travel_cost_s(terrain, a, b, speed_m_s):
    """
    Seconds to walk between two cells at a given speed.

    Climbing is charged extra. Nothing here decides whether the journey is
    worth making; that is for whoever is doing the walking.
    """
    flat = math.hypot(a.x - b.x, a.y - b.y) * terrain.cell_size_m
    climb = max(0.0, b.elevation_m - a.elevation_m)
    effective = flat + climb * R.get("climb_cost_multiplier")
    return effective / max(R.get("division_epsilon"), speed_m_s)
