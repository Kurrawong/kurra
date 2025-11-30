import json
from pathlib import Path

import pytest

from kurra.db import upload, clear_graph
from kurra.sparql import query
from kurra.utils import RenderFormat, render_sparql_result

LANG_TEST_VOC = Path(__file__).parent / "language-test.ttl"
TESTING_GRAPH = "https://example.com/testing-graph"


def test_date(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)

    SPARQL_ENDPOINT = f"http://localhost:{port}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"
    upload(SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, False, http_client)

    q = """
        PREFIX schema: <https://schema.org/>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#> 
        
        SELECT ?cs ?cd
        WHERE { 
            GRAPH ?g {
                ?cs 
                    a skos:ConceptScheme ;
                    schema:dateCreated ?cd ;
                .
            } 
        }"""

    r = query(SPARQL_ENDPOINT, q, http_client, "python")
    print(r)