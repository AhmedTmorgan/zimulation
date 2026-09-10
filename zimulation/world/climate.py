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

## Corrections

The first version matched the equator and was wrong almost everywhere
else, which was found only when ecology needed a winter. It put the annual
mean at 45 degrees at 16 C (Earth: about 11) and at 60 degrees at 11 C
(about 1), so a 45-degree map had no day below 5 C and no winter at all.
It put the warmest month on the solstice, with no seasonal lag. Its
insolation used the noon sun alone while claiming to include day length.
And it applied a declared day-night range as an amplitude, doubling it.
Temperature now comes from a Budyko energy balance on the exact daily
sunlight, with a heat capacity that damps and delays the seasons.

A single layer ties amplitude to lag, and matching the month's lag gave
hyper-continental seasons: a 39 K range at 45 degrees and a July mean of
32 C, hotter than any real 45-degree climate. Seasonal exchange with ocean
air (K) damps the swing without moving the annual mean. K and Cs are
calibrated to two stated targets at 45 degrees -- a month's lag and a 28 K
range (Bucharest 25, Minneapolis 32) -- and the other latitudes are then a
check, not a fit: about 10 K at 15 degrees (Timbuktu 13), 20 K at 30
(Dallas, El Paso 20-22) and 34 K at 60 (Moscow 28, Yakutsk 60). North of
60 degrees there is no ice or snow albedo, and the annual means run warm.
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
    Daily-mean sunlight at the top of the atmosphere, relative to the
    equator at an equinox, which is 1.

    Day length and beam angle both follow from the declination (the
    standard daily-mean formula; e.g. Berger 1978, Journal of the
    Atmospheric Sciences 35:2362). So a high-latitude winter is dark and
    oblique, and a high-latitude summer, with its long days, receives more
    sunlight in a day than the equator does. The first version used the
    noon beam angle alone while claiming to include day length, and missed
    exactly that summer surplus.
    """
    dec = solar_declination(tick)
    x = -math.tan(latitude_rad) * math.tan(dec)
    h0 = math.acos(max(-1.0, min(1.0, x)))
    return (h0 * math.sin(latitude_rad) * math.sin(dec)
            + math.cos(latitude_rad) * math.cos(dec) * math.sin(h0))


_HARMONICS = {}


def _sunlight_harmonics(latitude_rad):
    """
    Annual mean and first annual harmonic of daily sunlight at a latitude,
    in W m^-2: Q(t) ~ mean + a cos(wt) + b sin(wt). Computed from a
    hundred days spread over the year, and kept per latitude and per value
    of the parameters it depends on.
    """
    tilt = R.get("axial_tilt_degrees")
    s0 = R.get("solar_constant_w_m2")
    key = (latitude_rad, tilt, s0)
    hit = _HARMONICS.get(key)
    if hit is not None:
        return hit
    n = 100
    scale = s0 / math.pi
    mean = a = b = 0.0
    for k in range(n):
        q = insolation(k * YEAR / n, latitude_rad) * scale
        wt = 2.0 * math.pi * k / n
        mean += q
        a += q * math.cos(wt)
        b += q * math.sin(wt)
    hit = (mean / n, 2.0 * a / n, 2.0 * b / n)
    _HARMONICS[key] = hit
    return hit


def annual_mean_k(latitude_rad):
    """
    Annual-mean surface temperature at a latitude, from Budyko's energy
    balance: absorbed sunlight is lost as outgoing longwave, A + B T, and
    as heat carried toward the planetary mean, C (T - Tplanet) (Budyko
    1969, Tellus 21:611; North, Cahalan & Coakley 1981, Reviews of
    Geophysics 19:91). T is in Celsius in that fit.
    """
    mean_q, _, _ = _sunlight_harmonics(latitude_rad)
    co = 1.0 - R.get("planetary_albedo")
    a = R.get("olr_intercept_w_m2")
    b = R.get("olr_slope_w_m2_k")
    c = R.get("heat_transport_w_m2_k")
    planet = (R.get("solar_constant_w_m2") / 4.0 * co - a) / b
    local = (mean_q * co - a + c * planet) / (b + c)
    return local + R.get("celsius_zero_k")


def seasonal_anomaly_k(tick, latitude_rad):
    """
    The seasonal departure from the annual mean. Ground and air have heat
    capacity, so they answer the sun's annual swing damped and late: at
    frequency w the response is divided by (B + C + K + i w Cs), where K
    is the seasonal exchange of heat with ocean air that reaches the land.
    Calibrated so that land at 45 degrees lags the sun by a month and
    swings about 28 K between its coldest and warmest months.
    """
    _, a, b = _sunlight_harmonics(latitude_rad)
    co = 1.0 - R.get("planetary_albedo")
    damp = (R.get("olr_slope_w_m2_k") + R.get("heat_transport_w_m2_k")
            + R.get("seasonal_exchange_w_m2_k"))
    w = 2.0 * math.pi / YEAR
    inertia = w * R.get("surface_heat_capacity_j_m2_k")
    gain = co / math.hypot(damp, inertia)
    wt = w * (tick % YEAR) - math.atan2(inertia, damp)
    return gain * (a * math.cos(wt) + b * math.sin(wt))


def temperature_at(tick, cell, latitude_rad, stream=None):
    """
    Air temperature near the ground of a cell, in kelvin.

    Energy balance gives the annual mean for the latitude and the lagged
    seasonal swing; elevation cools by lapse rate; a daily cycle is layered
    on top, its warmest hour a little after solar noon, and standing water
    damps it because water stores heat. A night can kill where the day was
    survivable, and that difference is exactly the sort of thing an
    organism might come to act on.

    Time of day: tick % DAY == 0 is sunrise, a quarter-day before solar
    noon. Tick 0 is the vernal equinox.
    """
    t = annual_mean_k(latitude_rad) + seasonal_anomaly_k(tick, latitude_rad)
    t -= cell.elevation_m * R.get("lapse_rate_k_per_m")
    damping = 1.0 - R.get("water_thermal_damping") * cell.water_fraction
    phase = 2.0 * math.pi * (((tick - R.get("diurnal_lag_s")) % DAY) / DAY)
    t += 0.5 * R.get("diurnal_swing_k") * math.sin(phase) * damping
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
