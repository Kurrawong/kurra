from pathlib import Path

from typer.testing import CliRunner

from kurra.cli import app

runner = CliRunner()


def test_cli_valid():
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


def test_cli_invalid():
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
