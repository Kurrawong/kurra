import datetime
import json
from pathlib import Path

import httpx
import pytest
from rdflib.namespace import SKOS

from kurra.db.gsp import clear, upload
from kurra.sparql import query
from kurra.utils import RenderFormat, render_sparql_result

LANG_TEST_VOC = Path(__file__).parent / "language-test.ttl"
TESTING_GRAPH = "https://example.com/testing-graph"


def test_query_db(fuseki_container, http_client):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    # SPARQL_ENDPOINT = "http://localhost:3030/test"
    TESTING_GRAPH = "https://example.com/testing-graph"
    upload(
        SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, False, http_client=http_client
    )

    q = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#> 
        SELECT * 
        WHERE { 
            GRAPH ?g {
                ?c a skos:Concept .
            } 
        }"""

    assert "--- | ---" in render_sparql_result(
        query(SPARQL_ENDPOINT, q, http_client=http_client, return_format="python")
    )

    assert (
        "c"
        in json.loads(
            (
                render_sparql_result(
                    query(
                        SPARQL_ENDPOINT,
                        q,
                        http_client=http_client,
                        return_format="python",
                    ),
                    RenderFormat.json,
                )
            )
        )["head"]["vars"]
    )

    # test return format options

    q = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#> 
        SELECT *
        WHERE {
            GRAPH ?g {
                ?c a skos:Concept ;
                    skos:prefLabel "English only"@en ;
                .
            }
        }"""
    r = query(
        SPARQL_ENDPOINT,
        q,
        http_client=http_client,
        return_format="python",
        return_bindings_only=True,
    )
    assert r[0]["c"] == "https://example.com/demo-vocabs/language-test/en-only"

    r = query(
        SPARQL_ENDPOINT,
        q,
        http_client=http_client,
        return_format="python",
        return_bindings_only=False,
    )
    assert (
        r["results"]["bindings"][0]["c"]
        == "https://example.com/demo-vocabs/language-test/en-only"
    )

    r = query(SPARQL_ENDPOINT, q, http_client=http_client)
    r2 = json.loads(r)
    assert (
        r2["results"]["bindings"][0]["c"]["value"]
        == "https://example.com/demo-vocabs/language-test/en-only"
    )

    r = query(
        SPARQL_ENDPOINT,
        q,
        http_client=http_client,
        return_format="original",
        return_bindings_only=True,
    )
    # return_bindings_only=True is ignored since return format is not "python"
    assert isinstance(r, str)
    r2 = json.loads(r)
    assert (
        r2["results"]["bindings"][0]["c"]["value"]
        == "https://example.com/demo-vocabs/language-test/en-only"
    )

    q = "ASK {?s ?p ?o}"
    r = query(SPARQL_ENDPOINT, q, http_client=http_client)  # original, False
    assert '"boolean"' in r

    q = "ASK { GRAPH ?g { ?s ?p ?o} }"
    r = query(SPARQL_ENDPOINT, q, http_client=http_client, return_format="python")
    assert r["boolean"]

    q = "ASK { GRAPH ?g { ?s ?p ?o} }"
    r = query(
        SPARQL_ENDPOINT,
        q,
        http_client=http_client,
        return_format="python",
        return_bindings_only=True,
    )
    assert r

    q = "ASK {?s ?p ?o}"
    # return_bindings_only=True is ignored since return format is not "python"
    r = query(SPARQL_ENDPOINT, q, http_client=http_client, return_bindings_only=True)
    assert '"boolean"' in r

    q = "ASK {?s ?p <http://nothing.com/x>}"
    r = query(
        SPARQL_ENDPOINT,
        q,
        http_client=http_client,
        return_format="python",
        return_bindings_only=True,
    )
    assert not r


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

    assert "--- | --- | ---" in render_sparql_result(
        query(LANG_TEST_VOC, q, return_format="python")
    )

    r = query(LANG_TEST_VOC, q)
    assert (
        "pl" in json.loads(render_sparql_result(r, RenderFormat.json))["head"]["vars"]
    )

    # test return format options

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

    r = query(LANG_TEST_VOC, q, return_format="python", return_bindings_only=True)
    assert r[0]["c"] == "https://example.com/demo-vocabs/language-test/en-only"

    r = query(LANG_TEST_VOC, q, return_format="python", return_bindings_only=False)
    assert (
        r["results"]["bindings"][0]["c"]
        == "https://example.com/demo-vocabs/language-test/en-only"
    )

    r = query(LANG_TEST_VOC, q, return_format="original", return_bindings_only=False)
    assert isinstance(r, str)
    r2 = json.loads(r)
    assert (
        r2["results"]["bindings"][0]["c"]["value"]
        == "https://example.com/demo-vocabs/language-test/en-only"
    )

    r = query(LANG_TEST_VOC, q, return_format="original", return_bindings_only=True)
    # ignore the return_bindings_only=True bit as return_format != "python"
    assert isinstance(r, str)
    r2 = json.loads(r)
    assert (
        r2["results"]["bindings"][0]["c"]["value"]
        == "https://example.com/demo-vocabs/language-test/en-only"
    )

    q = "ASK {?s ?p ?o}"
    r = query(LANG_TEST_VOC, q)  # False, False
    assert r == '{"head": {}, "boolean": true}'

    q = "ASK {?s ?p ?o}"
    r = query(LANG_TEST_VOC, q, return_format="python")
    assert r["boolean"]

    q = "ASK {?s ?p ?o}"
    r = query(LANG_TEST_VOC, q, return_format="python", return_bindings_only=True)
    assert r

    q = "ASK {?s ?p ?o}"
    r = json.loads(query(LANG_TEST_VOC, q, return_bindings_only=True))
    # ignore the return_bindings_only=True bit as return_format != "python"
    assert r["boolean"]

    q = "ASK {?s ?p <http://nothing.com/x>}"
    r = query(LANG_TEST_VOC, q, return_format="python", return_bindings_only=True)
    assert not r


