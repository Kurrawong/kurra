import httpx

from kurra.db.sparql import query


def test_query(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    with httpx.Client() as client:
        SPARQL_ENDPOINT = f"http://localhost:{port}/ds"
        TESTING_GRAPH = "https://example.com/testing-graph"

        data = """
                PREFIX ex: <http://example.com/>
                
                ex:a ex:b ex:c .
                ex:a2 ex:b2 ex:c2 .
                """

        upload(SPARQL_ENDPOINT, data, TESTING_GRAPH, False, client)

        q = """
            SELECT (COUNT(*) AS ?count) 
            WHERE {
              GRAPH <XXX> {
                ?s ?p ?o
              }
            }        
            """.replace("XXX", TESTING_GRAPH)

        r = query(
            SPARQL_ENDPOINT,
            q,
            client,
            return_format="python",
            return_bindings_only=True,
        )

        assert r[0]["count"] == 2

        q = "DROP GRAPH <XXX>".replace("XXX", TESTING_GRAPH)

        r = query(SPARQL_ENDPOINT, q, client)

        print(r)
