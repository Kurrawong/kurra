from typer.testing import CliRunner

from kurra.cli import app

runner = CliRunner()


def test_cli_db_list(fuseki_container):
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
