from pathlib import Path

from typer.testing import CliRunner

from kurra.cli import app

runner = CliRunner()


def test_cli_db_create(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    result = runner.invoke(
        app,
        [
            "db",
            "create",
            f"http://localhost:{port}",
            "myds",
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert f"Dataset myds created at http://localhost:{port}." in result.output


def test_cli_db_create_with_both_dataset_name_and_config_file(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    current_dir = Path(__file__).parent
    file = current_dir / "config.ttl"
    result = runner.invoke(
        app,
        [
            "db",
            "create",
            f"http://localhost:{port}",
            "myds",
            "--config",
            str(file),
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 2
    assert "Only dataset name or --config is allowed, not both." in result.output


def test_cli_db_create_with_config_file(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    current_dir = Path(__file__).parent
    file = current_dir / "config.ttl"
    result = runner.invoke(
        app,
        [
            "db",
            "create",
            f"http://localhost:{port}",
            "--config",
            str(file),
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert (
        f"Dataset myds created using assembler config at http://localhost:{port}."
        in result.output
    )


def test_cli_db_create_existing_dataset(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    dataset_name = "ds"
    result = runner.invoke(
        app,
        [
            "db",
            "create",
            f"http://localhost:{port}",
            dataset_name,
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 1
    assert (
        f"Failed to create repository {dataset_name} at http://localhost:{port}"
        in result.output
    )
