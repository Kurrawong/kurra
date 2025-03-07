from pathlib import Path
from textwrap import dedent

import httpx
from typer.testing import CliRunner

from kurra.cli import app
from kurra.db import upload

runner = CliRunner()


LANG_TEST_VOC = (
    Path(__file__).parent.parent.resolve() / "test_sparql" / "language-test.ttl"
)


def test_query_db(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    SPARQL_ENDPOINT = f"http://localhost:{port}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"

    with httpx.Client() as client:
        upload(SPARQL_ENDPOINT, LANG_TEST_VOC, TESTING_GRAPH, False, client)

    q = dedent("""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#> 
        SELECT * 
        WHERE { 
            GRAPH ?g {
                ?c a skos:Concept .
            } 
        }""").replace("\n", "")

    result = runner.invoke(
        app,
        [
            "sparql",
            SPARQL_ENDPOINT,
            q,
        ],
    )
    print("BEFORE")
    print(result)
    print("AFTER")
    # assert result.exit_code == 0


def test_query_file():
    # TODO: work out why this test fails but the direct call works
    # direct call:
    # kurra sparql /Users/nick/work/kurrawong/kurra/tests/test_sparql/language-test.ttl "PREFIX skos: <http://www.w3.org/2004/02/skos/core#> SELECT * WHERE {     ?c a skos:Concept .}"
    q = dedent("""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#> 
        SELECT * 
        WHERE { 
            ?c a skos:Concept .
        }""").replace("\n", "")

    result = runner.invoke(
        app,
        ["sparql", LANG_TEST_VOC, q],
    )
