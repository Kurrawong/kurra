from pathlib import Path
from typing import Annotated

import httpx
import typer
from rich.progress import track

from kurra.cli.commands.sparql import sparql_command
from kurra.cli.console import console
from kurra.db import dataset_create, dataset_list
from kurra.db import suffix_map, upload, clear_graph

app = typer.Typer(help="RDF database commands. Currently only Fuseki is supported")


@app.command(name="list", help="Get the list of database repositories")
def repository_list_command(
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
                f"[bold red]ERROR[/bold red] Failed to list repositories at {fuseki_url}."
            )
            raise err


@app.command(name="create", help="Create a new database repository")
def repository_create_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    dataset_name: str = typer.Argument(..., help="repository name"),
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
                f"[bold red]ERROR[/bold red] Failed to create repository {dataset_name} at {fuseki_url}."
            )
            raise err


@app.command(name="upload", help="Upload files to a database repository")
def upload_command(
    path: Path = typer.Argument(
        ..., help="The path of a file or directory to be uploaded."
    ),
    fuseki_url: str = typer.Argument(
        ..., help="Repository SPARQL Endpoint URL. E.g. http://localhost:3030/ds"
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
    """Upload a file or a directory of files with an RDF file extension.

    File extensions: [.nt, .nq, .ttl, .trig, .json, .jsonld, .xml]

    Files are uploaded into their own named graph in the format:
    <urn:file:{file.name}>
    E.g. <urn:file:example.ttl>
    """
    files = []

    if path.is_file():
        files.append(path)
    else:
        files += path.glob("**/*")

    auth = (
        (username, password) if username is not None and password is not None else None
    )

    files = list(filter(lambda f: f.suffix in suffix_map.keys(), files))

    with httpx.Client(auth=auth, timeout=timeout) as client:
        for file in track(files, description=f"Uploading {len(files)} files..."):
            try:
                upload(fuseki_url, file, client, f"urn:file:{file.name}")
            except Exception as err:
                console.print(
                    f"[bold red]ERROR[/bold red] Failed to upload file {file}."
                )
                raise err


@app.command(name="clear", help="Clear a database repository")
def repository_clear_command(
    named_graph: str = typer.Argument(
        ..., help="Named graph. If 'all' is supplied, it will remove all named graphs."
    ),
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
):
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as client:
        try:
            clear_graph(fuseki_url, named_graph, client)
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to run clear command with '{named_graph}' at {fuseki_url}."
            )
            raise err


@app.command(name="delete", help="Delete a database repository")
def repository_delete_command():
    pass


@app.command(name="sparql", help="Query a database repository")
def sparql_command3(
    path_or_url: Path = typer.Argument(
        ..., help="Repository SPARQL Endpoint URL. E.g. http://localhost:3030/ds"
    ),
    q: str = typer.Argument(..., help="The SPARQL query to sent to the database"),
    response_format: Annotated[
        str,
        typer.Option(
            "--response-format",
            "-f",
            help="The response format of the SPARQL query",
        ),
    ] = "table",
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
    sparql_command(path_or_url, q, response_format, username, password, timeout)
