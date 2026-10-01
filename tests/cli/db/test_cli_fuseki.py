import json
import re
from datetime import datetime
from pathlib import Path
import httpx

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


def test_fuseki_ping(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    sparql_endpoint = f"http://localhost:{port}"

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "ping",
            sparql_endpoint,
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert str(datetime.now().year) in strip_ansi(result.output)


def test_fuseki_server(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    sparql_endpoint = f"http://localhost:{port}"

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "server",
            sparql_endpoint,
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert "version" in output
    assert "uptime" in output


def test_fuseki_stats(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    sparql_endpoint = f"http://localhost:{port}"

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "stats",
            sparql_endpoint,
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert "Requests" in strip_ansi(result.output)

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "stats",
            sparql_endpoint,
            "--dataset-name",
            "ds",
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    assert "Requests" in strip_ansi(result.output)


def test_fuseki_tasks(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    sparql_endpoint = f"http://localhost:{port}"

    # kurra has no function that spawns a Fuseki admin task, triggering one using the compact endpoint since it spawns a task
    httpx.Client(auth=("admin", "admin")).post(f"{sparql_endpoint}/$/compact/ds")

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "tasks",
            sparql_endpoint,
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    tasks = json.loads(strip_ansi(result.output))
    assert len(tasks) == 1
    assert tasks[0]["task"] == "Compact"

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "tasks",
            sparql_endpoint,
            "--task-name",
            "doesnotexist",
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 1
    assert "Failed to list tasks at" in strip_ansi(result.output)


def test_fuseki_metrics(fuseki_container):
    port = fuseki_container.get_exposed_port(3030)
    sparql_endpoint = f"http://localhost:{port}"

    result = runner.invoke(
        app,
        [
            "db",
            "fuseki",
            "metrics",
            sparql_endpoint,
            "--username",
            "admin",
            "--password",
            "admin",
        ],
    )
    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert "fuseki_requests" in output
    assert 'dataset="/ds"' in output


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
