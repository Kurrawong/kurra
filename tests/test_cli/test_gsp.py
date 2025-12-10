import pytest
from typer.testing import CliRunner

from kurra.cli import app
from kurra.cli.console import console
from kurra.sparql import query
from pathlib import Path

runner = CliRunner()


@pytest.mark.xfail  # This test fails with the testcontainer Fuseki image but works on 'rea' Fuseki installations
def test_upload_file(fuseki_container):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    f = Path(__file__).parent / "db" / "config.ttl"

    result = runner.invoke(
        app,
        [
            "db",
            "gsp",
            "upload",
            str(f),
            SPARQL_ENDPOINT,
        ],
    )
    assert result.exit_code == 0

    q = """
        SELECT (COUNT(?s) AS ?count)
        WHERE {
            ?s ?p ?o
        }
        """
    r = query(SPARQL_ENDPOINT, q, return_format="python", return_bindings_only=True)
    assert r[0]["count"] == 142


def test_upload_file_with_graph_id(fuseki_container):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"
    f = Path(__file__).parent / "db" / "config.ttl"

    result = runner.invoke(
        app,
        [
            "db",
            "gsp",
            "upload",
            str(f),
            "-g",
            TESTING_GRAPH,
            SPARQL_ENDPOINT,
        ],
    )
    assert result.exit_code == 0

    q = """
        SELECT (COUNT(?s) AS ?count)
        WHERE {
            ?s ?p ?o
        }
        """
    r = query(SPARQL_ENDPOINT, q, return_format="python", return_bindings_only=True)
    assert r[0]["count"] == 142


def test_upload_file_with_graph_id_file(fuseki_container):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "file"
    f = Path(__file__).parent / "db" / "config.ttl"

    result = runner.invoke(
        app,
        [
            "db",
            "gsp",
            "upload",
            str(f),
            "-g",
            TESTING_GRAPH,
            SPARQL_ENDPOINT,
        ],
    )
    assert result.exit_code == 0

    q = """
        SELECT DISTINCT ?g (COUNT(?s) AS ?count)
        WHERE {
        GRAPH ?g {
                ?s ?p ?o
            }
        }
        GROUP BY ?g
        """
    r = query(SPARQL_ENDPOINT, q, return_format="python", return_bindings_only=True)
    assert r[0]["count"] == 142
    assert r[0]["g"] == "urn:file:config.ttl"