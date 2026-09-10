"""
Heritable variation.

Three rules govern this module, and all three were learned the hard way.

**Name the model you are actually using.** Zimulation 1 declared a HEXACO
personality model and then listed Neuroticism among its six dimensions.
Neuroticism is Big Five; HEXACO's fourth factor is Emotionality, and the
two are not the same construct -- Emotionality loads sentimentality and
dependence where Neuroticism loads anger and hostility, which HEXACO
distributes into low Agreeableness instead. Citing one framework while
implementing another borrows credibility that has not been earned. The six
dimensions here are the six HEXACO dimensions, spelled as their authors
spell them.

**Heritability is a fraction of variance, not a mixing weight.** The
tempting implementation -- child = h2 * midparent + (1 - h2) * noise --
looks like heritability and is not. Its variance has a fixed point well
below the founders' (for h2 = 0.45 it settles near 40% of it), so the
population drifts toward uniformity while every number stays plausible.
Zimulation 1 collapsed this way, and the first draft of this module did
too, in a new form, before a test caught it.

The correct model is the infinitesimal model (Fisher 1918; Bulmer 1971):
what is *transmitted* is an additive breeding value, and a child's is its
parents' mean plus a segregation deviation of half the additive variance.
What is *expressed* is that breeding value plus an individual
environmental deviation. Under random mating both variances are then
stable by construction, and h2 = VA / (VA + VE) holds exactly. It also
buys a distinction the mixing-weight version erases: an organism's
disposition and what it passes on are not the same thing.

**Do not proliferate traits, and do not score organisms.** Every trait is
a free parameter; one that no module reads should not exist yet, and the
registry audit of declared-but-unread parameters is the check. Nothing
here computes fitness. Traits act on physiology and behaviour, and those
decide who lives to reproduce.
"""

from __future__ import annotations

import math

from ..core.parameters import REGISTRY as R

#: The six HEXACO dimensions (Ashton & Lee). Spelled as in the framework.
HEXACO = (
    "honesty_humility",
    "emotionality",
    "extraversion",
    "agreeableness",
    "conscientiousness",
    "openness",
)

#: Heritable physical characteristics, read by physiology.
PHYSICAL = (
    "adult_mass_kg",
    "metabolic_efficiency",
    "thermal_tolerance",
)

TRAITS = HEXACO + PHYSICAL


class Genome:
    """
    What one organism carries and what it expresses.

    `additive` holds breeding values -- the part transmitted to offspring.
    `phenotype` holds expressed values -- breeding value plus this
    individual's own environmental deviation, which is not transmitted.
    Indexing a genome returns the phenotype, because that is what acts on
    the world.
    """

    __slots__ = ("additive", "phenotype", "generation")

    def __init__(self, additive, phenotype, generation=0):
        self.additive = dict(additive)
        self.phenotype = dict(phenotype)
        self.generation = generation

    def __getitem__(self, trait):
        return self.phenotype[trait]

    def get(self, trait, default=None):
        return self.phenotype.get(trait, default)

    def __repr__(self):
        return f"<Genome gen={self.generation}>"


# ------------------------------------------------------------ variances
def _centre(trait):
    """Population mean of a trait."""
    if trait in HEXACO:
        return 0.5
    if trait == "adult_mass_kg":
        return R.get("reference_body_mass_kg")
    return 1.0


def _phenotypic_sd(trait):
    """Total phenotypic standard deviation of a trait in the population."""
    if trait in HEXACO:
        return R.get("trait_population_sd")
    if trait == "adult_mass_kg":
        return R.get("adult_mass_sd_kg")
    if trait == "metabolic_efficiency":
        return R.get("metabolic_efficiency_sd")
    return R.get("thermal_tolerance_sd")


def _heritability(trait):
    if trait in HEXACO:
        return R.get("trait_heritability")
    return R.get("physical_trait_heritability")


def _bounds(trait):
    if trait in HEXACO:
        return 0.0, 1.0
    if trait == "adult_mass_kg":
        return R.get("adult_mass_min_kg"), R.get("adult_mass_max_kg")
    return (R.get("physiology_multiplier_min"),
            R.get("physiology_multiplier_max"))


def _split(trait):
    """
    Standard deviations of the additive and environmental components.

    VA = h2 * VP and VE = (1 - h2) * VP, so the two components are not
    independent parameters: fixing the phenotypic spread and the
    heritability fixes both. Declaring them separately would add a free
    parameter that could silently disagree with the other two.
    """
    sd_p = _phenotypic_sd(trait)
    h2 = _heritability(trait)
    return math.sqrt(h2) * sd_p, math.sqrt(1.0 - h2) * sd_p


def _clip(trait, v):
    low, high = _bounds(trait)
    return max(low, min(high, v))


def _mutation_sd(trait):
    """
    Mutational input per generation, scaled to the trait's own spread so
    that one declared number serves every trait.
    """
    rel = R.get("mutation_sd") / R.get("trait_population_sd")
    return rel * _phenotypic_sd(trait)


# ---------------------------------------------------------------- making
def founder(stream):
    """A genome with no ancestry, drawn from the population distribution."""
    additive, phenotype = {}, {}
    for t in TRAITS:
        sd_a, sd_e = _split(t)
        a = stream.gauss(_centre(t), sd_a)
        additive[t] = a
        phenotype[t] = _clip(t, a + stream.gauss(0.0, sd_e))
    return Genome(additive, phenotype, generation=0)


def conceive(mother, father, stream):
    """
    A child's genome from two parents.

    Breeding value: the parents' mean plus a segregation deviation with
    variance VA / 2. That second term is what keeps additive variance
    stable under random mating -- averaging two parents halves variance,
    Mendelian segregation restores it. Leave it out and variance halves
    every generation; replace it with noise drawn toward a population mean
    and variance settles at a fraction of where it started.

    Phenotype: breeding value plus this child's own environmental
    deviation, which it does not pass on.
    """
    additive, phenotype = {}, {}
    for t in TRAITS:
        sd_a, sd_e = _split(t)
        mid = 0.5 * (mother.additive[t] + father.additive[t])
        a = (mid + stream.gauss(0.0, sd_a / math.sqrt(2.0))
             + stream.gauss(0.0, _mutation_sd(t)))
        additive[t] = a
        phenotype[t] = _clip(t, a + stream.gauss(0.0, sd_e))
    return Genome(additive, phenotype,
                  generation=max(mother.generation, father.generation) + 1)


def population_variance(genomes, trait):
    """
    Phenotypic spread of a trait across a population.

    Exposed because variance collapse is a silent failure: everything
    keeps running, the numbers stay plausible, and the population quietly
    converges. A test watches this across thirty generations.
    """
    vals = [g[trait] for g in genomes]
    if len(vals) < 2:
        return 0.0
    mean = sum(vals) / len(vals)
    return sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
