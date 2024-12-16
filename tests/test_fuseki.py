from kurrawong.fuseki import query, upload
from pathlib import Path
import httpx


def test_file_upload_ng_replacement():
    with httpx.Client() as client:
        SPARQL_ENDPOINT = "http://localhost:3030/mani"
        minimalist_rdf = Path(__file__).parent / "minimal3.ttl"

        upload(
            SPARQL_ENDPOINT,
            minimalist_rdf,
            "https://example.com/demo-vocabs/language-test",
            False,
            client
        )

def test_query():
    with httpx.Client() as client:
        SPARQL_ENDPOINT = "http://localhost:3030/mani"
        TESTING_GRAPH = "https://example.com/testing-graph"

        data =  """
                PREFIX ex: <http://example.com/>
                
                ex:a ex:b ex:c .
                ex:a2 ex:b2 ex:c2 .
                """

        upload(
            SPARQL_ENDPOINT,
            data,
            TESTING_GRAPH,
            False,
            client
        )

        q = """
            SELECT (COUNT(*) AS ?count) 
            WHERE {
              GRAPH <XXX> {
                ?s ?p ?o
              }
            }        
            """.replace("XXX", TESTING_GRAPH)

        r = query(SPARQL_ENDPOINT, q, client, return_python=True, return_bindings_only=True)

        count = int(r[0]["count"]["value"])

        assert count == 2

        q = "DROP GRAPH <XXX>".replace("XXX", TESTING_GRAPH)

        print("QUERY")
        print(q)
        print("QUERY")

        r = query(SPARQL_ENDPOINT, q, client)

        print(r)

