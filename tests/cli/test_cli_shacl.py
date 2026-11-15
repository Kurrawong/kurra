import sys
from pathlib import Path

import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, SH
from typer.testing import CliRunner

import kurra.shacl
from kurra.cli import app
from kurra.cli.commands import shacl as shacl_commands
from kurra.shacl import SH12, sync_validators, validate

runner = CliRunner()
EX = Namespace("http://example.com/")


@pytest.mark.parametrize("use_rudof", [False, True])
def test_validate_merges_local_files(tmp_path, monkeypatch, use_rudof):
    if use_rudof:
        pytest.importorskip("pyrudof")

    focus = tmp_path / "focus.rdf"
    values = tmp_path / "values.rdf"
    shapes = tmp_path / "shapes.rdf"
    Graph().add((EX.subject, RDF.type, EX.Thing)).serialize(focus, format="xml")
    Graph().add((EX.subject, EX.name, Literal("Example"))).serialize(
        values, format="xml"
    )
    shape_graph = Graph()
    shape_graph.add((EX.shape, RDF.type, SH.NodeShape))
    shape_graph.add((EX.shape, SH.targetClass, EX.Thing))
    shape_graph.add((EX.shape, SH.property, EX.propertyShape))
    shape_graph.add((EX.propertyShape, SH.path, EX.name))
    shape_graph.add((EX.propertyShape, SH.minCount, Literal(1)))
    shape_graph.serialize(shapes, format="xml")

    if use_rudof:
        load_graph = kurra.shacl.load_graph

        def load_shapes_only(source):
            assert source == shapes, "Rudof must load the data files directly"
            return load_graph(source)

        monkeypatch.setattr(kurra.shacl, "load_graph", load_shapes_only)

    assert not validate(focus, shapes, use_rudof=use_rudof)[0]
    assert not validate(str(focus), shapes, use_rudof=use_rudof)[0]
    assert validate([focus, values], shapes, use_rudof=use_rudof)[0]
    valid, _, _, provenance = validate(
        [str(focus), values], shapes, return_type="provenance", use_rudof=use_rudof
    )
    assert valid
    agent = "pyrudof" if use_rudof else "pyshacl"
    assert str(
        provenance.value(predicate=RDF.type, object=SH12.ValidationAgent)
    ).startswith(f"https://pypi.org/project/{agent}/")
    assert set(provenance.objects(None, SH12.usedDataGraph)) == {
        URIRef(focus.as_uri()),
        URIRef(values.as_uri()),
    }

    args = ["shacl", "validate", "--shacl", str(shapes), str(focus)]
    if use_rudof:
        args.append("-x")
    single = runner.invoke(app, args)
    assert single.exit_code == 0, single.exception
    assert "The data is NOT valid" in single.output
    merged = runner.invoke(app, [*args, str(values)])
    assert merged.exit_code == 0, merged.exception
    assert "The data is valid" in merged.output


def test_validate_cli_rudof_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "pyrudof", None)
    fixtures = Path(__file__).resolve().parents[1] / "shacl"
    data = fixtures / "vocab-valid.ttl"
    shapes = fixtures / "validator-vocpub-410.ttl"

    with pytest.warns(UserWarning, match="falling back to pySHACL"):
        result = runner.invoke(
            app, ["shacl", "validate", str(data), "-s", str(shapes), "-x"]
        )
    assert result.exit_code == 0, result.exception
    assert "The data is valid" in result.output

    with pytest.warns(UserWarning, match="falling back to pySHACL"):
        valid, _, _, provenance = validate(
            data, shapes, use_rudof=True, return_type="provenance"
        )
    assert valid
    agent = provenance.value(predicate=RDF.type, object=SH12.ValidationAgent)
    assert str(agent).startswith("https://pypi.org/project/pyshacl/")


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

    def fake_validate(
        data,
        shacl,
        hide_warnings=False,
        advanced=False,
        return_type="basic",
        use_rudof=False,
    ):
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


@pytest.mark.parametrize("return_type_option", ["--return", "-r"])
def test_validate_cli_summary(tmp_path, monkeypatch, return_type_option):
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
            return_type_option,
            "summary",
        ],
    )

    assert result.exit_code == 0
    assert "Validation summary" in result.output
    assert "Violations: 2" in result.output
    assert "TestShape" in result.output
    assert "Test message" in result.output


@pytest.mark.parametrize("return_type_option", ["--return", "-r"])
def test_validate_cli_provenance(tmp_path, monkeypatch, return_type_option):
    data_path = tmp_path / "data.ttl"
    data_path.touch()

    provenance_graph = Graph()
    provenance_graph.add((EX.activity, EX.value, Literal("provenance result")))
    monkeypatch.setattr(
        shacl_commands,
        "validate",
        lambda *args, **kwargs: (False, Graph(), "", provenance_graph),
    )

    # no --format passed (defaults to table) - provenance is still shown as Turtle
    result = runner.invoke(
        app,
        [
            "shacl",
            "validate",
            str(data_path),
            "--shacl",
            "validator.ttl",
            return_type_option,
            "provenance",
        ],
    )
    assert result.exit_code == 0
    assert "provenance result" in result.output


@pytest.mark.parametrize(
    ("return_type_args", "expected_value", "unexpected_value"),
    [
        ([], "full result", "extra result"),
        (["--return", "summary"], "extra result", "full result"),
        (["--return", "provenance"], "extra result", "full result"),
    ],
)
def test_validate_cli_rdf_output(
    tmp_path, monkeypatch, return_type_args, expected_value, unexpected_value
):
    data_path = tmp_path / "data.ttl"
    data_path.touch()

    results_graph = Graph()
    results_graph.add((EX.report, EX.value, Literal("full result")))
    extra_graph = Graph()
    extra_graph.add((EX.extra, EX.value, Literal("extra result")))
    monkeypatch.setattr(
        shacl_commands,
        "validate",
        lambda *args, **kwargs: (False, results_graph, "", extra_graph),
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
            *return_type_args,
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


@pytest.mark.parametrize("advanced_option", ["--advanced", "-a"])
def test_validate_cli_advanced(advanced_option):
    SHACL_TEST_DIR = Path(__file__).parent.parent.resolve() / "shacl"
    data = f"{SHACL_TEST_DIR / 'advanced-data.ttl'}"
    shapes = f"{SHACL_TEST_DIR / 'advanced-validator.ttl'}"

    result = runner.invoke(app, ["shacl", "validate", data, "--shacl", shapes])
    assert "The errors are:" in result.stdout

    result = runner.invoke(
        app, ["shacl", "validate", data, "--shacl", shapes, advanced_option]
    )
    assert result.output.strip() == "The data is valid"


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
