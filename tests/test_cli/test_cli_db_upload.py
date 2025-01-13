from typer.testing import CliRunner

from kurra.cli import app

runner = CliRunner()


def test_cli_db_upload_file(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    result = runner.invoke(
        app,
        [
            "db",
            "upload",
            "tests/test_fuseki/minimal1.ttl",
            f"http://localhost:{port}/ds",
        ],
    )
    assert result.exit_code == 0
