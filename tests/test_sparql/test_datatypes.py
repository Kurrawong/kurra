import json
from pathlib import Path

import pytest
from rdflib import Literal

from kurra.db import upload, clear_graph
from kurra.sparql import query
from kurra.utils import RenderFormat, render_sparql_result, cast_sparql_literal_to_python

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

    r = query(SPARQL_ENDPOINT, q, http_client)
    print(r)
    from rdflib.plugins.sparql.parser import parseQuery
    print(parseQuery(r))

    # print(r[0]["cd"]["value"])
    # print(cast_sparql_literal_to_python(r[0]["cd"]["value"], r[0]["cd"]["datatype"]))
    # print(type(Literal(r[0]["cd"]["value"], datatype=r[0]["cd"]["datatype"]).toPython()))