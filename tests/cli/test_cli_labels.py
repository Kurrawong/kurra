from pathlib import Path

import pytest
from typer.testing import CliRunner

from kurra.cli import app

runner = CliRunner()


@pytest.fixture
def duplicate_labels_file(tmp_path):
    source = tmp_path / "annotations.nt"
    source.write_text(
        '<urn:node> <http://www.w3.org/2000/01/rdf-schema#label> "Name" .\n'
        '<urn:node> <http://www.w3.org/2000/01/rdf-schema#label> "Name"@en .\n'
        '<urn:node> <http://www.w3.org/2000/01/rdf-schema#comment> "First" .\n'
        '<urn:node> <http://www.w3.org/2000/01/rdf-schema#comment> "Second" .\n'
        '<urn:node> <urn:extra1> "Extra one" .\n'
        '<urn:node> <urn:extra2> "Extra two" .\n'
    )
    return source


@pytest.mark.parametrize(
    "options, expected, absent",
    [
        ([], ['"Name"', '"Name"@en'], "First"),
        (["-n", "descriptions"], ["First", "Second"], "Name"),
        (
            ["-a", "urn:extra1", "-a", "urn:extra2"],
            ["Extra one", "Extra two"],
            "First",
        ),
    ],
)
def test_duplicates_command(duplicate_labels_file, options, expected, absent):
    result = runner.invoke(
        app, ["labels", "duplicates", str(duplicate_labels_file), *options]
    )

    assert result.exit_code == 0, result.output
    assert "urn:node" in result.output
    for value in expected:
        assert value in result.output
    assert absent not in result.output


def test_duplicates_command_empty(tmp_path):
    source = tmp_path / "empty.nt"
    source.write_text("")
    result = runner.invoke(app, ["labels", "duplicates", str(source)])

    assert result.exit_code == 0, result.output
    assert "No nodes with duplicate names" in result.output


def test_duplicates_command_invalid_mode(duplicate_labels_file):
    result = runner.invoke(
        app, ["labels", "duplicates", str(duplicate_labels_file), "-n", "invalid"]
    )

    assert result.exit_code == 2


def test_duplicates_command_missing_path(tmp_path):
    result = runner.invoke(app, ["labels", "duplicates", str(tmp_path / "missing")])

    assert result.exit_code == 2


def test_find_command():
    LABELS_TEST_DIR = Path(__file__).parent.parent.resolve() / "labels"

    result = runner.invoke(
        app,
        ["labels", "find", f"{LABELS_TEST_DIR / 'GeologicMaterialTypes.ttl'}"],
    )

    iris = result.output.splitlines()
    assert len(iris) == 42


def test_get_command():
    LABELS_TEST_DIR = Path(__file__).parent.parent.resolve() / "labels"

    result = runner.invoke(
        app,
        ["labels", "get", f"{LABELS_TEST_DIR / 'GeologicMaterialTypes.ttl'}"],
        color=False,
    )

    assert "date created" in result.output


def test_get_command_table():
    LABELS_TEST_DIR = Path(__file__).parent.parent.resolve() / "labels"

    result = runner.invoke(
        app,
        [
            "labels",
            "get",
            f"{LABELS_TEST_DIR / 'GeologicMaterialTypes.ttl'}",
            "-r",
            "table",
        ],
        color=False,
    )

    assert "Label" in result.output
    assert "http://www.w3.org/2002/07/owl#versionIRI" in result.output
