from pathlib import Path

import pytest
from rdflib import URIRef
from rdflib.namespace import RDF
from typer.testing import CliRunner

from kurra.cli import app
from kurra.db.gsp import get, put, upload
from kurra.sparql import query

runner = CliRunner()


def test_exists(fuseki_container, http_client):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"
    f = Path(__file__).parent / "config.ttl"

    upload(SPARQL_ENDPOINT, f, TESTING_GRAPH, http_client=http_client)

    result = runner.invoke(
        app,
        [
            "db",
            "gsp",
            "exists",
            "-g",
            TESTING_GRAPH,
            SPARQL_ENDPOINT,
        ],
    )
    assert "True" in result.output

    result = runner.invoke(
        app,
        [
            "db",
            "gsp",
            "exists",
            "-g",
            "http://nothing.com",
            SPARQL_ENDPOINT,
        ],
    )
    assert "False" in result.output

    # default graph
    result = runner.invoke(
        app,
        [
            "db",
            "gsp",
            "exists",
            SPARQL_ENDPOINT,
        ],
    )
    assert "True" in result.output


def test_get(fuseki_container, http_client):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"
    f = Path(__file__).parent / "config.ttl"

    upload(SPARQL_ENDPOINT, f, TESTING_GRAPH, http_client=http_client)

    result = runner.invoke(
        app,
        [
            "db",
            "gsp",
            "get",
            "-g",
            TESTING_GRAPH,
            SPARQL_ENDPOINT,
        ],
    )
    assert "PREFIX bibo:" in result.output

    result = runner.invoke(
        app,
        [
            "db",
            "gsp",
            "get",
            "-g",
            "http://nothing.com",
            SPARQL_ENDPOINT,
        ],
    )
    assert "Graph not found" in result.output

    # default graph
    result = runner.invoke(
        app,
        [
            "db",
            "gsp",
            "get",
            SPARQL_ENDPOINT,
        ],
    )
    assert "No content" in result.output


def test_put(fuseki_container, http_client):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"
    f = Path(__file__).parent / "config.ttl"

    runner.invoke(
        app,
        [
            "db",
            "gsp",
            "put",
            str(f),
            "-g",
            TESTING_GRAPH,
            SPARQL_ENDPOINT,
        ],
    )

    r = get(SPARQL_ENDPOINT, TESTING_GRAPH, http_client=http_client)
    assert (
        URIRef("http://base/#service_tdb_all"),
        RDF.type,
        URIRef("http://jena.apache.org/fuseki#Service"),
    ) in r

    # delete(SPARQL_ENDPOINT, "all", http_client=http_client)

    r = get(SPARQL_ENDPOINT, http_client=http_client)
    assert len(r) == 0

    runner.invoke(
        app,
        [
            "db",
            "gsp",
            "put",
            str(Path(__file__).parent.parent.resolve().parent / "rdf" / "rdf_1.ttl"),
            "-g",
            "default",
            # no -g so default
            SPARQL_ENDPOINT,
        ],
    )
    r = get(SPARQL_ENDPOINT, http_client=http_client)
    assert (
        URIRef("http://example.com/a"),
        URIRef("http://example.com/b"),
        URIRef("http://example.com/c"),
    ) in r


def test_post(fuseki_container, http_client):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"
    f = Path(__file__).parent / "config.ttl"

    put(SPARQL_ENDPOINT, f, TESTING_GRAPH, http_client=http_client)

    r = get(SPARQL_ENDPOINT, TESTING_GRAPH, http_client=http_client)
    assert len(r) == 142

    runner.invoke(
        app,
        [
            "db",
            "gsp",
            "post",
            str(Path(__file__).parent.parent.resolve().parent / "rdf" / "rdf_1.ttl"),
            "-g",
            TESTING_GRAPH,
            SPARQL_ENDPOINT,
        ],
    )

    r = get(SPARQL_ENDPOINT, TESTING_GRAPH, http_client=http_client)
    assert len(r) == 143


def test_delete(fuseki_container, http_client):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"
    f = Path(__file__).parent / "config.ttl"

    put(SPARQL_ENDPOINT, f, TESTING_GRAPH, http_client=http_client)

    r = get(SPARQL_ENDPOINT, TESTING_GRAPH, http_client=http_client)
    assert len(r) == 142

    runner.invoke(
        app,
        [
            "db",
            "gsp",
            "delete",
            "-g",
            TESTING_GRAPH,
            SPARQL_ENDPOINT,
        ],
    )

    r = get(SPARQL_ENDPOINT, TESTING_GRAPH, http_client=http_client)
    assert r == 404


def test_clear(fuseki_container, http_client):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"
    f = Path(__file__).parent / "config.ttl"

    put(SPARQL_ENDPOINT, f, TESTING_GRAPH, http_client=http_client)

    r = get(SPARQL_ENDPOINT, TESTING_GRAPH, http_client=http_client)
    assert len(r) == 142

    runner.invoke(
        app,
        [
            "db",
            "gsp",
            "delete",
            "-g",
            TESTING_GRAPH,
            SPARQL_ENDPOINT,
        ],
    )

    r = get(SPARQL_ENDPOINT, TESTING_GRAPH, http_client=http_client)
    assert r == 404


@pytest.mark.xfail  # This test fails with the testcontainer Fuseki image but works on 'rea' Fuseki installations
def test_upload_file(fuseki_container):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    f = Path(__file__).parent / "config.ttl"

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
    f = Path(__file__).parent / "config.ttl"

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
    f = Path(__file__).parent / "config.ttl"

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
