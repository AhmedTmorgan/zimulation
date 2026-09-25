"""Physical contact gates for object-on-object actions.

This is world physics, not cognition.  An agent may choose to attempt an
action without knowing why it can or cannot work; the world is allowed to
refuse an impossible contact.  Keeping this gate outside the decision code
preserves the ground-truth boundary while preventing degenerate zero-area
objects from entering the thermal equations.
"""

from __future__ import annotations

from ..core.parameters import REGISTRY as R
from .thermal import cross_section


def rubbing_contact_exists(a, b):
    """Whether two extant objects have a non-zero physical contact face."""
    eps = R.get("division_epsilon")
    return cross_section(a) > eps and cross_section(b) > eps
