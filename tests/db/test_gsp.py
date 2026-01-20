from pathlib import Path

import pytest
import rdflib
from typer.testing import CliRunner

from kurra.db.gsp import clear, delete, exists, get, post, put, upload
from kurra.sparql import query
from kurra.utils import load_graph

runner = CliRunner()

TESTS_DIR = Path(__file__).resolve().parent
LANG_TEST_VOC = Path(__file__).parent.parent / "sparql" / "language-test.ttl"
THREE_TRIPLE_FILE = Path(__file__).parent.parent / "file" / "prefixes-test.ttl"
TESTING_GRAPH = "https://example.com/testing-graph"


def test_exists(fuseki_container, http_client):
    sparql_endpoint = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    g1 = exists(sparql_endpoint, "http://nothing.com", http_client)
    assert not g1

    upload(sparql_endpoint, LANG_TEST_VOC, TESTING_GRAPH, http_client)
    g2 = exists(sparql_endpoint, TESTING_GRAPH, http_client)
    assert g2

    delete(sparql_endpoint, TESTING_GRAPH, http_client)
    g3 = exists(sparql_endpoint, TESTING_GRAPH, http_client)
    assert not g3


def test_get(fuseki_container, http_client):
    sparql_endpoint = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    g_result = load_graph(LANG_TEST_VOC)

    upload(sparql_endpoint, LANG_TEST_VOC, TESTING_GRAPH, http_client)
    g = get(sparql_endpoint, TESTING_GRAPH, http_client=http_client)
    assert g.isomorphic(g_result)
    assert str(g.identifier) == TESTING_GRAPH

    d = """
        PREFIX : <http://example.com/>
        
        :a 
            :b :c ;
            :d :e ;
        .
        """
    upload(sparql_endpoint, d, None, http_client)

    g2 = get(sparql_endpoint, "default", http_client=http_client)
    assert len(g2) == 2
    assert isinstance(g2.identifier, rdflib.BNode)

    g3 = get(sparql_endpoint, "http://nothing.com", http_client=http_client)
    assert g3 == 404

    g4 = get(
        sparql_endpoint, "default", http_client=http_client, return_format="original"
    )
    assert "http://example.com/" in g4


def test_put(fuseki_container, http_client):
    sparql_endpoint = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    put(sparql_endpoint, LANG_TEST_VOC, TESTING_GRAPH, http_client=http_client)

    r = query(
        sparql_endpoint,
        "SELECT (COUNT(?c) AS ?count) WHERE {?c a skos:Concept}",
        namespaces={"skos": "http://www.w3.org/2004/02/skos/core#"},
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 7

    # replace that graph
    put(sparql_endpoint, THREE_TRIPLE_FILE, TESTING_GRAPH, http_client=http_client)

    r = query(
        sparql_endpoint,
        "SELECT (COUNT(?s) AS ?count) WHERE { GRAPH <"
        + TESTING_GRAPH
        + "> {?s ?p ?o}}",
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 3


def test_post(fuseki_container, http_client):
    sparql_endpoint = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    post(sparql_endpoint, LANG_TEST_VOC, TESTING_GRAPH, http_client=http_client)

    r = query(
        sparql_endpoint,
        "SELECT (COUNT(?c) AS ?count) WHERE {?c a skos:Concept}",
        namespaces={"skos": "http://www.w3.org/2004/02/skos/core#"},
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 7

    # add to that graph
    post(sparql_endpoint, THREE_TRIPLE_FILE, TESTING_GRAPH, http_client=http_client)

    r = query(
        sparql_endpoint,
        "SELECT (COUNT(?s) AS ?count) WHERE { GRAPH <"
        + TESTING_GRAPH
        + "> {?s ?p ?o}}",
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 80


def test_delete(fuseki_container, http_client):
    sparql_endpoint = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    put(sparql_endpoint, LANG_TEST_VOC, TESTING_GRAPH, http_client=http_client)

    r = query(
        sparql_endpoint,
        "SELECT (COUNT(?c) AS ?count) WHERE {?c a skos:Concept}",
        namespaces={"skos": "http://www.w3.org/2004/02/skos/core#"},
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 7

    delete(sparql_endpoint, TESTING_GRAPH, http_client=http_client)

    r = query(
        sparql_endpoint,
        "SELECT (COUNT(?s) AS ?count) WHERE { GRAPH <"
        + TESTING_GRAPH
        + "> {?s ?p ?o}}",
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 0

    assert not exists(sparql_endpoint, TESTING_GRAPH)


def test_clear():
    pass  # alias of delete


def test_upload(fuseki_container, http_client):
    sparql_endpoint = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    upload(sparql_endpoint, LANG_TEST_VOC, TESTING_GRAPH)

    r = query(
        sparql_endpoint,
        "SELECT (COUNT(?s) AS ?count) WHERE { GRAPH <"
        + TESTING_GRAPH
        + "> {?s ?p ?o}}",
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 77

    upload(sparql_endpoint, THREE_TRIPLE_FILE, TESTING_GRAPH)

    r = query(
        sparql_endpoint,
        "SELECT (COUNT(?s) AS ?count) WHERE { GRAPH <"
        + TESTING_GRAPH
        + "> {?s ?p ?o}}",
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )
    assert r[0]["count"] == 3

    upload(sparql_endpoint, LANG_TEST_VOC, TESTING_GRAPH, append=True)

    r = query(
        sparql_endpoint,
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
def test_upload_no_graph(fuseki_container, http_client):
    sparql_endpoint = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    q = """
        SELECT (COUNT(?s) AS ?c)
        WHERE {
        GRAPH ?g {
                ?s ?p ?o
            }
        }
        """
    r = query(
        sparql_endpoint,
        q,
        return_format="python",
        return_bindings_only=True,
        http_client=http_client,
    )

    assert r[0]["c"] == 77


def test_upload_url(fuseki_container, http_client):
    sparql_endpoint = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    upload(
        sparql_endpoint,
        "https://raw.githubusercontent.com/Kurrawong/kurra/refs/heads/main/tests/db/config.ttl",
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
    r = query(sparql_endpoint, q, return_format="python", return_bindings_only=True)

    assert r[0]["c"] == 142

    # now test one with Content Negotiation and a redirect
    clear(sparql_endpoint, TESTING_GRAPH, http_client)

    upload(sparql_endpoint, "https://linked.data.gov.au/def/vocdermods", TESTING_GRAPH)

    r = query(sparql_endpoint, q, return_format="python", return_bindings_only=True)

    assert r[0]["c"] == 86
