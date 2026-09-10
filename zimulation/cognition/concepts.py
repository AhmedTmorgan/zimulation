"""
Concepts: categories a mind makes because they help it predict.

Contract section 19: agents cannot begin with a human ontology. There is no
list of kinds here -- nothing that says the world contains food, tools,
stones, animals or dangers. There are only the features perception reports
and the outcomes the body registers, and a mind that groups experiences
when grouping them lets it anticipate what will happen.

## How a category comes to exist

This is Anderson's rational model of categorisation (Anderson 1991,
Psychological Review 98:409). A category is a statistical summary of its
members: for each perceived feature, how many members showed it, their
mean, and how much they varied. When a new experience arrives, the mind
asks of every category it holds how probable this experience would be if
it belonged there -- and how probable it would be if it belonged to
something never met before. The first depends on the category's own
spread, so a tight category turns away what a loose one admits; the second
depends on the mind's overall sense of how things vary. The more probable
account wins. One prior, the coupling -- how readily two experiences are
taken to be the same kind of thing -- sets how quick the mind is to posit
something new.

Nothing is compared with a named kind. Scales are the agent's own: its
overall sense of each feature, learned from what it has perceived and
floored at a just-noticeable difference, so readings the senses could not
tell apart are never treated as different. A young category's predictions
are heavy-tailed (Student t), because a category known from two members
genuinely does not know its own spread yet.

## A correction found by building this

The first version measured closeness on one shared scale per feature and
admitted an experience if its mean squared deviation stayed under a fixed
vigilance. Over five noisy features that rejected roughly one genuine
member in five, and a single ordinary noise draw on a feature that says
nothing -- felt warmth -- left a freshly struck flake belonging to no
category at all. Judging each category by its own spread is the repair:
a genuine member is now turned away only when it really is improbable.

## How a category earns its keep

A category is worth having only if knowing that something belongs to it
tells you what to expect. Each category tracks what tended to follow its
members -- pain, a sated stomach, whatever outcomes the body registered --
and its predictive value is how far that departs from what follows
experience in general, weighted by how much of experience it covers.
Categories that predict nothing are dissolved once they have had enough
members to be judged. Outcomes never decide which category an experience
joins -- appearance does -- so a category survives only if appearance, so
grouped, actually foretells consequence.

An agent in a world where appearance says nothing about consequence will
therefore hold few categories, and one in a world where it says a great
deal will hold many -- a difference no one wrote.

## Consolidation

Assigning experiences one at a time depends on their order: early on, with
little to judge by, one kind can be split into several. Consolidation
repairs this by Bayesian model comparison. For each pair of categories it
asks whether one category explains both sets of members better than two
do, counting the prior's preference for fewer categories; if so they
merge. There is no threshold: the Occam factor of the marginal likelihood
does the work.

## Prediction

To anticipate what a thing will do, the mind weighs every category by the
probability that the thing belongs there -- including the possibility that
it belongs to none -- and averages what each predicts. Something that fits
nothing well yields a guess near what follows experience in general, which
is what an honest mind should expect of the unfamiliar.

## Provenance

Every category records who made it, when, from which experience, its
examples, and the counterexamples that fit its look but not its outcome.
Counterexamples lower confidence. Merged categories keep the lineage of
what they absorbed. A category received from another agent will record
that too, which is where cultural transmission will attach.

Category identities are opaque tokens. If an observer later glosses one as
"edible-soft-thing", that gloss lives outside the agent.
"""

from __future__ import annotations

import math

from ..core.parameters import REGISTRY as R

_LOG_PI = math.log(math.pi)
_EMPTY = (0, 0.0, 0.0)


# ------------------------------------------------------------ statistics
def _add(stats, v):
    """Welford update of (n, mean, sum of squared deviations)."""
    n, mean, m2 = stats
    n += 1
    d = v - mean
    mean += d / n
    return (n, mean, m2 + d * (v - mean))


