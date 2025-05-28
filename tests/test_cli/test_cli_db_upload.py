from typer.testing import CliRunner

from kurra.cli import app
from kurra.sparql import query

runner = CliRunner()


def test_cli_db_upload_file(fuseki_container):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"

    result = runner.invoke(
        app,
        [
            "db",
            "upload",
            "tests/test_fuseki/minimal1.ttl",
            SPARQL_ENDPOINT,
        ],
    )
    assert result.exit_code == 0

    q = """
        SELECT (COUNT(?s) AS ?c)
        WHERE {
            GRAPH ?g {
                ?s ?p ?o
            }
        }
        """
    r = query(SPARQL_ENDPOINT, q)
    print(r)



def test_cli_db_upload_file_with_graph_id(fuseki_container):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "https://example.com/testing-graph"

    result = runner.invoke(
        app,
        [
            "db",
            "upload",
            "tests/test_fuseki/minimal1.ttl",
            "-g",
            TESTING_GRAPH,
            SPARQL_ENDPOINT,
        ],
    )
    assert result.exit_code == 0

    q = """
        SELECT (COUNT(?s) AS ?c)
        WHERE {
            ?s ?p ?o
        }
        """
    r = query(SPARQL_ENDPOINT, q)
    print(r)


def test_cli_db_upload_file_with_graph_id_file(fuseki_container):
    SPARQL_ENDPOINT = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    TESTING_GRAPH = "file"

    result = runner.invoke(
        app,
        [
            "db",
            "upload",
            "tests/test_fuseki/minimal1.ttl",
            "-g",
            TESTING_GRAPH,
            SPARQL_ENDPOINT,
        ],
    )
    assert result.exit_code == 0

    q = """
        SELECT (COUNT(?s) AS ?c)
        WHERE {
            ?s ?p ?o
        }
        """
    r = query(SPARQL_ENDPOINT, q)
    print(r)

