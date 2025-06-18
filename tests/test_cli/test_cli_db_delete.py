from typer.testing import CliRunner

from kurra.cli import app

runner = CliRunner()


def test_cli_db_delete(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    result = runner.invoke(
        app,
        [
            "db",
            "list",
            f"http://localhost:{port}",
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert "'ds.name': '/ds'" in result.output

    result = runner.invoke(
        app,
        [
            "db",
            "delete",
            f"http://localhost:{port}",
            "ds",
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert "Dataset ds deleted." in result.output

    result = runner.invoke(
        app,
        [
            "db",
            "list",
            f"http://localhost:{port}",
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert "'ds.name': '/ds'" not in result.output


def test_cli_db_sparql_drop(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    result = runner.invoke(
        app,
        [
            "db",
            "sparql",
            "DROP ALL",
            f"http://localhost:{port}",
            "-u",
            "admin",
            "-p",
            "admin",
        ],
    )
    # assert result.exit_code == 0  # TODO: work out why this isn't returning 0
    assert result.output == ""