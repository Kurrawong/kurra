from typing import Annotated

import httpx
import typer

from kurra.cli.console import console
from kurra.fuseki import dataset_create, dataset_list
from pathlib import Path
from kurra.fuseki import suffix_map, upload, query
from rich.progress import track
from rich.table import Table
from rich.console import RenderableType

app = typer.Typer()

@app.command(name="list", help="Get a list of Fuseki datasets")
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


@app.command(name="create", help="Create a new Fuseki dataset")
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


@app.command(name="query", help="Query a Fuseki database")
def query_command(
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    q: str = typer.Argument(..., help="The SPARQL query to sent to the database"),
    response_format: Annotated[
        str,
        typer.Option(
            "--response-format",
            "-f",
            help="The response format of the SPARQL query",
        )
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
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as client:
        try:
            result = query(fuseki_url, q, client, return_python=True, return_bindings_only=False)

            if response_format == "table":
                t = Table()

                # ASK
                if not result.get("results"):
                    t.add_column("Ask")
                    t.add_row(str(result["boolean"]))
                else:
                    # SELECT
                    for x in result["head"]["vars"]:
                        t.add_column(x)
                    for row in result["results"]["bindings"]:
                        cols = []
                        for k, v in row.items():
                            cols.append(v["value"])
                        t.add_row(*tuple(cols))

                console.print(t)
            else:
                console.print(result)
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to query Fuseki at {fuseki_url}."
            )
            raise err


@app.command(name="upload", help="Upload files to a Fuseki dataset.")
def upload_command(
    path: Path = typer.Argument(
        ..., help="The path of a file or directory to be uploaded."
    ),
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki dataset URL. E.g. http://localhost:3030/ds"
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
