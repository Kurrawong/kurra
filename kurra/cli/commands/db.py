from pathlib import Path
from typing import Annotated

import httpx
import typer
from rich.progress import track

from kurra.cli.commands.sparql import sparql_command
from kurra.cli.console import console
from kurra.db import (
    FusekiError,
    clear_graph,
    create_dataset,
    delete_dataset,
    list_dataset,
    suffix_map,
    upload,
)

app = typer.Typer(help="RDF database commands. Currently only Fuseki is supported")

dataset_type_options = ["mem", "tdb", "tdb1", "tdb2"]


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
            result = list_dataset(fuseki_url, client)
            console.print(result)
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to list repositories at {fuseki_url}."
            )
            raise err


@app.command(
    name="create",
    help="Create a new database repository. Provide either the dataset name and optionally the dataset type or provide the assembler file with --config.",
)
def repository_create_command(
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
        with httpx.Client(auth=auth, timeout=timeout) as client:
            try:
                result = create_dataset(fuseki_url, dataset_name, dataset_type, client)
                console.print(result)
            except Exception as err:
                console.print(
                    f"[bold red]ERROR[/bold red] Failed to create repository {dataset_name} at {fuseki_url}."
                )
                raise err
    else:
        if config is None:
            raise typer.BadParameter(
                "Either dataset name or assembler config file must be provided."
            )
        with httpx.Client(auth=auth, timeout=timeout) as client:
            try:
                result = create_dataset(fuseki_url, config, http_client=client)
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
    disable_ssl_verification: Annotated[
        bool,
        typer.Option(
            "--disable-ssl-verification", "-k", help="Disable SSL verification."
        ),
    ] = False,
    host_header: Annotated[
        str | None, typer.Option("--host-header", "-h", help="Override the Host header")
    ] = None,
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

    headers = {}
    if host_header is not None:
        headers["Host"] = host_header

    with httpx.Client(
        auth=auth,
        timeout=timeout,
        headers=headers,
        verify=False if disable_ssl_verification else True,
    ) as client:
        for file in track(files, description=f"Uploading {len(files)} files..."):
            try:
                upload(fuseki_url, file, f"urn:file:{file.name}", http_client=client)
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
def repository_delete_command(
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

    with httpx.Client(auth=auth, timeout=timeout) as client:
        try:
            success_message = delete_dataset(fuseki_url, dataset_name, client)
            console.print(success_message)
        except FusekiError as err:
            console.print(err)


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
