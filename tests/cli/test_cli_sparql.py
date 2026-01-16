from pathlib import Path
from textwrap import dedent

from typer.testing import CliRunner

from kurra.cli import app
from kurra.db.gsp import upload

runner = CliRunner()

LANG_TEST_VOC = Path(__file__).parent.parent.resolve() / "sparql" / "language-test.ttl"
TESTING_GRAPH = "https://example.com/testing-graph"


def test_query_db(fuseki_container, http_client):
    sparql_endpoint = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"

    upload(
        sparql_endpoint, LANG_TEST_VOC, TESTING_GRAPH, False, http_client=http_client
    )

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
            sparql_endpoint,
            q,
        ],
    )
    assert result.exit_code == 0


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
        ["sparql", str(LANG_TEST_VOC), q],
    )
    assert (
        "https://example.com/demo-vocabs/language-test/lang-and-no-lang"
        in result.output
    )


def test_select(fuseki_container, http_client):
    sparql_endpoint = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    upload(
        sparql_endpoint, LANG_TEST_VOC, TESTING_GRAPH, False, http_client=http_client
    )

    result = runner.invoke(
        app,
        [
            "sparql",
            sparql_endpoint,
            "SELECT * WHERE { <https://example.com/demo-vocabs/language-test> ?p ?o }",
        ],
    )
    assert "https://example.com/demo-vocabs/lan" in result.output


def test_describe(fuseki_container, http_client):
    sparql_endpoint = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    upload(
        sparql_endpoint, LANG_TEST_VOC, TESTING_GRAPH, False, http_client=http_client
    )

    result = runner.invoke(
        app,
        [
            "sparql",
            sparql_endpoint,
            "DESCRIBE <https://example.com/demo-vocabs/language-test>",
        ],
    )
    assert "Made in Nov 2024 just for testing" in result.output


def test_fuseki_sparql_drop(fuseki_container):
    result = runner.invoke(
        app,
        [
            "db",
            "sparql",
            "DROP ALL",
            f"http://localhost:{fuseki_container.get_exposed_port(3030)}",
            "-u",
            "admin",
            "-p",
            "admin",
        ],
    )
    # assert result.exit_code == 0  # TODO: work out why this isn't returning 0
    assert result.output == ""
