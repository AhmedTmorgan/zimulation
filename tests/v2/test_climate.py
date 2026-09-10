"""
Climate, held to the Earth it stands for.

The first climate matched the equator and was wrong almost everywhere
else: 45 degrees averaged 16 C instead of about 11, 60 degrees 11 C instead
of about 1, the warmest month fell on the solstice instead of a month after
it, the day-night range was twice what was declared, and daily sunlight
ignored day length. These tests hold the energy-balance replacement to
zonal climatology within the tolerance a model this simple deserves.

    python -m tests.v2.test_climate
"""

from __future__ import annotations

import contextlib
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.world.params  # noqa: F401  (declares on import)
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.scheduler import DAY, HOUR
from zimulation.world import climate as CL
from zimulation.world.space import Cell

DRY = Cell(0, 0, 0.0, 1.0, 0.0, 0.0, 0.0)
SOLSTICE = 91


@contextlib.contextmanager
def _setting(name, value):
    old = R.get(name)
    R.set(name, value)
    try:
        yield
    finally:
        R.set(name, old)


def _daily_means(lat_deg):
    lat = math.radians(lat_deg)
    return [sum(CL.temperature_at(d * DAY + h * HOUR, DRY, lat)
                for h in range(0, 24, 2)) / 12 - 273.15 for d in range(365)]


def _months(days):
    return [sum(days[(d + k) % 365] for k in range(30)) / 30
            for d in range(365)]


def _warmest_month_centre(months):
    return (max(range(365), key=months.__getitem__) + 15) % 365


def test_daily_sunlight_includes_day_length():
    """At the summer solstice the long high-latitude day outweighs the
    oblique sun; at the winter solstice there is no sun at all."""
    assert abs(CL.insolation(0, 0.0) - 1.0) < 1e-12
    assert (CL.insolation(SOLSTICE * DAY, math.radians(75))
            > CL.insolation(SOLSTICE * DAY, 0.0))
    assert CL.insolation(274 * DAY, math.radians(75)) == 0.0


def test_annual_means_follow_latitude_as_on_earth():
    """
    Zonal-mean surface air temperature is about 26 C at the equator, 11 C
    at 45 degrees and 1 C at 60 (e.g. Hartmann 2016, Global Physical
    Climatology). A one-layer energy balance is held to within four
    degrees.
    """
    for lat, earth in ((0, 26.0), (45, 11.0), (60, 1.0)):
        mean = sum(_daily_means(lat)) / 365
        assert abs(mean - earth) < 4.0, f"{lat} deg: {mean:.1f} C"


def test_the_warmest_month_comes_about_a_month_after_the_solstice():
    centre = _warmest_month_centre(_months(_daily_means(45)))
    assert SOLSTICE + 15 <= centre <= SOLSTICE + 50, centre


def test_a_mid_latitude_winter_freezes():
    days = _daily_means(45)
    months = _months(days)
    assert min(months) < 0.0 < 20.0 < max(months), (min(months),
                                                    max(months))
    warm = sum(t > 5.0 for t in days)
    assert 150 < warm < 300, f"{warm} days above 5 C"


def test_tilt_is_the_only_origin_of_seasons():
    """The counterfactual lever: remove the tilt and the seasons go."""
    with _setting("axial_tilt_degrees", 0.0):
        months = _months(_daily_means(45))
    assert max(months) - min(months) < 0.1


def test_heat_capacity_trades_range_for_lateness():
    """An ocean-like surface swings less and later than land -- the knob
    that separates continental from maritime climates."""
    def season(capacity):
        with _setting("surface_heat_capacity_j_m2_k", capacity):
            months = _months(_daily_means(45))
        return max(months) - min(months), _warmest_month_centre(months)
    land = season(R.get("surface_heat_capacity_j_m2_k"))
    sea = season(1.5e8)
    assert sea[0] < land[0] and sea[1] > land[1], (land, sea)


def test_seasonal_ranges_follow_continental_climates_across_latitudes():
    """
    The seasonal exchange and heat capacity were calibrated at 45 degrees
    only (a month's lag, a 28 K range). The other latitudes are a check:
    mid-continental ranges run about 13 K near 15 degrees (Timbuktu), 20
    to 22 at 30 (Dallas, El Paso), 25 to 32 at 45 (Bucharest,
    Minneapolis) and 26 to 60 near 60 (Moscow to Yakutsk).
    """
    for lat, low, high in ((15, 6, 16), (30, 14, 26), (45, 22, 34),
                           (60, 24, 50)):
        months = _months(_daily_means(lat))
        swing = max(months) - min(months)
        assert low < swing < high, f"{lat} deg: {swing:.1f} K"


def test_latitude_follows_the_ground_between_places():
    """A degree of latitude is about 111 km: a map a few kilometres across
    lies at one latitude. The first version spread every map over a
    declared eight degrees whatever its size."""
    from zimulation.core.rng import Streams
    from zimulation.world.space import Terrain
    terr = Terrain(16, Streams(1).get("t"))
    span = math.degrees(CL.latitude_of(terr, terr.at(0, 15))
                        - CL.latitude_of(terr, terr.at(0, 0)))
    expected = 15 * terr.cell_size_m / R.get("meters_per_degree_latitude")
    assert abs(span - expected) < 1e-9 and span < 0.05, span


def test_the_day_night_range_is_what_was_declared():
    lat = math.radians(45)
    diurnal = []
    for m in range(0, 1440, 5):
        tick = 100 * DAY + m * 60
        diurnal.append(CL.temperature_at(tick, DRY, lat)
                       - CL.annual_mean_k(lat)
                       - CL.seasonal_anomaly_k(tick, lat))
    swing = max(diurnal) - min(diurnal)
    assert abs(swing - R.get("diurnal_swing_k")) < 0.01, swing


def test_the_warmest_hour_follows_solar_noon():
    lat = math.radians(45)
    noon = DAY // 4
    best = max(range(0, 1440, 5), key=lambda m: (
        CL.temperature_at(100 * DAY + m * 60, DRY, lat)
        - CL.seasonal_anomaly_k(100 * DAY + m * 60, lat)))
    assert noon + HOUR <= best * 60 <= noon + 4 * HOUR, best / 60


def _run_all():
    ok = fail = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  PASS  {name}")
            ok += 1
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            fail += 1
        except Exception as e:
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
            fail += 1
    print(f"\n{ok} passed, {fail} failed")
    return fail


if __name__ == "__main__":
    sys.exit(1 if _run_all() else 0)