def test_duplicates():
    rdf_data = """
    PREFIX people: <https://linked.data.gov.au/dataset/people/>
    PREFIX schema: <https://schema.org/>

    people:nick
        a
            schema:Person , 
            schema:Patient ;
        schema:name "Nick" ;
        schema:age 42 ;
        schema:parent people:george ;
    .

    people:george
        a schema:Person ; 
        schema:name "George" ;
        schema:age 70 ;    
    .
    """

    q = """
    PREFIX people: <https://linked.data.gov.au/dataset/people/>
    PREFIX schema: <https://schema.org/>

    SELECT ?p ?name
    WHERE {
        ?p 
            a schema:Person ;
            schema:name ?name ;
            schema:age ?age ;
        .

        FILTER (?age < 50)
    }
    """
    r = query(rdf_data, q, return_format="python", return_bindings_only=True)
    assert len(r) == 1


def test_auth(fuseki_container, http_client):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    # SPARQL_ENDPOINT = "http://localhost:3030/test"

    upload(
        SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, False, http_client=http_client
    )

    x = httpx.get(
        SPARQL_ENDPOINT, params={"query": "ASK { ?s ?p ?o}"}, auth=("admin", "admin")
    )

    q = "ASK {?s ?p ?o}"
    r = query(
        SPARQL_ENDPOINT,
        q,
        http_client=http_client,
        return_format="python",
        return_bindings_only=True,
    )
    assert r

    with pytest.raises(RuntimeError):
        query(
            SPARQL_ENDPOINT,
            q,
            None,
            None,
            return_format="python",
            return_bindings_only=True,
        )


def test_construct(fuseki_container, http_client):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    upload(
        SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, False, http_client=http_client
    )

    q = """
        CONSTRUCT { ?s ?p ?o }
        WHERE {
            GRAPH ?g {
                ?s ?p ?o
            }
        }
        LIMIT 3       
        """

    r = query(SPARQL_ENDPOINT, q, http_client=http_client, return_format="python")
    assert len(r) == 3


