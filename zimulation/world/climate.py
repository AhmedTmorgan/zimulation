"""
Climate: insolation, temperature, and water arriving from the sky.

Zimulation 1 asserted its climate as a pair of sine waves and, worse, made
the star an agent could observe a function of the *same* sine -- so the
correlation those agents could discover was not in their world, it was one
hand writing in two places. The lesson stuck: here temperature comes from
the sun's angle, and the sun's angle comes from where the planet is in its
year and how far north the ground lies.

That is still a simplification. It is not a general circulation model and
does not claim to be. What it does claim is that every quantity here
follows from something above it, so that "why was that winter hard" has an
answer other than "because the function said so".

## Why this matters for the experiment

Section 11 of the contract forbids scripting a cold bottleneck to force
the discovery of controlled combustion. The pressure has to be ecological
and real: winters that genuinely cost energy, in a world where migration,
shelter, body mass and diet are all also available answers. This module
supplies the cold. It has no opinion about how anyone survives it.
"""

from __future__ import annotations

import math

from ..core.parameters import REGISTRY as R
from ..core.scheduler import DAY, YEAR


def solar_declination(tick):
    """
    The sun's angle above the equator, in radians.

    Follows from axial tilt and the fraction of the year elapsed. This is
    the single source of seasonality: everything below reads from it, so
    seasons cannot drift out of step with each other.
    """
    tilt = math.radians(R.get("axial_tilt_degrees"))
    phase = 2.0 * math.pi * ((tick % YEAR) / YEAR)
    return tilt * math.sin(phase)


def insolation(tick, latitude_rad):
    """
    Relative solar energy reaching flat ground, 0..1.

    Day length and beam angle both come from the same declination, so a
    high-latitude winter is dark *and* oblique, which is why it is cold
    rather than merely dim.
    """
    dec = solar_declination(tick)
    noon_altitude = math.pi / 2.0 - abs(latitude_rad - dec)
    if noon_altitude <= 0.0:
        return 0.0
    return math.sin(noon_altitude)


def temperature_at(tick, cell, latitude_rad, stream=None):
    """
    Ground temperature of a cell in kelvin.

    Insolation sets the seasonal swing; elevation cools by lapse rate;
    standing water damps the swing because water stores heat. A daily
    cycle is layered on top, because a night can kill where the day was
    survivable and that difference is exactly the sort of thing an
    organism might come to act on.
    """
    base = R.get("ambient_temperature")
    swing = R.get("seasonal_swing_k")
    s = insolation(tick, latitude_rad)
    seasonal = base + swing * (s - R.get("insolation_neutral"))

    lapse = cell.elevation_m * R.get("lapse_rate_k_per_m")
    # Water moderates: a wet cell is cooler by day and warmer by night.
    damping = 1.0 - R.get("water_thermal_damping") * cell.water_fraction

    day_phase = 2.0 * math.pi * ((tick % DAY) / DAY)
    diurnal = R.get("diurnal_swing_k") * math.sin(day_phase) * damping

    t = seasonal - lapse + diurnal
    if stream is not None:
        t += stream.gauss(0.0, R.get("weather_noise_k"))
    return t


def precipitation(tick, cell, latitude_rad, stream):
    """
    Water arriving on a cell this step, as a depth in metres.

    Warm air holds more water, so precipitation follows temperature, and
    high ground wrings more out of what passes over it. The consequence
    that matters is downstream: rain raises ground moisture, and ground
    moisture is what makes fuel too damp to burn.
    """
    warmth = max(0.0, insolation(tick, latitude_rad))
    orographic = 1.0 + cell.elevation_m * R.get("orographic_gain_per_m")
    mean = R.get("mean_precipitation_m_per_day") * warmth * orographic
    if mean <= 0.0:
        return 0.0
    # Rain is episodic, not a trickle: most days dry, some days wet.
    if stream.random() > R.get("rain_day_fraction"):
        return 0.0
    return stream.expovariate(1.0 / (mean / R.get("rain_day_fraction")))


def update_moisture(cell, rain_m, temperature_k, dt_s):
    """
    Ground moisture after rain and evaporation.

    Warmth dries the ground; rain wets it; standing water keeps its
    surroundings damp. This is the quantity combustion actually reads, so
    it is the hinge between weather and whether anything can burn.
    """
    gain = rain_m / max(R.get("division_epsilon"),
                        R.get("moisture_saturation_depth_m"))
    warmth = max(0.0, temperature_k - R.get("evaporation_threshold_k"))
    loss = (warmth * R.get("evaporation_per_k_per_day")
            * (dt_s / DAY) * (1.0 - cell.water_fraction))
    cell.moisture = max(cell.water_fraction,
                        min(1.0, cell.moisture + gain - loss))
    return cell.moisture


def latitude_of(terrain, cell):
    """
    Latitude of a cell in radians.

    The map spans a band of latitude, so north and south differ. Without
    this every place has the same seasons and there is nowhere to migrate
    *to* when the cold comes, which would quietly decide one of the
    questions the experiment is supposed to be asking.
    """
    span = math.radians(R.get("map_latitude_span_degrees"))
    centre = math.radians(R.get("map_centre_latitude_degrees"))
    f = (cell.y / max(1, terrain.size - 1)) - 0.5
    return centre + span * f
