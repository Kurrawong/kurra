import json
from pathlib import Path

import httpx

from kurra.db import upload
from kurra.sparql import query
from kurra.utils import RenderFormat, render_sparql_result

LANG_TEST_VOC = Path(__file__).parent / "language-test.ttl"


def test_query_db(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    with httpx.Client() as client:
        SPARQL_ENDPOINT = f"http://localhost:{port}/ds"
        TESTING_GRAPH = "https://example.com/testing-graph"
        upload(SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, False, client)

        q = """
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#> 
            SELECT * 
            WHERE { 
                GRAPH ?g {
                    ?c a skos:Concept .
                } 
            }"""

        assert "--- | ---" in render_sparql_result(query(SPARQL_ENDPOINT, q))

        assert (
            "c"
            in json.loads((render_sparql_result(query(SPARQL_ENDPOINT, q), RenderFormat.json)))["head"]["vars"]
        )

        q = "ASK {?s ?p ?o}"
        assert render_sparql_result(query(LANG_TEST_VOC, q)) == "True"


def test_query_file():
    q = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#> 
        SELECT * 
        WHERE {
            ?c a skos:Concept ;
                skos:prefLabel ?pl ;
            .
            
            OPTIONAL {
                ?c skos:altLabel ?al .
            }
        }
        LIMIT 3"""

    assert "--- | --- | ---" in render_sparql_result(query(LANG_TEST_VOC, q))

    assert (
        "pl"
        in json.loads(render_sparql_result(query(LANG_TEST_VOC, q), RenderFormat.json))["head"]["vars"]
    )

    q = "ASK {?s ?p ?o}"
    assert render_sparql_result(query(LANG_TEST_VOC, q)) == "True"
