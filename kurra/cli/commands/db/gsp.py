from pathlib import Path
from typing import Annotated

import httpx
import typer
from rich.progress import track

from kurra.cli.console import console
from kurra.db.gsp import clear, delete, exists, get, post, put, upload
from kurra.utils import RDF_SUFFIX_MAP

app = typer.Typer(help="Graph Store Protocol commands")


@app.command(name="exists", help="Checks to see if a graph exists within a database")
def exists_command(
    sparql_endpoint_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    graph_identifier: Annotated[
        str,
        typer.Option(
            "--graph",
            "-g",
            help='ID - IRI or URN - of the graph to upload into. If not set, the default graph is targeted. If set to the string "file", the URN urn:file:FILE_NAME will be used per file',
        ),
    ] = "default",
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
            console.print(
                exists(sparql_endpoint_url, graph_identifier, http_client=http_client)
            )
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to run clear command with '{graph_identifier}' at {sparql_endpoint_url}."
            )
            raise err


@app.command(name="get", help="Gets the content of a database graph")
def get_command(
    sparql_endpoint_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    graph_identifier: Annotated[
        str,
        typer.Option(
            "--graph",
            "-g",
            help='ID - IRI or URN - of the graph to upload into. If not set, the default graph is targeted. If set to the string "file", the URN urn:file:FILE_NAME will be used per file',
        ),
    ] = "default",
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
            r = get(sparql_endpoint_url, graph_identifier, http_client=http_client)
            if r == 404:
                console.print("Graph not found")
            else:
                rdf = r.serialize(format="longturtle")
                if rdf == "":
                    console.print("No content")
                else:
                    console.print(rdf)

        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to run the get command with '{graph_identifier}' at {sparql_endpoint_url}: {err.message}."
            )
            raise err


@app.command(name="put", help="Load content into a database graph")
def put_command(
    path: Path = typer.Argument(
        ..., help="The path of a file or directory of files to be uploaded."
    ),
    sparql_endpoint_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    graph_identifier: Annotated[
        str,
        typer.Option(
            "--graph",
            "-g",
            help='ID - IRI or URN - of the graph to upload into. If not set, the default graph is targeted. If set to the string "file", the URN urn:file:FILE_NAME will be used per file',
        ),
    ] = "default",
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
            console.print(
                put(
                    sparql_endpoint_url, path, graph_identifier, http_client=http_client
                )
            )
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to run clear command with '{graph_identifier}' at {sparql_endpoint_url}."
            )
            raise err


@app.command(name="post", help="Add content to a database graph")
def post_command(
    path: Path = typer.Argument(
        ..., help="The path of a file or directory of files to be uploaded."
    ),
    sparql_endpoint_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    graph_identifier: Annotated[
        str,
        typer.Option(
            "--graph",
            "-g",
            help='ID - IRI or URN - of the graph to upload into. If not set, the default graph is targeted. If set to the string "file", the URN urn:file:FILE_NAME will be used per file',
        ),
    ] = "default",
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
            console.print(
                post(
                    sparql_endpoint_url, path, graph_identifier, http_client=http_client
                )
            )
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to run clear command with '{graph_identifier}' at {sparql_endpoint_url}."
            )
            raise err


@app.command(name="delete", help="Deletes the content of a database graph")
def delete_command(
    sparql_endpoint_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    graph_identifier: Annotated[
        str,
        typer.Option(
            "--graph",
            "-g",
            help='ID - IRI or URN - of the graph to upload into. If not set, the default graph is targeted. If set to the string "file", the URN urn:file:FILE_NAME will be used per file',
        ),
    ] = "default",
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
            console.print(
                delete(sparql_endpoint_url, graph_identifier, http_client=http_client)
            )
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to run clear command with '{graph_identifier}' at {sparql_endpoint_url}."
            )
            raise err


@app.command(name="clear", help="Clears a database graph")
def clear_command(
    sparql_endpoint_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
    ),
    graph_identifier: Annotated[
        str,
        typer.Option(
            "--graph",
            "-g",
            help='ID - IRI or URN - of the graph to upload into. If not set, the default graph is targeted. If set to the string "file", the URN urn:file:FILE_NAME will be used per file',
        ),
    ] = "default",
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
            clear(sparql_endpoint_url, graph_identifier, http_client=http_client)
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to run clear command with '{graph_identifier}' at {sparql_endpoint_url}."
            )
            raise err


@app.command(name="upload", help="Upload file(s) to a database")
def upload_command(
    path: Path = typer.Argument(
        ..., help="The path of a file or directory of files to be uploaded."
    ),
    sparql_endpoint: str = typer.Argument(
        ..., help="SPARQL Endpoint URL. E.g. http://localhost:3030/ds"
    ),
    graph_identifier: Annotated[
        str | None,
        typer.Option(
            "--graph",
            "-g",
            help='ID - IRI or URN - of the graph to upload into. If not set, the default graph is targeted. If set to the string "file", the URN urn:file:FILE_NAME will be used per file',
        ),
    ] = None,
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
        str | None, typer.Option("--host-header", "-e", help="Override the Host header")
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

    files = list(filter(lambda f: f.suffix in RDF_SUFFIX_MAP.keys(), files))

    with httpx.Client(
        auth=auth,
        timeout=timeout,
        headers={"Host": host_header} if host_header is not None else {},
        verify=False if disable_ssl_verification else True,
    ) as http_client:
        for file in track(files, description=f"Uploading {len(files)} files..."):
            try:
                if graph_identifier == "file":
                    upload(
                        sparql_endpoint,
                        file,
                        f"urn:file:{file.name}",
                        http_client=http_client,
                    )
                else:
                    upload(
                        sparql_endpoint,
                        file,
                        graph_identifier if graph_identifier is not None else "default",
                        http_client=http_client,
                    )  # str and None handled by upload()
            except Exception as err:
                console.print(
                    f"[bold red]ERROR[/bold red] Failed to upload file {file}."
                )
                raise err