def _pool(a, b):
    """Combine two (n, mean, m2) summaries exactly (Chan et al. 1979)."""
    na, ma, sa = a
    nb, mb, sb = b
    n = na + nb
    if n <= 0:
        return _EMPTY
    d = mb - ma
    return (n, ma + d * nb / n, sa + sb + d * d * na * nb / n)


def _posterior(stats, prior):
    """
    Normal-inverse-chi-squared posterior for one feature of one category,
    with the prior's strength used for both its mean and its spread.
    Returns (mean, variance, kappa, dof).
    """
    n, mean, m2 = stats
    mu0, var0, k0 = prior
    kn = k0 + n
    mu = (k0 * mu0 + n * mean) / kn
    var = (k0 * var0 + m2 + (k0 * n / kn) * (mean - mu0) ** 2) / kn
    return mu, var, kn, kn


def _student_logpdf(x, loc, scale, dof):
    z = (x - loc) / scale
    return (math.lgamma((dof + 1) * 0.5) - math.lgamma(dof * 0.5)
            - 0.5 * (math.log(dof) + _LOG_PI) - math.log(scale)
            - (dof + 1) * 0.5 * math.log1p(z * z / dof))


def _log_predictive(x, stats, prior):
    mu, var, kn, dof = _posterior(stats, prior)
    return _student_logpdf(x, mu, math.sqrt(var * (1 + 1 / kn)), dof)


def _log_evidence(stats, prior):
    """
    Marginal likelihood of a category's values on one feature (Murphy
    2007, conjugate analysis of the Gaussian, normal-inverse-chi-squared).
    """
    n = stats[0]
    if n <= 0:
        return 0.0
    _, var0, k0 = prior
    _, var, kn, dof = _posterior(stats, prior)
    return (math.lgamma(dof * 0.5) - math.lgamma(k0 * 0.5)
            + 0.5 * (math.log(k0) - math.log(kn))
            + k0 * 0.5 * math.log(k0 * var0)
            - dof * 0.5 * math.log(dof * var)
            - n * 0.5 * _LOG_PI)


# --------------------------------------------------------------- category
class Concept:
    """One category: a summary of its members, what follows them, and
    where it came from."""

    __slots__ = ("id", "creator", "origin_time", "origin_trace", "stats",
                 "outcome_mean", "outcome_n", "n", "n_counter", "examples",
                 "counterexamples", "absorbed", "received_from")

    def __init__(self, cid, creator, time, trace_id):
        self.id = cid
        self.creator = creator
        self.origin_time = time
        self.origin_trace = trace_id
        self.stats = {}
        self.outcome_mean = {}
        self.outcome_n = {}
        self.n = 0
        self.n_counter = 0
        self.examples = []
        self.counterexamples = []
        self.absorbed = ()
        self.received_from = None

    @property
    def prototype(self):
        return {f: s[1] for f, s in self.stats.items()}

    def __repr__(self):
        return f"<Concept {self.id} n={self.n}>"


