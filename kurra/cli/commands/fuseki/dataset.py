from typing import Annotated

import httpx
import typer

from kurra.cli.console import console
from kurra.fuseki import dataset_create, dataset_list

app = typer.Typer()


@app.command(name="list", help="Get a list of Fuseki datasets.")
def dataset_list_command(
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

    with httpx.Client(auth=auth, timeout=timeout) as client:
        try:
            result = dataset_list(fuseki_url, client)
            console.print(result)
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to list Fuseki datasets at {fuseki_url}."
            )
            raise err


@app.command(name="create", help="Create a new Fuseki dataset.")
def dataset_create_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    dataset_name: str = typer.Argument(..., help="Fuseki dataset name"),
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

    with httpx.Client(auth=auth, timeout=timeout) as client:
        try:
            result = dataset_create(fuseki_url, client, dataset_name)
            console.print(result)
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to create Fuseki dataset {dataset_name} at {fuseki_url}."
            )
            raise err
