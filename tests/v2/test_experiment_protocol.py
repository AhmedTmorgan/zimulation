"""The first V2 experiment runner is reproducible and leaves no state behind."""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import zimulation.behavior.params  # noqa: F401
import zimulation.biology.params  # noqa: F401
import zimulation.cognition.params  # noqa: F401
import zimulation.world.params  # noqa: F401
from experiments.v2.culture_zero_v1 import PROTOCOL, run_seed
from zimulation.core.parameters import REGISTRY as R


def test_culture_zero_smoke_is_deterministic():
    kw = dict(days=0.02, size=12, founders=1, latitude=20.0,
              age_years=25.0, learning=True, consummatory_bias=0.0)
    a = run_seed(991, **kw)
    b = run_seed(991, **kw)
    assert a == b
    assert a["protocol"] == PROTOCOL
    assert len(a["parameter_hash"]) == 16
    assert len(a["ledger_head"]) == 16
    assert a["termination"] in ("duration", "extinction")


def test_runner_restores_process_wide_parameters():
    lat = R.get("map_centre_latitude_degrees")
    bias = R.get("consummatory_bias")
    run_seed(992, days=0.005, size=12, latitude=15.0,
             consummatory_bias=0.5)
    assert R.get("map_centre_latitude_degrees") == lat
    assert R.get("consummatory_bias") == bias


def test_result_contains_no_civilisation_success_score():
    row = run_seed(993, days=0.005, size=12)
    assert "score" not in row
    assert set(row) == {"protocol", "seed", "scenario", "parameter_hash",
                        "ledger_head", "termination", "population",
                        "cognition"}


def _run_all():
    ok = fail = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  PASS  {name}")
            ok += 1
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            fail += 1
        except Exception as e:
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
            fail += 1
    print(f"\n{ok} passed, {fail} failed")
    return fail


if __name__ == "__main__":
    sys.exit(1 if _run_all() else 0)
