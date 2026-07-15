from pathlib import Path

import pytest
from rdflib import Graph
from typer.testing import CliRunner

from kurra.cli import app
from kurra.cli.commands import shacl as shacl_commands
from kurra.shacl import sync_validators

runner = CliRunner()


@pytest.mark.parametrize(
    ("shacl_value", "expected_type"),
    [
        ("validator.ttl", Path),
        ("https://example.com/validator", str),
        ("7", int),
    ],
)
def test_validate_cli_shacl_types(tmp_path, monkeypatch, shacl_value, expected_type):
    data_path = tmp_path / "data.ttl"
    data_path.write_text(
        "<http://example.com/s> <http://example.com/p> <http://example.com/o> ."
    )
    if expected_type is Path:
        shacl_path = tmp_path / shacl_value
        shacl_path.touch()
        shacl_value = str(shacl_path)

    received = {}

    def fake_validate(data, shacl, hide_warnings=False):
        received["data"] = data
        received["shacl"] = shacl
        return True, Graph(), ""

    monkeypatch.setattr(shacl_commands, "validate", fake_validate)

    result = runner.invoke(
        app,
        ["shacl", "validate", str(data_path), "--shacl", shacl_value],
    )

    assert result.exit_code == 0
    assert received["data"] == [data_path]
    assert isinstance(received["shacl"], expected_type)


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
