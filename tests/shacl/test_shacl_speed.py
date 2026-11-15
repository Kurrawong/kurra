"""Opt-in speed regression tests for a local GSQ vocabulary and cached VocPub."""

import os
import subprocess
import sys
from pathlib import Path
from statistics import median

import pytest

from kurra.shacl import list_local_validators

VOCPUB = "https://linked.data.gov.au/def/vocpub/validator"
TIMING_TOLERANCE = 0.05
VALIDATE_ONCE = """
import sys
from pathlib import Path
from time import perf_counter

from kurra.shacl import validate

data = Path(sys.argv[1])
validator = sys.argv[2]
use_rudof = sys.argv[3] == "True"
start = perf_counter()
conforms, _, _ = validate(data, validator, use_rudof=use_rudof)
elapsed = perf_counter() - start
assert not conforms
print(elapsed)
"""


@pytest.fixture(scope="module")
def minerals_file():
    source = os.environ.get("KURRA_MINERALS_TTL")
    if not source:
        pytest.skip("Set KURRA_MINERALS_TTL to opt into the local speed tests")
    path = Path(source).expanduser()
    assert path.is_file(), f"Minerals fixture not found: {path}"
    assert VOCPUB in list_local_validators(), (
        "Sync the VocPub validator before benchmarking"
    )
    return path


@pytest.mark.parametrize(
    ("use_rudof", "baseline_seconds"),
    [(False, 8.42), (True, 1.30)],
    ids=["pyshacl", "rudof"],
)
def test_validate_minerals_speed(minerals_file, use_rudof, baseline_seconds):
    if use_rudof:
        # A fallback to pySHACL would invalidate the Rudof measurement.
        pytest.importorskip("pyrudof")

    # The reference profile used fresh processes. Exclude interpreter startup.
    elapsed = median(
        float(
            subprocess.check_output(
                [
                    sys.executable,
                    "-c",
                    VALIDATE_ONCE,
                    str(minerals_file),
                    VOCPUB,
                    str(use_rudof),
                ],
                text=True,
            )
        )
        for _ in range(3)
    )
    limit = baseline_seconds * (1 + TIMING_TOLERANCE)
    print(
        f"Median validation time: {elapsed:.3f}s "
        f"(baseline: {baseline_seconds:.2f}s; limit: {limit:.3f}s)"
    )
    assert elapsed <= limit
