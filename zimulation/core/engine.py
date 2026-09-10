"""
The engine: time, the world, and the organisms in it.

An event-driven clock (core.scheduler) advances between meaningful events,
never by a fixed global step (contract section 48). The world keeps its own
time: weather is drawn once a day for the whole map, and ecology -- growth,
litter, the wetting and drying of fuel -- is stepped every hour, with rain
falling in the first hours of a wet day. Each organism keeps its own: it
acts, and its next turn comes when the act is done. Between turns its body
is advanced by physiology for the time the act took, in the air of the
place it stands at that hour of that day.

What the engine writes down (core.events) is what an observer needs to
reconstruct what happened: arrivals, deaths and their causes, remedies an
agent has come to trust, procedures it has stored, and plans it acted on
together with the alternatives it weighed (section 26). Single acts are
counted, not ledgered -- tens of thousands a day would drown the record,
and each is recoverable from the seeds.

The engine decides nothing for anyone. It keeps time and applies physics.
"""

from __future__ import annotations

from ..behavior import primitives as PR
from ..behavior.perceptual_agent import Agent
from ..biology import genetics as G
from ..biology import physiology as PHY
from ..core.parameters import REGISTRY as R
from ..world import climate as CL
from ..world.ecology import Ecology
from ..world.space import Terrain
from .events import Ledger
from .rng import Streams
from .scheduler import (DAY, HOUR, PRIORITY_ACTION, PRIORITY_PHYSICS, YEAR,
                        Scheduler)


class Engine:
    """One world, its clock, its organisms, and the record of them."""

    __slots__ = ("seed", "streams", "terrain", "ecology", "weather",
                 "ledger", "clock", "agents", "rain", "today")

    def __init__(self, seed, size, start=0):
        self.seed = seed
        self.streams = Streams(seed)
        self.terrain = Terrain(size, self.streams.get("terrain"))
        self.ecology = Ecology(self.terrain, self.streams.get("ecology"))
        self.weather = self.streams.get("weather")
        self.ledger = Ledger()
        self.clock = Scheduler(start)
        self.agents = []
        self.rain = {}
        self.today = None
        self.clock.every(HOUR, self._hour, priority=PRIORITY_PHYSICS,
                         label="world", first=start)

    # -------------------------------------------------------------- world
    def _hour(self):
        now = self.clock.now
        day = now // DAY
        if day != self.today:
            self.today = day
            self.rain = CL.step_day(self.terrain, day * DAY, self.weather)
        hour = (now % DAY) // HOUR
        wet = (hour < int(R.get("rain_hours_per_wet_day"))
               and any(v > 0.0 for v in self.rain.values()))
        self.ecology.update(HOUR, rain=self.rain if wet else None)

    def air_k(self, cell, time):
        """Air temperature at a place and moment: the climate's daily and
        seasonal course, plus the day's weather over the whole map."""
        lat = CL.latitude_of(self.terrain, cell)
        weather = cell.temperature_k - CL.daily_mean_k(
            (time // DAY) * DAY, cell, lat)
        return CL.temperature_at(time, cell, lat) + weather

    # ---------------------------------------------------------- organisms
    def add(self, cell, age_years, mass_kg=None, learning=True, when=None):
        """Place a newly made adult at a cell and start its turns."""
        n = len(self.agents) + 1
        genome = G.founder(self.streams.entity("genome", n))
        mass = genome["adult_mass_kg"] if mass_kg is None else mass_kg
        body = PHY.Body(mass_kg=mass, age_s=age_years * YEAR)
        agent = Agent(n, PR.Actor(n, body, genome, cell), self.streams,
                      learning=learning)
        self.agents.append(agent)
        at = self.clock.now if when is None else when
        self.ledger.append(at, "arrival", location=(cell.x, cell.y),
                           participants=(n,),
                           physical={"age_years": age_years, "mass_kg": mass,
                                     "learning": learning})
        self.clock.at(at, lambda a=agent: self._turn(a),
                      priority=PRIORITY_ACTION, label=f"agent {n}")
        return agent

    def _turn(self, agent):
        body = agent.actor.body
        if not body.alive:
            return
        now = self.clock.now
        spent, asleep = agent.turn(self.terrain, now)
        dt = max(1, int(round(spent)))
        PHY.step(body, dt, self.air_k(agent.actor.cell, now),
                 sleeping=asleep)
        for item in agent.news:
            self._record(agent, now, item)
        agent.news = []
        if not body.alive:
            self.ledger.append(now + dt, "death",
                               location=agent.actor.here,
                               participants=(agent.id,),
                               physical={"cause": body.cause,
                                         "age_s": body.age_s,
                                         "acts": agent.acts})
            return
        self.clock.at(now + dt, lambda a=agent: self._turn(a),
                      priority=PRIORITY_ACTION, label=f"agent {agent.id}")

    def _record(self, agent, now, item):
        what = item[0]
        where = agent.actor.here
        if what == "remedy":
            _, drive, act, kind, mean = item
            self.ledger.append(now, "remedy", location=where,
                               participants=(agent.id,), primitives=(act,),
                               physical={"drive": drive, "kind": repr(kind),
                                         "mean_change": mean})
        elif what == "skill":
            self.ledger.append(now, "skill", location=where,
                               participants=(agent.id,),
                               physical={"skill": repr(item[1])})
        elif what == "decision":
            d = item[1]
            self.ledger.append(now, "decision", location=where,
                               participants=(agent.id,),
                               physical={
                                   "goal": sorted(repr(t) for t in
                                                  d.goal.wanted),
                                   "chosen": repr(d.chosen),
                                   "chance": d.chance,
                                   "alternatives": sorted(
                                       [repr(k), v] for k, v in
                                       d.alternatives.items()),
                                   "examined": d.examined,
                                   "stopped": d.stopped})

    # ---------------------------------------------------------------- run
    def run(self, until):
        self.clock.run_until(until)

    def living(self):
        return [a for a in self.agents if a.actor.body.alive]
