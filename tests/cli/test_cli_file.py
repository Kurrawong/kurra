import json
import subprocess
from pathlib import Path

import pytest
from rdflib import Graph
from typer.testing import CliRunner

from kurra.cli.commands.file import app

runner = CliRunner()


@pytest.mark.parametrize("context_source", ["inline", "file"])
@pytest.mark.parametrize("indent", [None, 2])
@pytest.mark.parametrize("context_option", ["--context", "-t"])
def test_reformat_cli_context_and_indent(
    tmp_path, context_source, indent, context_option
):
    source = tmp_path / "source.nt"
    source.write_text(
        '<http://example.com/alice> <http://example.com/name> "Alice" .\n',
        encoding="utf-8",
    )
    context = {"@context": {"ex": "http://example.com/"}}
    argument = json.dumps(context)
    if context_source == "file":
        context_path = tmp_path / "context.jsonld"
        context_path.write_text(argument, encoding="utf-8")
        argument = str(context_path)
    destination = tmp_path / "result.jsonld"
    args = [
        "reformat",
        str(source),
        "-f",
        "json-ld",
        "-o",
        str(destination),
        context_option,
        argument,
    ]
    if indent is not None:
        args.extend(["--indent", str(indent)])

    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.output
    document = json.loads(destination.read_text())
    assert document == {**context, "@id": "ex:alice", "ex:name": "Alice"}
    assert destination.read_text() == json.dumps(
        document, indent=4 if indent is None else indent
    )


def test_reformat_cli_context_prefixes(tmp_path):
    source = tmp_path / "source.nt"
    source.write_text(
        '<http://example.com/alice> <http://example.com/name> "Alice" .\n',
        encoding="utf-8",
    )
    destination = tmp_path / "result.n3"

    result = runner.invoke(
        app,
        [
            "reformat",
            str(source),
            "-f",
            "n3",
            "-o",
            str(destination),
            "--context",
            '{"@context": {"ex": "http://example.com/"}}',
        ],
    )

    assert result.exit_code == 0, result.output
    assert 'ex:alice ex:name "Alice"' in destination.read_text()
    assert Graph().parse(source).isomorphic(Graph().parse(destination, format="n3"))


@pytest.mark.parametrize(
    "context",
    [
        '{"@context": {"ex": 42}}',
        "{invalid json",
        "missing-context.jsonld",
    ],
)
def test_reformat_cli_invalid_context(tmp_path, context):
    source = tmp_path / "source.nt"
    source.write_text('<http://example.com/a> <http://example.com/p> "v" .\n')
    destination = tmp_path / "result.jsonld"

    result = runner.invoke(
        app,
        [
            "reformat",
            str(source),
            "-f",
            "json-ld",
            "-o",
            str(destination),
            "--context",
            context,
        ],
    )

    assert result.exit_code == 2
    assert "Invalid value" in result.output
    assert not destination.exists()


def test_reformat_cli_rejects_negative_indent(tmp_path):
    result = runner.invoke(app, ["reformat", str(tmp_path), "--indent", "-1"])

    assert result.exit_code == 2
    assert "Invalid value" in result.output


def test_merge_cli_lists_output_formats():
    result = runner.invoke(app, ["merge", "--help"])

    assert result.exit_code == 0
    for output_format in ["turtle", "longturtle", "xml", "nt", "json-ld"]:
        assert output_format in result.stdout


def test_merge_cli_prints_turtle(tmp_path):
    first = tmp_path / "first.ttl"
    first.write_text("@prefix ex: <http://example.com/> . ex:a ex:p ex:b .")
    second = tmp_path / "second.nt"
    second.write_text(
        "<http://example.com/c> <http://example.com/p> <http://example.com/d> .\n"
    )

    result = runner.invoke(app, ["merge", str(first), str(second)])

    assert result.exit_code == 0
    assert len(Graph().parse(data=result.stdout, format="turtle")) == 2


def test_merge_cli_writes_requested_format(tmp_path):
    first = tmp_path / "first.ttl"
    first.write_text("@prefix ex: <http://example.com/> . ex:a ex:p ex:b .")
    second = tmp_path / "second.ttl"
    second.write_text("@prefix ex: <http://example.com/> . ex:c ex:p ex:d .")
    destination = tmp_path / "merged.nt"

    result = runner.invoke(
        app,
        [
            "merge",
            str(first),
            str(second),
            "--destination",
            str(destination),
            "--output-format",
            "nt",
        ],
    )

    assert result.exit_code == 0
    assert len(Graph().parse(destination, format="nt")) == 2


def test_hierarchy_cli_prints_hierarchy(tmp_path):
    source = tmp_path / "hierarchy.ttl"
    source.write_text(
        """
        @prefix ex: <http://example.com/> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        ex:ontology a owl:Ontology ; rdfs:label "Fruits" .
        ex:Fruit a owl:Class ; rdfs:label "Fruit" .
        ex:Apple a owl:Class ; rdfs:label "Apple" ;
            rdfs:subClassOf ex:Fruit .
        """,
        encoding="utf-8",
    )

    result = runner.invoke(app, ["hierarchy", str(source), "--use-names"])

    assert result.exit_code == 0
    assert result.stdout == "Fruits\n└── Fruit\n    └── Apple\n"


def test_hierarchy_cli_accepts_named_graph(tmp_path):
    source = tmp_path / "hierarchy.trig"
    source.write_text(
        """
        @prefix ex: <http://example.com/> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        ex:wanted {
            ex:Fruit a owl:Class .
            ex:Apple a owl:Class ; rdfs:subClassOf ex:Fruit .
        }
        ex:ignored { ex:Vehicle a owl:Class . }
        """,
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "hierarchy",
            str(source),
            "--graph-iri",
            "http://example.com/wanted",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == "ex:Fruit\n└── ex:Apple\n"


def test_reformat_cli():
    subprocess.check_output(
        [
            "kurra",
            "file",
            "reformat",
            "--output-format",
            "json-ld",
            str(Path(__file__).parent.parent.resolve() / "file/minimal1.ttl"),
        ]
    )

    comparison = """[
  {
    "@id": "http://example.com/a",
    "http://example.com/b": [
      {
        "@id": "http://example.com/c"
      }
    ]
  }
]"""

    output_file = Path(__file__).parent.parent.resolve() / "file/minimal1.jsonld"

    assert open(output_file).read() == comparison

    Path.unlink(output_file)
