"""
Development: growing up and wearing out.

An organism is born small, grows toward the adult size its genome
predisposes it to, reaches peak capacity, and then declines. None of that
is scheduled. Growth happens only when there is energy to build tissue
with, so a starved child stays small; decline happens because capacities
fall with age past an onset, not because a clock runs out.

The distinction that matters is the same one physiology makes about death.
There is no "age of adulthood" at which an organism is switched on, and no
age at which it is switched off. There are curves, and the curves are
gated by what the body actually has to work with.

This is also where a genome first acts on the world. `adult_mass_kg` is a
target, not a size: the phenotype sets how large the body *could* grow,
and nourishment decides how much of that it does.
"""

from __future__ import annotations

import math

from ..core.parameters import REGISTRY as R
from ..core.scheduler import YEAR


def _maturity_fraction(age_years):
    """
    How far along the growth curve an organism of this age is, 0..1.

    A logistic in age, rescaled so that birth is exactly zero and the
    asymptote exactly one. The rescaling matters: an unrescaled logistic
    starts above zero, which would mean a newborn already carries a slice
    of adult mass it never had to build.
    """
    k = R.get("growth_steepness_per_year")
    mid = R.get("maturity_age_years") * 0.5

    def logistic(a):
        return 1.0 / (1.0 + math.exp(-k * (a - mid)))

    at_birth = logistic(0.0)
    return max(0.0, (logistic(age_years) - at_birth) / (1.0 - at_birth))


def target_mass_kg(genome, age_years):
    """
    The mass this organism would have at this age if it never went short.

    The genome sets the ceiling; age sets how much of it is due yet.
    """
    birth = R.get("birth_mass_kg")
    adult = genome["adult_mass_kg"]
    return birth + (adult - birth) * _maturity_fraction(age_years)


def grow(body, genome, dt_s, nourished):
    """
    Move the body toward its target mass. Returns the energy spent.

    Building tissue costs energy, drawn from the same store that keeps the
    body warm and moving. So in a hard winter a child faces a real choice
    that nobody makes for it: growth competes with staying alive, and a
    body short of energy simply does not grow. Stunting is an outcome of
    scarcity, not a trait.
    """
    from .physiology import spend_energy

    target = target_mass_kg(genome, body.age_years)
    if body.mass_kg >= target:
        return 0.0
    gap = target - body.mass_kg
    rate = R.get("max_growth_kg_per_year") / YEAR
    want = min(gap, rate * dt_s) * max(0.0, min(1.0, nourished))
    if want <= 0.0:
        return 0.0
    cost = want * R.get("tissue_energy_cost_j_per_kg")
    unmet = spend_energy(body, cost)
    built = want * (1.0 - unmet / cost) if cost > 0.0 else 0.0
    body.mass_kg += built
    return cost - unmet


def strength(genome, body):
    """
    Physical capacity relative to a peak adult of reference mass, 0..1+.

    Rises with maturity, holds near a peak in early adulthood, then falls
    by a fraction a year. Scaled by mass, because a larger body can apply
    more force. This number caps what an organism can do to the world --
    how hard it can strike, how far it can carry, how long it can rub --
    and it is where the body's age first limits what an agent can attempt.
    """
    age = body.age_years
    peak = R.get("strength_peak_age_years")
    grown = _maturity_fraction(age)
    if age <= peak:
        base = grown
    else:
        base = max(R.get("strength_floor_fraction"),
                   1.0 - R.get("strength_decline_per_year") * (age - peak))
    mass_ratio = body.mass_kg / R.get("reference_body_mass_kg")
    return base * mass_ratio


def sensory_acuity(age_years):
    """
    How well the senses resolve, 1.0 at best.

    Steady until an onset in middle age, then declining a little each
    year. The consequence is epistemic: an older organism perceives less
    accurately, so its beliefs rest on noisier evidence -- a physical
    source of error that has nothing to do with judgement.
    """
    onset = R.get("visual_acuity_decline_onset_years")
    if age_years <= onset:
        return 1.0
    lost = R.get("sensory_decline_per_year") * (age_years - onset)
    return max(R.get("sensory_floor_fraction"), 1.0 - lost)
