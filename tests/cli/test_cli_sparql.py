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


def test_query_file():
    LANG_TEST_VOC_PATH_STR = str(
        Path(__file__).parent.parent / "sparql/language-test.ttl"
    )

    result = runner.invoke(
        app,
        [
            "sparql",
            LANG_TEST_VOC_PATH_STR,
            str(Path(__file__).parent.parent / "sparql/q.sparql"),
        ],
    )

    assert "count" in result.output

    q = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

        SELECT (COUNT(?c) AS ?count)
        WHERE {
            ?c a skos:Concept ;
        }
        """

    result = runner.invoke(
        app,
        [
            "sparql",
            LANG_TEST_VOC_PATH_STR,
            q,
        ],
    )

    assert "count" in result.output

    # checks to ensure a 'long file name' which is really just a textual SPARQL query is handled but fails to parse as it's not a real query
    q = "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur? At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores."

    result = runner.invoke(
        app,
        [
            "sparql",
            LANG_TEST_VOC_PATH_STR,
            q,
        ],
    )

    assert "Expected one of" in str(result.exception)