def test_insert(fuseki_container, http_client):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    upload(
        SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, False, http_client=http_client
    )

    q = """
        INSERT { 
            GRAPH <http://other> {
                ?s ?p ?o 
            }
        }
        WHERE {
            GRAPH ?g {
                ?s ?p ?o
            }
        }
        """

    r = query(SPARQL_ENDPOINT, q, http_client=http_client)
    assert r == ""

    q = """
        SELECT *
        WHERE {
            GRAPH <http://other> {
                ?cs a skos:ConceptScheme ;
            }            
        }
        """
    r = query(
        SPARQL_ENDPOINT,
        q,
        namespaces={"skos": SKOS},
        http_client=http_client,
        return_format="python",
        return_bindings_only=True,
    )
    assert r[0]["cs"] == "https://example.com/demo-vocabs/language-test"


def test_204_response(fuseki_container, http_client):
    # DROP data from SPARQL Endpoint
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    upload(
        SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, False, http_client=http_client
    )
    r = query(
        SPARQL_ENDPOINT,
        "DROP ALL",
        http_client=http_client,
        return_format="python",
        return_bindings_only=True,
    )
    assert r == ""

    # DROP data from a file
    with pytest.raises(NotImplementedError):
        query(
            Path(__file__).parent / "vocab.nq",
            "DROP ALL",
            return_format="python",
            return_bindings_only=True,
        )

    # DROP no data
    clear(SPARQL_ENDPOINT, "all", http_client)
    r = query(
        SPARQL_ENDPOINT,
        "DROP ALL",
        http_client=http_client,
        return_format="python",
        return_bindings_only=True,
    )
    assert r == ""


def test_describe(fuseki_container, http_client):
    # DROP data from SPARQL Endpoint
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    query(SPARQL_ENDPOINT, "DROP ALL", http_client=http_client)
    upload(
        SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, False, http_client=http_client
    )

    g = query(
        SPARQL_ENDPOINT,
        "DESCRIBE <https://example.com/demo-vocabs/language-test>",
        http_client=http_client,
        return_format="python",
    )
    assert len(g) == 16


