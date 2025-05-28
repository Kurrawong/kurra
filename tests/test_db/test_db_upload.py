from pathlib import Path
from kurra.db import upload
from kurra.sparql import query
import pytest


def test_db_upload(fuseki_container):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"

    upload(SPARQL_ENDPOINT, Path(__file__).parent / "config.ttl", TESTING_GRAPH)

    q = """
        SELECT (COUNT(?s) AS ?c)
        WHERE {
            GRAPH ?g {
                ?s ?p ?o
            }
        }
        """
    r = query(SPARQL_ENDPOINT, q, return_python=True, return_bindings_only=True)

    assert r[0]["c"]["value"] == "142"


@pytest.mark.skip(reason="Test works with normal Fuseki but not testing container version")
def test_db_upload_no_graph(fuseki_container):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    upload(SPARQL_ENDPOINT, Path(__file__).parent / "config.ttl", None)

    q = """
        SELECT (COUNT(?s) AS ?c)
        WHERE {
            ?s ?p ?o
        }
        """
    r = query(SPARQL_ENDPOINT, q, return_python=True, return_bindings_only=True)

    print(r)

    assert r[0]["c"]["value"] == "142"