"""
Memory.

Memory here is not a record. It is a set of traces that fade, blend, lose
track of where they came from, and change a little every time they are
recalled. Contract section 16 asks for exactly that, and for one boundary
above all: the agent must never have access to whether a memory is true.

## The boundary, made structural

Zimulation 1 stored a `truth` field on each trace and relied on a test
that grepped decision code for reads of it. That caught one real leak,
which is precisely why a convention is not enough.

Here, what actually happened is stored only inside a `GroundTruth`
wrapper -- the trace's `ground`. An agent holds it like a sealed envelope.
Inside a causal block it cannot be opened by any route; outside, only an
observer module may open it, and every opening is audited. So "was this
memory accurate?" is a question the observer can answer and the agent
cannot even ask.

## False memory without anything planting it

Nothing here writes a false memory. Three ordinary mechanisms produce
them, each with a literature behind it:

**Source fades faster than content** (Johnson, Hashtroudi & Lindsay 1993).
Weeks later you remember *that* the river floods at the turn of the
season, but not whether you saw it or were told. As source memory fades,
the chance that the trace is re-attributed rises with it, biased toward
one's own experience -- so the longer ago something was heard, the likelier
it is now remembered as seen.

The first version used a threshold: one re-attribution draw when source
strength crossed a half, then immunity. That produced a step -- nothing for
a week, then 71% overnight, then flat forever -- so a thing heard two years
ago was no likelier to feel witnessed than one heard two weeks ago. The
hazard form removes the hidden threshold and gives the smooth rise.

**Recall is reconstruction** (Bartlett 1932; Nader et al. 2000). Each
retrieval returns a slightly altered view and stores it back. A memory
recalled often is strengthened -- and drifted.

**Similar episodes blend** into a gist that matches no single event. The
lineage is kept (`merged_from`), so the observer can trace the blend back
to what it came from, but the agent sees one memory where there were
several.

The observer can then measure misattribution, drift and fusion by
comparing each trace against its sealed `ground`. The agent lives with
the result.
"""

from __future__ import annotations

from ..core.parameters import REGISTRY as R
from ..core.scheduler import DAY

#: Where an agent believes a trace came from (contract section 17).
OBSERVED = "observed"
INFERRED = "inferred"
TOLD = "told"
RECONSTRUCTED = "reconstructed"
IMITATED = "imitated"
RECORD = "record"
SOURCES = (OBSERVED, INFERRED, TOLD, RECONSTRUCTED, IMITATED, RECORD)


class Trace:
    """
    One remembered episode.

    `source` is where the agent *believes* it came from, and can change as
    source memory fades. Where it really came from is inside `ground`,
    sealed. `strength` is accessibility; `source_strength` is how well the
    agent still remembers the source; `salience` is how arousing the
    episode was, which protects both.
    """

    __slots__ = ("id", "subject", "t_event", "t_encoded", "features",
                 "source", "source_settled", "strength", "source_strength",
                 "salience", "recalls", "merged_from", "ground")

    def __init__(self, tid, subject, t_event, t_encoded, features, source,
                 salience, ground):
        self.id = tid
        self.subject = subject
        self.t_event = t_event
        self.t_encoded = t_encoded
        self.features = dict(features)
        self.source = source
        self.source_settled = False
        self.strength = 1.0
        self.source_strength = 1.0
        self.salience = max(0.0, min(1.0, salience))
        self.recalls = 0
        self.merged_from = ()
        self.ground = ground

    def __repr__(self):
        return (f"<Trace {self.id} {self.source} s={self.strength:.2f} "
                f"src={self.source_strength:.2f}>")


def _halving(dt_s, half_life_days):
    return 0.5 ** (dt_s / (half_life_days * DAY))


def _similarity(a, b):
    """
    How alike two feature sets are, 0..1. Only comparable when they report
    the same features; otherwise they are different kinds of episode.
    """
    if set(a) != set(b) or not a:
        return 0.0
    tot = 0.0
    n = 0
    for k, va in a.items():
        vb = b[k]
        if not isinstance(va, (int, float)) or not isinstance(vb, (int, float)):
            continue
        span = max(abs(va), abs(vb), R.get("division_epsilon"))
        tot += min(1.0, abs(va - vb) / span)
        n += 1
    return 1.0 - tot / n if n else 0.0


