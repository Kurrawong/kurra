import subprocess
from pathlib import Path

from rdflib import Graph
from typer.testing import CliRunner

from kurra.cli.commands.file import app

runner = CliRunner()


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
