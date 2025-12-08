from pathlib import Path

import pytest
from typer.testing import CliRunner

from kurra.db import query
from kurra.db.graph import exists, upload, clear

runner = CliRunner()

TESTS_DIR = Path(__file__).resolve().parent


def test_exists(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    SPARQL_ENDPOINT = f"http://localhost:{port}/ds"
    g1 = exists(SPARQL_ENDPOINT, "http://nothing.com", http_client)
    assert not g1


def test_upload(fuseki_container):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"

    upload(SPARQL_ENDPOINT, Path(__file__).parent.parent / "test_fuseki/config.ttl", TESTING_GRAPH)

    q = """
        SELECT (COUNT(?s) AS ?c)
        WHERE {
            GRAPH ?g {
                ?s ?p ?o
            }
        }
        """
    r = query(SPARQL_ENDPOINT, q, return_format="python", return_bindings_only=True)

    assert r[0]["c"] == 142


@pytest.mark.skip(reason="Test works with normal Fuseki but not testing container version")
def test_upload_no_graph(fuseki_container):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    upload(SPARQL_ENDPOINT, Path(__file__).parent.parent / "test_fuseki/config.ttl", None)

    q = """
        SELECT (COUNT(?s) AS ?c)
        WHERE {
            ?s ?p ?o
        }
        """
    r = query(SPARQL_ENDPOINT, q, return_format="python", return_bindings_only=True)

    print(r)

    assert r[0]["c"] == 142


def test_upload_url(fuseki_container, http_client):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"

    upload(SPARQL_ENDPOINT,
           "https://raw.githubusercontent.com/Kurrawong/kurra/refs/heads/main/tests/test_fuseki/config.ttl",
           TESTING_GRAPH)

    q = """
        SELECT (COUNT(?s) AS ?c)
        WHERE {
            GRAPH ?g {
                ?s ?p ?o
            }
        }
        """
    r = query(SPARQL_ENDPOINT, q, return_format="python", return_bindings_only=True)

    assert r[0]["c"] == 142

    # now test one with Content Negotiation and a redirect
    clear(SPARQL_ENDPOINT, TESTING_GRAPH, http_client)

    upload(SPARQL_ENDPOINT,
           "https://linked.data.gov.au/def/vocdermods",
           TESTING_GRAPH)

    r = query(SPARQL_ENDPOINT, q, return_format="python", return_bindings_only=True)

    assert r[0]["c"] == 86
