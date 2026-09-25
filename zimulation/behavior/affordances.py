"""
Action affordances: what this body can attempt here, before it knows what
anything is for.

This module deliberately contains no goals and no semantic shortcuts.  It
looks only at the body's current reach, what is in its hands, and adjacent
places.  It does not inspect material, nutritive, thermal, toxic or other
hidden properties.  The primitive itself remains the final physical gate:
an offered grasp may fail because the object is too heavy, a cut may fail
because the edge is blunt, and rubbing may produce nothing.

The purpose is to keep the open-ended experiment honest.  If a physical
primitive exists in the world but the agent can never choose it, then the
corresponding discoveries are impossible by construction even though the
physics appears to permit them.
"""

from __future__ import annotations


#: Actions whose target contains a destination cell as well as an object.
#: Direction is deliberately local: exploration can choose an adjacent
#: direction without consulting a global map.
DIRECTIONAL = frozenset(("apply_force", "throw"))


#: Multi-object acts.  No item in this set says what an act is useful for.
MULTI_OBJECT = frozenset(("strike", "rub", "separate", "combine"))


def available(actor, terrain):
    """Return ``action -> tuple(target-tuples)`` for acts possible to try.

    "Possible to try" is intentionally weaker than "will work".  A body
    may attempt to bite stone or lift a log and learn from failure.  This
    function therefore uses reach and gross body configuration only; it
    never peeks at the true properties that determine the outcome.
    """
    near = tuple(actor.cell.things)
    held = tuple(actor.held)
    reach = held + near
    neighbours = tuple(terrain.neighbours(actor.cell.x, actor.cell.y))

    out = {"rest": ((),)}
    if neighbours:
        out["move"] = tuple((cell,) for cell in neighbours)
    if near:
        out["grasp"] = tuple((thing,) for thing in near)
        if neighbours:
            out["apply_force"] = tuple(
                (thing, cell) for thing in near for cell in neighbours)
    if held:
        out["release"] = tuple((thing,) for thing in held)
        if neighbours:
            out["throw"] = tuple(
                (thing, cell) for thing in held for cell in neighbours)
    if reach:
        out["consume"] = tuple((thing,) for thing in reach)
        out["touch"] = tuple((thing,) for thing in reach)

    pairs = tuple((a, b) for a in held for b in reach if a is not b)
    if pairs:
        out["strike"] = pairs
        out["rub"] = pairs
        out["separate"] = pairs

    # Combination does not require the candidate binder to be held.  The
    # body can manipulate two things at its feet; the primitive decides
    # whether either can physically hold the other.
    combos = []
    for i, a in enumerate(reach):
        for b in reach[i + 1:]:
            combos.append((a, b))
    if combos:
        out["combine"] = tuple(combos)

    return out
