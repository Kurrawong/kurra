import re
from pathlib import Path

from typer.testing import CliRunner

from kurra.cli import app

runner = CliRunner()
from click.utils import strip_ansi


def strip_ansi(text):
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


def test_fuseki_create(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    sparql_endpoint = f"http://localhost:{port}"
    dataset_name = "myds"

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "create",
            sparql_endpoint,
            dataset_name,
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert f"Dataset myds created at http://localhost:{port}." in strip_ansi(
        result.output
    )


def test_fuseki_create_with_both_dataset_name_and_config_file(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    sparql_endpoint = f"http://localhost:{port}"
    dataset_name = "myds"
    config_file = Path(__file__).parent / "config.ttl"

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "create",
            sparql_endpoint,
            dataset_name,
            "--config",
            str(config_file),
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 2
    assert "Only dataset name or --config is allowed, not both." in strip_ansi(
        result.output
    )


def test_fuseki_create_with_config_file(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    sparql_endpoint = f"http://localhost:{port}"
    dataset_name = "myds"
    config_file = Path(__file__).parent / "config.ttl"

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "create",
            sparql_endpoint,
            "--config",
            str(config_file),
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert (
        f"Dataset myds created using assembler config at http://localhost:{port}."
        in strip_ansi(result.output)
    )


def test_fuseki_create_existing_dataset(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    sparql_endpoint = f"http://localhost:{port}"
    dataset_name = "ds"

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "create",
            sparql_endpoint,
            dataset_name,
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 1
    assert (
        f"Failed to create dataset {dataset_name} at {sparql_endpoint}"
        in strip_ansi(result.output)
    )


def test_fuseki_delete(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    sparql_endpoint = f"http://localhost:{port}"
    dataset_name = "ds"

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "describe",
            sparql_endpoint,
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert "'ds.name': '/ds'" in strip_ansi(result.output)

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "delete",
            sparql_endpoint,
            dataset_name,
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert "Dataset ds deleted." in strip_ansi(result.output)

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "describe",
            sparql_endpoint,
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert "'ds.name': '/ds'" not in strip_ansi(result.output)


def test_fuseki_describe(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "describe",
            f"http://localhost:{port}",
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert "'ds.name': '/ds'" in strip_ansi(result.output)
