"""Culture Zero v1: the first reproducible Zimulation 2 baseline.

This is an experiment runner, not causal code.  It supplies scenario
conditions and records what the existing world and agents do.  It does not
reward civilisation, language, controlled combustion, social hierarchy or
any other human outcome.

The initial protocol deliberately uses a warm latitude so that immediate
cold death does not dominate tests of basic perception and learning.  A
separate cold-bottleneck protocol should later ask whether organisms can
solve the thermal problem by controlled heat, movement, insulation or some
other route.
"""

from __future__ import annotations

import argparse
import contextlib
import json
from collections import Counter
from pathlib import Path

import zimulation.behavior.params  # noqa: F401
import zimulation.biology.params  # noqa: F401
import zimulation.cognition.params  # noqa: F401
import zimulation.world.params  # noqa: F401
from zimulation.core.engine import Engine
from zimulation.core.parameters import REGISTRY as R
from zimulation.core.scheduler import DAY

PROTOCOL = "culture-zero-v1"


@contextlib.contextmanager
def settings(**values):
    previous = {name: R.get(name) for name in values}
    for name, value in values.items():
        R.set(name, value)
    try:
        yield
    finally:
        for name, value in previous.items():
            R.set(name, value)


def shoreline_cells(engine):
    """Deterministic candidate starts with standing water and nearby land."""
    terrain = engine.terrain
    cells = [c for c in terrain.all_cells() if c.water_fraction > 0.0]
    cells.sort(key=lambda c: (
        -sum(n.water_fraction == 0.0
             for n in terrain.neighbours(c.x, c.y)), c.x, c.y))
    if not cells:
        raise RuntimeError("scenario generated no standing-water cell")
    return cells


def run_seed(seed, days, size=16, founders=1, latitude=20.0,
             age_years=25.0, learning=True, consummatory_bias=0.0):
    """Run one preregisterable baseline replicate and return plain data."""
    with settings(map_centre_latitude_degrees=latitude,
                  consummatory_bias=consummatory_bias):
        engine = Engine(seed, size)
        starts = shoreline_cells(engine)
        agents = []
        for i in range(founders):
            agents.append(engine.add(starts[i % len(starts)], age_years,
                                     learning=learning))
        parameter_hash = R.hash()
        engine.run(days * DAY)

        deaths = Counter(
            ev.physical.get("cause", "unknown")
            for ev in engine.ledger.events if ev.kind == "death")
        remedies = Counter()
        for a in agents:
            for drive in a.goals.remedies:
                pass
            for drive in ("hunger", "thirst", "cold", "heat", "pain",
                          "sleepiness"):
                remedies[drive] += len(a.goals.remedies(drive))

        living = sum(a.actor.body.alive for a in agents)
        return {
            "protocol": PROTOCOL,
            "seed": seed,
            "scenario": {
                "days": days,
                "size": size,
                "founders": founders,
                "latitude_degrees": latitude,
                "founder_age_years": age_years,
                "learning": learning,
                "consummatory_bias": consummatory_bias,
            },
            "parameter_hash": parameter_hash,
            "ledger_head": engine.ledger.head,
            "termination": "extinction" if living == 0 else "duration",
            "population": {
                "initial": founders,
                "living": living,
                "dead": founders - living,
                "death_causes": dict(sorted(deaths.items())),
            },
            "cognition": {
                "acts": sum(a.acts for a in agents),
                "concepts": sum(len(a.concepts.items) for a in agents),
                "skills": sum(len(a.skills.items) for a in agents),
                "remedies": dict(sorted(remedies.items())),
            },
        }


def run_batch(first_seed, seeds, **kwargs):
    return [run_seed(first_seed + i, **kwargs) for i in range(seeds)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--first-seed", type=int, default=0)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--days", type=float, default=5.0)
    ap.add_argument("--size", type=int, default=16)
    ap.add_argument("--founders", type=int, default=1)
    ap.add_argument("--latitude", type=float, default=20.0)
    ap.add_argument("--age-years", type=float, default=25.0)
    ap.add_argument("--consummatory-bias", type=float, default=0.0)
    ap.add_argument("--no-learning", action="store_true")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    rows = run_batch(
        args.first_seed, args.seeds, days=args.days, size=args.size,
        founders=args.founders, latitude=args.latitude,
        age_years=args.age_years, learning=not args.no_learning,
        consummatory_bias=args.consummatory_bias)
    text = json.dumps(rows, indent=2, sort_keys=True)
    if args.out is None:
        print(text)
    else:
        args.out.write_text(text + "\n", encoding="utf-8")
        print(args.out)


if __name__ == "__main__":
    main()
