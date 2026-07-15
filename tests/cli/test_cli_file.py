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
