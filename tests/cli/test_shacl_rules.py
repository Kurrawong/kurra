from pathlib import Path

from rdflib.compare import isomorphic
from typer.testing import CliRunner
from kurra.utils import load_graph
from kurra.cli import app
import click

runner = CliRunner()


def test_infer():
    INFER_DATA_DIR = Path(__file__).parent.parent.resolve() / "shacl" / "infer"

    result = runner.invoke(
        app,
        [
            "shacl",
            "infer",
            f"{INFER_DATA_DIR / '01-data.ttl'}",
            f"{INFER_DATA_DIR / '01-rules.srl'}",
        ],
    )

    assert "ns1:grandParent" in result.output


def test_infer_remove():
    INFER_DATA_DIR = Path(__file__).parent.parent.resolve() / "shacl" / "infer"

    result = runner.invoke(
        app,
        [
            "shacl",
            "infer",
            f"{INFER_DATA_DIR / '01-data.ttl'}",
            f"{INFER_DATA_DIR / '02-rules.srl'}",
        ],
    )

    results_graph_expected = load_graph(
        Path(__file__).parent.parent / "shacl/infer" / "02-results.ttl"
    )
    actual_output = load_graph(click.unstyle(result.output))

    assert isomorphic(results_graph_expected, actual_output)