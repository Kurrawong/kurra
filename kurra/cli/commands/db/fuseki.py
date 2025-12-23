from pathlib import Path
from typing import Annotated

import httpx
import typer

from kurra.cli.console import console
from kurra.db.fuseki import FusekiError, create, delete, describe

app = typer.Typer(help="Fuseki database commands")

dataset_type_options = ["mem", "tdb", "tdb1", "tdb2"]


@app.command(name="ping", help="Check if the server is alive")
def describe_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    username: Annotated[
        str, typer.Option("--username", "-u", help="Fuseki username.")
    ] = None,
    password: Annotated[
        str, typer.Option("--password", "-p", help="Fuseki password.")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Timeout per request")
    ] = 60,
) -> None:
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as http_client:
        try:
            console.print(describe(fuseki_url, http_client=http_client))
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to describe datasets at {fuseki_url}."
            )
            raise err


@app.command(name="server", help="Get basic server info")
def describe_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    username: Annotated[
        str, typer.Option("--username", "-u", help="Fuseki username.")
    ] = None,
    password: Annotated[
        str, typer.Option("--password", "-p", help="Fuseki password.")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Timeout per request")
    ] = 60,
) -> None:
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as http_client:
        try:
            console.print(describe(fuseki_url, http_client=http_client))
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to describe datasets at {fuseki_url}."
            )
            raise err


@app.command(name="stats", help="Request statistics for all datasets")
def describe_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    username: Annotated[
        str, typer.Option("--username", "-u", help="Fuseki username.")
    ] = None,
    password: Annotated[
        str, typer.Option("--password", "-p", help="Fuseki password.")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Timeout per request")
    ] = 60,
) -> None:
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as http_client:
        try:
            console.print(describe(fuseki_url, http_client=http_client))
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to describe datasets at {fuseki_url}."
            )
            raise err


@app.command(name="backup", help="Ask the server to create a backup")
def describe_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    username: Annotated[
        str, typer.Option("--username", "-u", help="Fuseki username.")
    ] = None,
    password: Annotated[
        str, typer.Option("--password", "-p", help="Fuseki password.")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Timeout per request")
    ] = 60,
) -> None:
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as http_client:
        try:
            console.print(describe(fuseki_url, http_client=http_client))
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to describe datasets at {fuseki_url}."
            )
            raise err


@app.command(name="backups_list", help="List all existing backups")
def describe_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    username: Annotated[
        str, typer.Option("--username", "-u", help="Fuseki username.")
    ] = None,
    password: Annotated[
        str, typer.Option("--password", "-p", help="Fuseki password.")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Timeout per request")
    ] = 60,
) -> None:
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as http_client:
        try:
            console.print(describe(fuseki_url, http_client=http_client))
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to describe datasets at {fuseki_url}."
            )
            raise err


@app.command(name="sleep", help="Tell the server to sleep")
def describe_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    username: Annotated[
        str, typer.Option("--username", "-u", help="Fuseki username.")
    ] = None,
    password: Annotated[
        str, typer.Option("--password", "-p", help="Fuseki password.")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Timeout per request")
    ] = 60,
) -> None:
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as http_client:
        try:
            console.print(describe(fuseki_url, http_client=http_client))
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to describe datasets at {fuseki_url}."
            )
            raise err


@app.command(name="tasks", help="List running tasks")
def describe_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    username: Annotated[
        str, typer.Option("--username", "-u", help="Fuseki username.")
    ] = None,
    password: Annotated[
        str, typer.Option("--password", "-p", help="Fuseki password.")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Timeout per request")
    ] = 60,
) -> None:
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as http_client:
        try:
            console.print(describe(fuseki_url, http_client=http_client))
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to describe datasets at {fuseki_url}."
            )
            raise err


@app.command(name="metrics", help="Get server metrics")
def describe_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    username: Annotated[
        str, typer.Option("--username", "-u", help="Fuseki username.")
    ] = None,
    password: Annotated[
        str, typer.Option("--password", "-p", help="Fuseki password.")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Timeout per request")
    ] = 60,
) -> None:
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as http_client:
        try:
            console.print(describe(fuseki_url, http_client=http_client))
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to describe datasets at {fuseki_url}."
            )
            raise err


@app.command(name="describe", help="Get the list of datasets or describe one")
def describe_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    username: Annotated[
        str, typer.Option("--username", "-u", help="Fuseki username.")
    ] = None,
    password: Annotated[
        str, typer.Option("--password", "-p", help="Fuseki password.")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Timeout per request")
    ] = 60,
) -> None:
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as http_client:
        try:
            console.print(describe(fuseki_url, http_client=http_client))
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to describe datasets at {fuseki_url}."
            )
            raise err


@app.command(
    name="create",
    help="Create a new dataset",
)
def create_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    dataset_name: str | None = typer.Argument(None, help="repository name"),
    dataset_type: str = typer.Option(
        "tdb2", help=f"dataset type. Options: {dataset_type_options}"
    ),
    config: Path | None = typer.Option(None, help="assembler file"),
    username: Annotated[
        str, typer.Option("--username", "-u", help="Fuseki username.")
    ] = None,
    password: Annotated[
        str, typer.Option("--password", "-p", help="Fuseki password.")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Timeout per request")
    ] = 60,
) -> None:
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    if dataset_name and config:
        raise typer.BadParameter("Only dataset name or --config is allowed, not both.")

    if dataset_name and dataset_type not in dataset_type_options:
        raise typer.BadParameter(
            f"Invalid dataset type '{dataset_type}'. Options: {dataset_type_options}"
        )

    if dataset_name:
        with httpx.Client(auth=auth, timeout=timeout) as http_client:
            try:
                console.print(
                    create(
                        fuseki_url, dataset_name, dataset_type, http_client=http_client
                    )
                )
            except Exception as err:
                console.print(
                    f"[bold red]ERROR[/bold red] Failed to create dataset {dataset_name} at {fuseki_url}."
                )
                raise err
    else:
        if config is None:
            raise typer.BadParameter(
                "Either dataset name or assembler config file must be provided."
            )
        with httpx.Client(auth=auth, timeout=timeout) as http_client:
            try:
                console.print(create(fuseki_url, config, http_client=http_client))
            except Exception as err:
                console.print(
                    f"[bold red]ERROR[/bold red] Failed to create dataset {dataset_name} at {fuseki_url}."
                )
                raise err


@app.command(name="delete", help="Delete a dataset")
def delete_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    dataset_name: str = typer.Argument(..., help="The name of the dataset to delete."),
    username: Annotated[
        str, typer.Option("--username", "-u", help="Fuseki username.")
    ] = None,
    password: Annotated[
        str, typer.Option("--password", "-p", help="Fuseki password.")
    ] = None,
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Timeout per request")
    ] = 60,
):
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as http_client:
        try:
            console.print(delete(fuseki_url, dataset_name, http_client=http_client))
        except FusekiError as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to delete dataset {dataset_name} at {fuseki_url}."
            )
            raise err