def test_return_formats(fuseki_container, http_client):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    query(SPARQL_ENDPOINT, "DROP ALL", http_client=http_client)
    upload(
        SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, False, http_client=http_client
    )

    with pytest.raises(
        ValueError,
        match="must be either 'original', 'python' or 'dataframe'",
    ):
        g = query(
            SPARQL_ENDPOINT,
            "DESCRIBE <https://example.com/demo-vocabs/language-test>",
            http_client=http_client,
            return_format="json",
        )

    with pytest.raises(
        ValueError,
        match='Only SELECT and ASK queries can have return_format set to "dataframe"',
    ):
        g = query(
            SPARQL_ENDPOINT,
            "DESCRIBE <https://example.com/demo-vocabs/language-test>",
            http_client=http_client,
            return_format="dataframe",
        )

    q = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        
        SELECT *
        WHERE {
            ?c
                a skos:Concept ;
                skos:prefLabel ?pl ;
            .
        
            OPTIONAL {
                ?c skos:altLabel ?al
            }
        }
        ORDER BY ?pl
        """
    r = query(SPARQL_ENDPOINT, q, http_client=http_client, return_format="dataframe")

    from pandas import DataFrame

    assert type(r) == DataFrame
    assert r["pl"][0] == "English prefLabel"

    r = query(Path(__file__).parent / "language-test.ttl", q, return_format="dataframe")
    assert type(r) == DataFrame
    assert isinstance(r["pl"][0], str)
    assert r["pl"][0] == "English prefLabel"

    q = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

        SELECT (COUNT(?c) AS ?count) 
        WHERE {
            ?c a skos:Concept
        }
        ORDER BY ?c
        """
    r = query(SPARQL_ENDPOINT, q, http_client=http_client, return_format="dataframe")
    assert r["count"][0] == 7

    r = query(Path(__file__).parent / "language-test.ttl", q, return_format="dataframe")
    assert r["count"][0] == 7

    q = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

        ASK 
        WHERE {
            <https://example.com/demo-vocabs/language-test> a skos:ConceptScheme .
        }
        """
    r = query(SPARQL_ENDPOINT, q, http_client=http_client, return_format="dataframe")
    assert r["boolean"][0]

    r = query(Path(__file__).parent / "language-test.ttl", q, return_format="dataframe")
    assert r["boolean"][0]


def test_deep_python_db(fuseki_container, http_client):
    """Ensures that 'deep python' is returned from DB queries

    Tests the "deep" conversion of SPARQL types to Python types at kurra.db.sparql() Line 96"""
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    query(SPARQL_ENDPOINT, "DROP ALL", http_client=http_client)
    upload(
        SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, False, http_client=http_client
    )

    q = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

        SELECT (COUNT(?c) AS ?count) 
        WHERE {
            ?c 
                a skos:Concept .
        }
        ORDER BY ?pl
        """
    r = query(
        SPARQL_ENDPOINT,
        q,
        http_client=http_client,
        return_format="python",
        return_bindings_only=False,
    )
    assert r["results"]["bindings"][0]["count"] == 7

    q = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX schema: <https://schema.org/>

        SELECT *
        WHERE {
            ?c 
                a skos:ConceptScheme ;
                schema:dateCreated ?dc ;
            . 
        }
        ORDER BY ?pl
        """
    r = query(
        SPARQL_ENDPOINT,
        q,
        http_client=http_client,
        return_format="python",
        return_bindings_only=False,
    )
    assert isinstance(r["results"]["bindings"][0]["dc"], datetime.date)


def test_deep_python_file():
    """Ensures that 'deep python' is returned from file queries"""
    q = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

        SELECT (COUNT(?c) AS ?count) 
        WHERE {
            ?c 
                a skos:Concept .
        }
        ORDER BY ?pl
        """
    r = query(LANG_TEST_VOC, q, return_format="python", return_bindings_only=True)
    assert r[0]["count"] == 7

    q = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX schema: <https://schema.org/>

        SELECT *
        WHERE {
            ?c 
                a skos:ConceptScheme ;
                schema:dateCreated ?dc ;
            . 
        }
        ORDER BY ?pl
        """
    r = query(LANG_TEST_VOC, q, return_format="python")
    assert isinstance(r["results"]["bindings"][0]["dc"], datetime.date)

    d = """
        PREFIX ex: <https://exammple.org/>
        PREFIX schema: <https://schema.org/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        
        ex:a schema:dateIssued "2025-12-11" .  # str
        
        ex:b schema:dateIssued "2025-12-11T14:30:20" .  # str
        
        ex:c schema:dateIssued "2025-12-11"^^xsd:date .  # date
        
        ex:d schema:dateIssued "2025-12-11T14:30:20"^^xsd:dateTime .  # datetime
        """

    q = """
        PREFIX ex: <https://exammple.org/>
        PREFIX schema: <https://schema.org/>

        SELECT *
        WHERE {
            ex:a schema:dateIssued ?di ;
            . 
        }
        """
    r = query(d, q, return_format="python")
    assert isinstance(r["results"]["bindings"][0]["di"], str)

    q = """
        PREFIX ex: <https://exammple.org/>
        PREFIX schema: <https://schema.org/>

        SELECT *
        WHERE {
            ex:b schema:dateIssued ?di ;
            . 
        }
        """
    r = query(d, q, return_format="python")
    assert isinstance(r["results"]["bindings"][0]["di"], str)

    q = """
        PREFIX ex: <https://exammple.org/>
        PREFIX schema: <https://schema.org/>

        SELECT *
        WHERE {
            ex:c schema:dateIssued ?di ;
            . 
        }
        """
    r = query(d, q, return_format="python")
    assert isinstance(r["results"]["bindings"][0]["di"], datetime.date)

    q = """
        PREFIX ex: <https://exammple.org/>
        PREFIX schema: <https://schema.org/>

        SELECT *
        WHERE {
            ex:d schema:dateIssued ?di ;
            . 
        }
        """
    r = query(d, q, return_format="python")
    assert isinstance(r["results"]["bindings"][0]["di"], datetime.datetime)
