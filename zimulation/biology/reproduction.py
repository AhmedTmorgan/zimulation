"""
Reproduction -- the physiology of it, and nothing else.

Section 28 of the contract separates two systems that are easy to fuse:
sexual motivation, and reproduction. This module is only the second. It
answers one question: given that an insemination event occurred between
two bodies, what does physiology do next? Whether such an event happens,
between whom, and why, belongs to drives and behaviour, which live
elsewhere and are not built yet. Nothing here models attraction, choice,
preference or pairing, and a test fails if it starts to.

What remains is a body's accounting, and it is where much of demography
comes from without anyone deciding it:

  - A body too thin does not ovulate (Frisch & McArthur 1974). Famine
    therefore lowers births before it raises deaths.
  - A nursing body mostly does not conceive (lactational amenorrhea). In
    forager populations this, not any decision, is what spaces children
    three or four years apart.
  - Gestation and lactation cost energy, drawn from the same store that
    keeps the body warm. A mother in a hard winter is paying for two.
  - Birth itself can injure. Maternal death is not a flag set on the
    mother; it is tissue damage passing the lethal threshold, and it
    comes out near the pre-modern rate from the complication rate and
    severity range rather than being declared as a rate.

Both parents must be reproductively mature, which is a biological fact
about when conception is possible at all.
"""

from __future__ import annotations

from ..core.parameters import REGISTRY as R
from ..core.scheduler import DAY, YEAR
from . import genetics as GEN
from . import physiology as PHY
from .development import _maturity_fraction

FEMALE = "female"
MALE = "male"


class Pregnancy:
    """A gestation in progress: whose genome, and when it is due."""

    __slots__ = ("father_genome", "conceived_s", "due_s")

    def __init__(self, father_genome, conceived_s):
        self.father_genome = father_genome
        self.conceived_s = conceived_s
        self.due_s = conceived_s + R.get("gestation_days") * DAY


def _ramp(x, low, high):
    if high <= low:
        return 1.0 if x >= high else 0.0
    return max(0.0, min(1.0, (x - low) / (high - low)))


def mature(body):
    """Whether a body has reached the stage at which conception can occur."""
    return (body.alive and _maturity_fraction(body.age_years)
            >= R.get("reproductive_maturity_fraction"))


def fecundity(body, sex, nursing_s_remaining=0.0):
    """
    Probability that one insemination of this body leads to conception.

    Gestation is a property of the female body, so this is zero for any
    other. For a female body it is the product of four physical factors:
    maturity, age, body condition and whether she is nursing.
    """
    if sex != FEMALE or not mature(body):
        return 0.0
    age = body.age_years
    onset = R.get("fertility_decline_onset_years")
    end = R.get("fertility_end_years")
    if age >= end:
        return 0.0
    age_factor = 1.0 if age <= onset else 1.0 - (age - onset) / (end - onset)
    body_factor = _ramp(body.fat_fraction,
                        R.get("fat_fraction_ovulation_low"),
                        R.get("fat_fraction_ovulation_high"))
    nurse_factor = (1.0 - R.get("lactation_suppression")
                    if nursing_s_remaining > 0.0 else 1.0)
    return (R.get("conception_probability_per_event")
            * age_factor * body_factor * nurse_factor)


def inseminate(mother_body, mother_sex, father_body, father_sex,
               father_genome, now_s, stream, nursing_s_remaining=0.0):
    """
    Physiological consequence of one insemination event. Returns a
    Pregnancy or None. The event itself is the caller's; this decides only
    what the bodies do with it.
    """
    if father_sex != MALE or not mature(father_body):
        return None
    p = fecundity(mother_body, mother_sex, nursing_s_remaining)
    if p <= 0.0 or stream.random() >= p:
        return None
    return Pregnancy(father_genome, now_s)


def gestation_power_w(pregnancy, now_s):
    """Extra metabolic power a pregnancy draws, in watts."""
    if pregnancy is None or now_s >= pregnancy.due_s:
        return 0.0
    return R.get("gestation_extra_power_w")


def lactation_power_w(nursing_s_remaining):
    """Extra metabolic power nursing draws, in watts."""
    return R.get("lactation_extra_power_w") if nursing_s_remaining > 0.0 else 0.0


def deliver(mother_body, mother_genome, pregnancy, stream):
    """
    Birth. Returns (child_genome, child_body, child_sex, nursing_s).

    A complication injures the mother; whether she dies is decided by the
    same viability check as every other death, so a birth death is tissue
    damage passing its threshold rather than a separate outcome. A poorly
    nourished mother is more likely to suffer one.
    """
    child_genome = GEN.conceive(mother_genome, pregnancy.father_genome, stream)
    child_body = PHY.Body(mass_kg=R.get("birth_mass_kg"))
    child_sex = (MALE if stream.random() < R.get("sex_ratio_male_fraction")
                 else FEMALE)

    condition = max(0.0, min(1.0, mother_body.fat_fraction
                             / R.get("fat_fraction_healthy")))
    p = R.get("birth_complication_probability") * (2.0 - condition)
    if stream.random() < p:
        severity = (stream.uniform(R.get("birth_complication_severity_low"),
                                   R.get("birth_complication_severity_high"))
                    * R.get("damage_lethal_threshold"))
        PHY.injure(mother_body, severity)
        PHY.check_viability(mother_body)

    return child_genome, child_body, child_sex, R.get(
        "lactation_duration_years") * YEAR
