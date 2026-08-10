from pathlib import Path

import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, SH
from typer.testing import CliRunner

from kurra.cli import app
from kurra.cli.commands import shacl as shacl_commands
from kurra.shacl import sync_validators

runner = CliRunner()
EX = Namespace("http://example.com/")


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
        return True, Graph(), "", Graph()

    monkeypatch.setattr(shacl_commands, "validate", fake_validate)

    result = runner.invoke(
        app,
        ["shacl", "validate", str(data_path), "--shacl", shacl_value],
    )

    assert result.exit_code == 0
    assert received["data"] == [data_path]
    assert isinstance(received["shacl"], expected_type)


@pytest.mark.parametrize("summary_option", ["--summary", "-y"])
def test_validate_cli_summary(tmp_path, monkeypatch, summary_option):
    data_path = tmp_path / "data.ttl"
    data_path.touch()

    sg = Graph()
    report = BNode()
    counts = BNode()
    result_summary = BNode()
    sg.add((report, RDF.type, EX.ValidationReportSummary))
    sg.add((report, EX["counts"], counts))
    sg.add((counts, RDF.type, EX.ValidationCounts))
    sg.add((counts, EX.violationCount, Literal(2)))
    sg.add((counts, EX.warningCount, Literal(1)))
    sg.add((counts, EX.infoCount, Literal(0)))
    sg.add((report, EX["result"], result_summary))
    sg.add((result_summary, RDF.type, EX.ValidationResultSummary))
    sg.add((result_summary, EX["count"], Literal(3)))
    sg.add((result_summary, SH.sourceShape, URIRef("http://example.com/TestShape")))
    sg.add((result_summary, SH.resultMessage, Literal("Test message")))
    sg.add((result_summary, EX.exampleNode, URIRef("http://example.com/example")))

    monkeypatch.setattr(
        shacl_commands,
        "validate",
        lambda *args, **kwargs: (False, Graph(), "", sg),
    )

    result = runner.invoke(
        app,
        [
            "shacl",
            "validate",
            str(data_path),
            "--shacl",
            "validator.ttl",
            summary_option,
        ],
    )

    assert result.exit_code == 0
    assert "Validation summary" in result.output
    assert "Violations: 2" in result.output
    assert "TestShape" in result.output
    assert "Test message" in result.output


@pytest.mark.parametrize(
    ("summary_args", "expected_value", "unexpected_value"),
    [
        ([], "full result", "summary result"),
        (["--summary"], "summary result", "full result"),
    ],
)
def test_validate_cli_rdf_output(
    tmp_path, monkeypatch, summary_args, expected_value, unexpected_value
):
    data_path = tmp_path / "data.ttl"
    data_path.touch()

    results_graph = Graph()
    results_graph.add((EX.report, EX.value, Literal("full result")))
    summary_graph = Graph()
    summary_graph.add((EX.summary, EX.value, Literal("summary result")))
    monkeypatch.setattr(
        shacl_commands,
        "validate",
        lambda *args, **kwargs: (False, results_graph, "", summary_graph),
    )

    result = runner.invoke(
        app,
        [
            "shacl",
            "validate",
            str(data_path),
            "--shacl",
            "validator.ttl",
            "--format",
            "rdf",
            *summary_args,
        ],
    )

    assert result.exit_code == 0
    assert expected_value in result.output
    assert unexpected_value not in result.output


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
