"""Temporary diagnostic for the open-agent integration; remove after CI diagnosis."""

import zimulation.behavior.params  # noqa: F401
import zimulation.biology.params  # noqa: F401
import zimulation.cognition.params  # noqa: F401
import zimulation.world.params  # noqa: F401
from zimulation.core.engine import Engine
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.scheduler import DAY


def shore(engine):
    cells = [c for c in engine.terrain.all_cells() if c.water_fraction > 0.0]
    return max(cells, key=lambda c: (sum(n.water_fraction == 0.0 for n in
                                         engine.terrain.neighbours(c.x, c.y)),
                                     -c.x, -c.y))


old_lat = R.get("map_centre_latitude_degrees")
old_bias = R.get("consummatory_bias")
try:
    R.set("map_centre_latitude_degrees", 20.0)
    R.set("consummatory_bias", 0.0)
    engine = Engine(0, 16)
    engine.add(shore(engine), 25.0, learning=True)
    engine.run(5 * DAY)
finally:
    R.set("map_centre_latitude_degrees", old_lat)
    R.set("consummatory_bias", old_bias)
