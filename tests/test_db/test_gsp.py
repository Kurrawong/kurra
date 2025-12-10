from pathlib import Path

import pytest
from typer.testing import CliRunner

from kurra.db import query
from kurra.db.gsp import clear, delete, exists, get, post, put, upload
from kurra.utils import load_graph

runner = CliRunner()

TESTS_DIR = Path(__file__).resolve().parent
LANG_TEST_VOC = Path(__file__).parent.parent / "test_sparql" / "language-test.ttl"
THREE_TRIPLE_FILE = Path(__file__).parent.parent / "test_file" / "prefixes-test.ttl"
TESTING_GRAPH = "https://example.com/testing-graph"


def test_exists(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    SPARQL_ENDPOINT = f"http://localhost:{port}/ds"
    g1 = exists(SPARQL_ENDPOINT, "http://nothing.com", http_client)
    assert not g1

    upload(SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, http_client)
    g2 = exists(SPARQL_ENDPOINT, TESTING_GRAPH, http_client)
    assert g2

    delete(SPARQL_ENDPOINT, TESTING_GRAPH, http_client)
    g3 = exists(SPARQL_ENDPOINT, TESTING_GRAPH, http_client)
    assert not g3


def test_get(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    SPARQL_ENDPOINT = f"http://localhost:{port}/ds"

    g_result = load_graph(LANG_TEST_VOC)

    upload(SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, http_client)
    g = get(SPARQL_ENDPOINT, TESTING_GRAPH, http_client=http_client)
    assert g.isomorphic(g_result)

    g2 = get(SPARQL_ENDPOINT, "http://nothing.com", http_client=http_client)
    assert g2 == 404


def test_put(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    SPARQL_ENDPOINT = f"http://localhost:{port}/ds"

    put(SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, http_client=http_client)

    r = query(
        SPARQL_ENDPOINT,
        "SELECT (COUNT(?c) AS ?count) WHERE {?c a skos:Concept}",
        namespaces={"skos": "http://www.w3.org/2004/02/skos/core#"},
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 7

    # replace that graph
    put(SPARQL_ENDPOINT, THREE_TRIPLE_FILE, TESTING_GRAPH, http_client=http_client)

    r = query(
        SPARQL_ENDPOINT,
        "SELECT (COUNT(?s) AS ?count) WHERE { GRAPH <"
        + TESTING_GRAPH
        + "> {?s ?p ?o}}",
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 3


def test_post(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    SPARQL_ENDPOINT = f"http://localhost:{port}/ds"

    post(SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, http_client=http_client)

    r = query(
        SPARQL_ENDPOINT,
        "SELECT (COUNT(?c) AS ?count) WHERE {?c a skos:Concept}",
        namespaces={"skos": "http://www.w3.org/2004/02/skos/core#"},
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 7

    # add to that graph
    post(SPARQL_ENDPOINT, THREE_TRIPLE_FILE, TESTING_GRAPH, http_client=http_client)

    r = query(
        SPARQL_ENDPOINT,
        "SELECT (COUNT(?s) AS ?count) WHERE { GRAPH <"
        + TESTING_GRAPH
        + "> {?s ?p ?o}}",
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 80


def test_delete(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    SPARQL_ENDPOINT = f"http://localhost:{port}/ds"

    put(SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, http_client=http_client)

    r = query(
        SPARQL_ENDPOINT,
        "SELECT (COUNT(?c) AS ?count) WHERE {?c a skos:Concept}",
        namespaces={"skos": "http://www.w3.org/2004/02/skos/core#"},
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 7

    delete(SPARQL_ENDPOINT, TESTING_GRAPH, http_client=http_client)

    r = query(
        SPARQL_ENDPOINT,
        "SELECT (COUNT(?s) AS ?count) WHERE { GRAPH <"
        + TESTING_GRAPH
        + "> {?s ?p ?o}}",
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 0

    assert not exists(SPARQL_ENDPOINT, TESTING_GRAPH)


def test_clear():
    pass  # alias of delete


def test_upload(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    SPARQL_ENDPOINT = f"http://localhost:{port}/ds"

    upload(SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH)

    r = query(
        SPARQL_ENDPOINT,
        "SELECT (COUNT(?s) AS ?count) WHERE { GRAPH <"
        + TESTING_GRAPH
        + "> {?s ?p ?o}}",
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 77

    upload(SPARQL_ENDPOINT, THREE_TRIPLE_FILE, TESTING_GRAPH)

    r = query(
        SPARQL_ENDPOINT,
        "SELECT (COUNT(?s) AS ?count) WHERE { GRAPH <"
        + TESTING_GRAPH
        + "> {?s ?p ?o}}",
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 3

    upload(SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, append=True)

    r = query(
        SPARQL_ENDPOINT,
        "SELECT (COUNT(?s) AS ?count) WHERE { GRAPH <"
        + TESTING_GRAPH
        + "> {?s ?p ?o}}",
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 80


@pytest.mark.skip(
    reason="Test works with normal Fuseki but not testing container version"
)
def test_upload_no_graph(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    SPARQL_ENDPOINT = f"http://localhost:{port}/ds"

    upload(SPARQL_ENDPOINT, LANG_TEST_VOC, None)

    q = """
        SELECT (COUNT(?s) AS ?c)
        WHERE {
            ?s ?p ?o
        }
        """
    r = query(SPARQL_ENDPOINT, q, return_format="python", return_bindings_only=True)

    assert r[0]["c"] == 77


def test_upload_url(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    SPARQL_ENDPOINT = f"http://localhost:{port}/ds"

    upload(
        SPARQL_ENDPOINT,
        "https://raw.githubusercontent.com/Kurrawong/kurra/refs/heads/main/tests/test_db/config.ttl",
        TESTING_GRAPH,
    )

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

    upload(SPARQL_ENDPOINT, "https://linked.data.gov.au/def/vocdermods", TESTING_GRAPH)

    r = query(SPARQL_ENDPOINT, q, return_format="python", return_bindings_only=True)

    assert r[0]["c"] == 86