class Memory:
    """One agent's episodic store."""

    __slots__ = ("traces", "_next", "capacity")

    def __init__(self):
        self.traces = []
        self._next = 1
        self.capacity = int(R.get("episodic_capacity"))

    def encode(self, subject, t_event, t_now, features, source,
               salience=0.0, ground=None):
        """
        Store an episode. `ground` is the sealed record of what actually
        happened; the caller that knows the truth passes it in, and nothing
        in cognition can open it again.
        """
        tr = Trace(self._next, subject, t_event, t_now, features, source,
                   salience, ground)
        self._next += 1
        self.traces.append(tr)
        if len(self.traces) > self.capacity:
            self.traces.remove(min(self.traces, key=lambda t: t.strength))
        return tr

    def decay(self, dt_s, stream):
        """
        Let time pass. Content and source fade at their own rates, arousal
        protects both, weak traces are lost -- and as a trace's source
        fades, it becomes steadily likelier to be re-attributed to one's
        own experience.

        The re-attribution hazard is exact rather than approximate: the
        cumulative chance equals `bias * (1 - source_strength)` at every
        step boundary, so the outcome distribution does not depend on how
        time is chopped up. That matters because the engine advances time
        in irregular jumps.
        """
        gain = R.get("arousal_retention_gain")
        content_hl = R.get("memory_half_life_days")
        source_hl = R.get("source_half_life_days")
        floor = R.get("forget_threshold")
        bias = R.get("source_default_bias")
        eps = R.get("division_epsilon")
        kept = []
        for tr in self.traces:
            protect = 1.0 + (gain - 1.0) * tr.salience
            tr.strength *= _halving(dt_s, content_hl * protect)
            before = tr.source_strength
            tr.source_strength *= _halving(dt_s, source_hl * protect)
            if not tr.source_settled and tr.source != OBSERVED:
                done = bias * (1.0 - before)
                target = bias * (1.0 - tr.source_strength)
                hazard = (target - done) / max(eps, 1.0 - done)
                if stream.random() < hazard:
                    tr.source = OBSERVED
                    tr.source_settled = True
            if tr.strength >= floor:
                kept.append(tr)
        self.traces = kept

    def recall(self, tr, stream):
        """
        Retrieve a trace. Returns what the agent remembers, which is not
        quite what was stored: the view is reconstructed with drift and
        written back, and the retrieval itself strengthens the trace.
        """
        sd = R.get("recall_drift_sd")
        view = {}
        for k, v in tr.features.items():
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                view[k] = v
            else:
                view[k] = v * stream.gauss(1.0, sd)
        tr.features = dict(view)
        tr.recalls += 1
        tr.strength = min(1.0, tr.strength + R.get("recall_strengthening"))
        return view

    def consolidate(self):
        """
        Blend near-identical episodes of the same subject into gists.

        Deterministic: pairs are considered in trace order. The merged
        trace keeps the lineage of everything it absorbed, and seals the
        grounds of its parents together so the observer can still see
        what it was made from.
        """
        from ..observer.truth import GroundTruth
        threshold = R.get("merge_similarity")
        out = []
        for tr in self.traces:
            host = None
            for other in out:
                if (other.subject == tr.subject
                        and _similarity(other.features, tr.features)
                        >= threshold):
                    host = other
                    break
            if host is None:
                out.append(tr)
                continue
            w_a, w_b = host.strength, tr.strength
            tot = max(R.get("division_epsilon"), w_a + w_b)
            for k, v in tr.features.items():
                hv = host.features.get(k)
                if isinstance(v, (int, float)) and isinstance(hv, (int, float)) \
                        and not isinstance(v, bool):
                    host.features[k] = (hv * w_a + v * w_b) / tot
            host.merged_from = (host.merged_from + (tr.id,)
                                + tr.merged_from)
            host.t_event = min(host.t_event, tr.t_event)
            host.strength = max(host.strength, tr.strength)
            host.salience = max(host.salience, tr.salience)
            if host.ground is not None or tr.ground is not None:
                host.ground = GroundTruth("merged_trace_origins",
                                          (host.ground, tr.ground))
        self.traces = out

    def about(self, subject):
        """Traces concerning one subject, strongest first."""
        return sorted((t for t in self.traces if t.subject == subject),
                      key=lambda t: t.strength, reverse=True)
