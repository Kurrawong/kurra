import httpx

from kurra.db.gsp import upload
from kurra.sparql import query


def test_query(fuseki_container, http_client):
    with httpx.Client() as client:
        sparql_endpoint = (
            f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
        )
        testing_graph = "https://example.com/testing-graph"

        data = """
                PREFIX ex: <http://example.com/>
                
                ex:a ex:b ex:c .
                ex:a2 ex:b2 ex:c2 .
                """

        upload(sparql_endpoint, data, testing_graph, False, http_client=http_client)

        q = """
            SELECT (COUNT(*) AS ?count) 
            WHERE {
              GRAPH <XXX> {
                ?s ?p ?o
              }
            }        
            """.replace("XXX", testing_graph)

        r = query(
            sparql_endpoint,
            q,
            http_client=http_client,
            return_format="python",
            return_bindings_only=True,
        )

        assert r[0]["count"] == 2

        q = "DROP GRAPH <XXX>".replace("XXX", testing_graph)

        r = query(sparql_endpoint, q, http_client=http_client)

        q = """
            SELECT (COUNT(*) AS ?count) 
            WHERE {
              GRAPH <XXX> {
                ?s ?p ?o
              }
            }        
            """.replace("XXX", testing_graph)

        r = query(
            sparql_endpoint,
            q,
            http_client=http_client,
            return_format="python",
            return_bindings_only=True,
        )

        assert r[0]["count"] == 0
