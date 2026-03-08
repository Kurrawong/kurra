from pathlib import Path
from unittest import result

import pytest
from rdflib import Graph
from typer.testing import CliRunner

from kurra.cli import app
from kurra.cli.commands.labels import find_command, get_command
from kurra.shacl import sync_validators

runner = CliRunner()


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

    assert "sdo:dateCreated" in result.output


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