class Concepts:
    """One agent's categories, and its own sense of how things vary."""

    __slots__ = ("owner", "items", "_seq", "_feat", "_out")

    def __init__(self, owner):
        self.owner = owner
        self.items = []
        self._seq = 0
        self._feat = {}      # feature -> (n, mean, m2) over all experience
        self._out = {}       # outcome -> [n, mean] over all experience

    # -------------------------------------------------- the agent's scale
    def _see(self, features, outcome):
        for f, v in features.items():
            self._feat[f] = _add(self._feat.get(f, _EMPTY), v)
        for o, v in outcome.items():
            s = self._out.setdefault(o, [0, 0.0])
            s[0] += 1
            s[1] += (v - s[1]) / s[0]

    def _prior(self, f):
        """
        The agent's overall sense of feature f -- its mean and spread over
        everything perceived -- floored at a just-noticeable difference.
        """
        n, mean, m2 = self._feat[f]
        var = m2 / (n - 1) if n > 1 else 0.0
        floor = max(R.get("weber_fraction_magnitude") * abs(mean),
                    R.get("division_epsilon"))
        return mean, max(var, floor * floor), R.get("concept_prior_strength")

    # ----------------------------------------------------------- judging
    def _scores(self, features):
        """
        Log posterior (unnormalised) that these features belong to each
        category, and that they belong to none yet known.
        """
        known = [(f, v, self._prior(f)) for f, v in features.items()
                 if f in self._feat]
        c = R.get("concept_coupling")
        denom = (1 - c) + c * sum(x.n for x in self.items)
        new = math.log((1 - c) / denom)
        for f, v, p in known:
            new += _log_predictive(v, _EMPTY, p)
        scores = []
        for x in self.items:
            s = math.log(c * x.n / denom)
            for f, v, p in known:
                s += _log_predictive(v, x.stats.get(f, _EMPTY), p)
            scores.append(s)
        return scores, new

    def _weights(self, features):
        scores, new = self._scores(features)
        top = max(scores + [new])
        w = [math.exp(s - top) for s in scores]
        w_new = math.exp(new - top)
        z = sum(w) + w_new
        return [x / z for x in w], w_new / z

    # ----------------------------------------------------------- learning
    def _found(self, time, trace_id):
        self._seq += 1
        c = Concept(("concept", self.owner, self._seq), self.owner, time,
                    trace_id)
        self.items.append(c)
        return c

    def _absorb(self, c, features, outcome, trace_id):
        judged = c.n >= R.get("concept_min_examples")
        dev = R.get("counterexample_deviation")
        counter = judged and any(
            abs(v - c.outcome_mean[k]) > dev
            for k, v in outcome.items() if k in c.outcome_mean)
        c.n += 1
        for f, v in features.items():
            c.stats[f] = _add(c.stats.get(f, _EMPTY), v)
        for o, v in outcome.items():
            k = c.outcome_n.get(o, 0) + 1
            c.outcome_n[o] = k
            m = c.outcome_mean.get(o, v)
            c.outcome_mean[o] = m + (v - m) / k
        cap = int(R.get("concept_example_cap"))
        if counter:
            c.n_counter += 1
            c.counterexamples.append(trace_id)
            del c.counterexamples[:-cap]
        else:
            c.examples.append(trace_id)
            del c.examples[:-cap]

    def learn(self, features, outcome, time, trace_id=None):
        """
        Take one experience -- what was perceived, and what followed -- and
        fold it into the category it most probably belongs to, founding a
        new one if it most probably belongs to none. Appearance alone
        decides; the outcome is recorded, not consulted.
        """
        best = None
        if self.items:
            scores, new = self._scores(features)
            i = max(range(len(scores)), key=scores.__getitem__)
            if scores[i] >= new:
                best = self.items[i]
        if best is None:
            if len(self.items) >= int(R.get("concept_capacity")):
                self.items.remove(min(self.items, key=self.predictive_value))
            best = self._found(time, trace_id)
        self._absorb(best, features, outcome, trace_id)
        self._see(features, outcome)
        return best

    # ------------------------------------------------------------- worth
    def predictive_value(self, c):
        """
        How much knowing membership of this category tells about what
        follows, beyond what follows experience in general, weighted by how
        much of experience the category covers. In squared outcome units.
        """
        total = sum(x.n for x in self.items)
        if total <= 0:
            return 0.0
        gap = 0.0
        for o, m in c.outcome_mean.items():
            g = self._out.get(o)
            if g is not None:
                gap += (m - g[1]) ** 2
        return (c.n / total) * gap

    def confidence(self, c):
        """Support from numbers, discounted by counterexamples; below one."""
        support = c.n / (c.n + R.get("concept_min_examples"))
        return support * (1.0 - c.n_counter / max(1, c.n))

    # ------------------------------------------------------ consolidation
    def _merge_gain(self, a, b, priors, log_alpha):
        """Log Bayes factor for one category over two, with the partition
        prior's preference for fewer categories included."""
        gain = (math.lgamma(a.n + b.n) - math.lgamma(a.n)
                - math.lgamma(b.n) - log_alpha)
        for f in sorted(set(a.stats) | set(b.stats)):
            p = priors.get(f)
            if p is None:
                continue
            sa = a.stats.get(f, _EMPTY)
            sb = b.stats.get(f, _EMPTY)
            gain += (_log_evidence(_pool(sa, sb), p)
                     - _log_evidence(sa, p) - _log_evidence(sb, p))
        return gain

    def _merge(self, host, other):
        for f, s in other.stats.items():
            host.stats[f] = _pool(host.stats.get(f, _EMPTY), s)
        for o, v in other.outcome_mean.items():
            hn = host.outcome_n.get(o, 0)
            on = other.outcome_n[o]
            hv = host.outcome_mean.get(o, v)
            host.outcome_mean[o] = (hv * hn + v * on) / (hn + on)
            host.outcome_n[o] = hn + on
        host.n += other.n
        host.n_counter += other.n_counter
        cap = int(R.get("concept_example_cap"))
        host.examples = (host.examples + other.examples)[-cap:]
        host.counterexamples = (host.counterexamples
                                + other.counterexamples)[-cap:]
        host.absorbed = host.absorbed + (other.id,) + other.absorbed
        self.items.remove(other)

    def consolidate(self):
        """
        Merge, pair by pair, whenever one category explains two sets of
        members better than two categories do. The older category absorbs
        the newer and keeps its lineage. Returns how many merges happened.
        """
        c = R.get("concept_coupling")
        log_alpha = math.log((1 - c) / c)
        priors = {f: self._prior(f) for f in self._feat}
        merges = 0
        while len(self.items) > 1:
            best, pair = 0.0, None
            for i, a in enumerate(self.items):
                for b in self.items[i + 1:]:
                    g = self._merge_gain(a, b, priors, log_alpha)
                    if g > best:
                        best, pair = g, (a, b)
            if pair is None:
                break
            a, b = pair
            host, other = ((a, b) if (a.origin_time, a.id[2])
                           <= (b.origin_time, b.id[2]) else (b, a))
            self._merge(host, other)
            merges += 1
        return merges

    def prune(self):
        """
        Consolidate, then dissolve every category that has had enough
        members to be judged and still predicts nothing. Returns how many
        were dissolved.
        """
        self.consolidate()
        need = R.get("concept_min_examples")
        floor = R.get("concept_min_predictive_value")
        keep = [c for c in self.items
                if c.n < need or self.predictive_value(c) >= floor]
        gone = len(self.items) - len(keep)
        self.items = keep
        return gone

    # --------------------------------------------------------------- use
    def categorize(self, features):
        """The category an experience most probably belongs to, or None if
        it most probably belongs to none this mind knows."""
        if not self.items:
            return None
        scores, new = self._scores(features)
        i = max(range(len(scores)), key=scores.__getitem__)
        return self.items[i] if scores[i] >= new else None

    def predict(self, features):
        """
        What this agent expects to follow an experience like this: the
        outcomes of every category, weighted by how probably the experience
        belongs to each, with the chance that it belongs to none weighted
        toward what follows experience in general. Returns the most
        probable category (or None) and the expected outcomes.
        """
        if not self.items:
            return None, {}
        w, w_new = self._weights(features)
        expect = {}
        for o, g in self._out.items():
            acc = w_new * g[1]
            for wi, c in zip(w, self.items):
                acc += wi * c.outcome_mean.get(o, g[1])
            expect[o] = acc
        i = max(range(len(w)), key=w.__getitem__)
        return (self.items[i] if w[i] >= w_new else None), expect
