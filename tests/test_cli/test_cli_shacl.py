from pathlib import Path
from kurra.shacl import list_local_validators, sync_validators
from kurra.utils import make_httpx_client

from typer.testing import CliRunner

from kurra.cli import app

runner = CliRunner()


def test_shacl_valid():
    SHACL_TEST_DIR = Path(__file__).parent.parent.resolve() / "test_shacl"

    result = runner.invoke(
        app,
        [
            "shacl",
            "validate",
            f"{SHACL_TEST_DIR / 'vocab-valid.ttl'}",
            f"{SHACL_TEST_DIR / 'validator-vocpub-410.ttl'}",
        ],
    )
    assert result.stdout.strip() == "The data is valid"


def test_shacl_invalid():
    SHACL_TEST_DIR = Path(__file__).parent.parent.resolve() / "test_shacl"

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


def test_shacl_list_validators():
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
