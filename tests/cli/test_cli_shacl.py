from pathlib import Path

import pytest
from typer.testing import CliRunner

from kurra.cli import app
from kurra.shacl import sync_validators

runner = CliRunner()


def shacl_valid():
    SHACL_TEST_DIR = Path(__file__).parent.parent.resolve() / "shacl"

    result = runner.invoke(
        app,
        [
            "shacl",
            "validate",
            f"{SHACL_TEST_DIR / 'vocab-valid.ttl'}",
            f"{SHACL_TEST_DIR / 'validator-vocpub-410.ttl'}",
        ],
    )

    assert result.output.strip() == "The data is valid"


def shacl_invalid():
    SHACL_TEST_DIR = Path(__file__).parent.parent.resolve() / "shacl"

    result = runner.invoke(
        app,
        [
            "shacl",
            "validate",
            f"{SHACL_TEST_DIR / 'vocab-invalid.ttl'}",
            f"{SHACL_TEST_DIR / 'validator-vocpub-410.ttl'}",
        ],
    )
    assert "The errors are:" in result.stdout


@pytest.mark.xfail
def shacl_list_validators():
    sync_validators()

    result = runner.invoke(
        app,
        [
            "shacl",
            "listv",
        ],
    )

    assert "Prez Manifest Validator" in result.output
    assert "fake-validator" not in result.output
