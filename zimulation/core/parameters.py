"""
The parameter registry.

Zimulation 1 ended with roughly seven hundred hand-chosen numbers, most of
them written inline and never declared anywhere. When the manifest was
finally made to count them honestly, the published figure went from 66 to
about 700. A model with seven hundred free parameters can produce almost
any history, so it predicts nothing.

This module exists so that cannot happen again. Every number used in
causal code must be declared here first, with its category, units, range,
source and uncertainty. Undeclared constants fail the build.

Categories (docs/SCIENTIFIC_CONTRACT.md section 7):

    P  physical      externally constrained by physics
    B  biological    externally constrained by biology
    H  hypothesis    deliberately under test
    S  structural    model architecture choice, not a claim about reality
    N  numerical     computational approximation, carries no causal claim

The distinction that matters most is H versus the rest. An H parameter is
a question the experiment is asking. A P or B parameter is something the
world already settled. Confusing the two is how a model begins to fit its
own conclusions.
"""

from __future__ import annotations

import hashlib
import json
import math

CATEGORIES = {
    "P": "physical - externally constrained",
    "B": "biological - externally constrained",
    "H": "hypothesis - deliberately under test",
    "S": "structural - model architecture choice",
    "N": "numerical - approximation, no causal claim",
}

#: Categories whose values assert something about the real world. These are
#: the ones a reviewer must interrogate; S and N assert nothing.
CLAIM_BEARING = ("P", "B", "H")


class ParameterError(Exception):
    pass


class Parameter:
    __slots__ = ("name", "category", "units", "default", "low", "high",
                 "source", "uncertainty", "modules", "notes")

    def __init__(self, name, category, units, default, low, high,
                 source, uncertainty, modules, notes=""):
        if category not in CATEGORIES:
            raise ParameterError(
                f"{name}: category {category!r} not one of {sorted(CATEGORIES)}")
        if not source or source.strip().upper() in ("TODO", "TBD", "?"):
            raise ParameterError(
                f"{name}: every parameter needs a source. For H, state the "
                f"hypothesis it tests; for S/N, state why this value.")
        if low is not None and high is not None and low > high:
            raise ParameterError(f"{name}: range [{low}, {high}] is inverted")
        if low is not None and default < low:
            raise ParameterError(f"{name}: default {default} below low {low}")
        if high is not None and default > high:
            raise ParameterError(f"{name}: default {default} above high {high}")
        if category in CLAIM_BEARING and not units:
            raise ParameterError(
                f"{name}: a {category} parameter asserts something about the "
                f"world, so it needs units (use 'dimensionless' if truly none)")
        self.name = name
        self.category = category
        self.units = units
        self.default = default
        self.low = low
        self.high = high
        self.source = source
        self.uncertainty = uncertainty
        self.modules = tuple(modules)
        self.notes = notes

    def as_dict(self):
        return {
            "name": self.name, "category": self.category, "units": self.units,
            "default": self.default, "low": self.low, "high": self.high,
            "source": self.source, "uncertainty": self.uncertainty,
            "modules": list(self.modules), "notes": self.notes,
        }


class Registry:
    """
    Holds every declared parameter and the values in force.

    It is also the audit trail. `used` records which parameters were
    actually read during a run, so a parameter declared and never touched
    shows up as dead weight, and code reading a parameter it never declared
    an interest in shows up as a leak.
    """

    def __init__(self):
        self._params = {}
        self._values = {}
        self.used = set()

    def declare(self, name, category, units, default, low=None, high=None,
                source="", uncertainty="unknown", modules=(), notes=""):
        if name in self._params:
            raise ParameterError(f"{name}: declared twice")
        p = Parameter(name, category, units, default, low, high,
                      source, uncertainty, modules, notes)
        self._params[name] = p
        self._values[name] = default
        return p

    def get(self, name):
        if name not in self._values:
            raise ParameterError(
                f"{name}: read but never declared. Every number in causal "
                f"code must be declared in the registry first.")
        self.used.add(name)
        return self._values[name]

    def set(self, name, value):
        if name not in self._params:
            raise ParameterError(f"{name}: cannot set an undeclared parameter")
        p = self._params[name]
        if p.low is not None and value < p.low:
            raise ParameterError(f"{name}: {value} below allowed {p.low}")
        if p.high is not None and value > p.high:
            raise ParameterError(f"{name}: {value} above allowed {p.high}")
        self._values[name] = value

    def all(self):
        return dict(self._params)

    def values(self):
        return dict(self._values)

    def by_category(self):
        out = {k: [] for k in CATEGORIES}
        for p in self._params.values():
            out[p.category].append(p.name)
        return {k: sorted(v) for k, v in out.items()}

    def unused(self):
        return sorted(set(self._params) - self.used)

    def hash(self):
        """
        Stable hash of the values in force. Goes into every result record;
        two results with different hashes are not comparable.
        """
        blob = json.dumps(
            {k: _canon(v) for k, v in sorted(self._values.items())},
            sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def manifest(self):
        cat = self.by_category()
        counts = {k: len(v) for k, v in cat.items()}
        claims = sum(counts[k] for k in CLAIM_BEARING)
        L = ["# Parameter manifest", ""]
        L.append(f"total declared: **{len(self._params)}** - "
                 f"hash `{self.hash()}`")
        L.append("")
        L.append("| category | count | meaning |")
        L.append("|---|---|---|")
        for k, desc in CATEGORIES.items():
            L.append(f"| {k} | {counts[k]} | {desc} |")
        L.append("")
        L.append(f"**{claims}** of these assert something about the real "
                 f"world (P, B, H). The rest are architecture and arithmetic.")
        if cat["H"]:
            L.append("")
            L.append("## Hypothesis parameters - what the experiment asks")
            L.append("")
            for n in cat["H"]:
                p = self._params[n]
                L.append(f"- `{n}` = {p.default} {p.units} - {p.source}")
        dead = self.unused()
        if dead:
            L.append("")
            L.append(f"## Declared but never read ({len(dead)})")
            L.append("")
            L.append("A parameter nothing reads is dead code, or a mechanism "
                     "that was removed and not cleaned up.")
            L.append("")
            L.append(", ".join(f"`{d}`" for d in dead))
        return "\n".join(L)


def _canon(v):
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            raise ParameterError(f"non-finite parameter value: {v}")
        return round(v, 12)
    return v


#: Process-wide registry. Modules declare into this at import time.
REGISTRY = Registry()
