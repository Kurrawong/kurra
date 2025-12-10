from pathlib import Path
from typing import Annotated

import httpx
import typer
from rich.progress import track

from kurra.cli.commands import app
from kurra.cli.commands.sparql import sparql_command
from kurra.cli.console import console
from kurra.db.fuseki import FusekiError, ping, server, status, stats, backup, backups_list, sleep, tasks, metrics, describe, create, delete
from kurra.db.gsp import exists, get, put, post, delete, clear, upload
from kurra.db.utils import rdf_suffix_map


app = typer.Typer(help="Graph Store Protocol commands.")


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

    with httpx.Client(auth=auth, timeout=timeout) as http_client:
        try:
            clear(fuseki_url, named_graph, http_client=http_client)
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to run clear command with '{named_graph}' at {fuseki_url}."
            )
            raise err


@app.command(name="upload", help="Upload file(s) to a database repository")
def upload_command(
        path: Path = typer.Argument(
            ..., help="The path of a file or directory of files to be uploaded."
        ),
        sparql_endpoint: str = typer.Argument(
            ..., help="SPARQL Endpoint URL. E.g. http://localhost:3030/ds"
        ),
        username: Annotated[
            str, typer.Option("--username", "-u", help="Fuseki username.")
        ] = None,
        password: Annotated[
            str, typer.Option("--password", "-p", help="Fuseki password.")
        ] = None,
        graph_id: Annotated[
            str | None, typer.Option("--graph", "-g",
                                     help="ID - IRI or URN - of the graph to upload into. If not set, the default graph is targeted. If set to the string \"file\", the URN urn:file:FILE_NAME will be used per file")
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

    files = list(filter(lambda f: f.suffix in rdf_suffix_map.keys(), files))

    with httpx.Client(
            auth=auth,
            timeout=timeout,
            headers={"Host": host_header} if host_header is not None else {},
            verify=False if disable_ssl_verification else True,
    ) as http_client:
        for file in track(files, description=f"Uploading {len(files)} files..."):
            try:
                if graph_id == "file":
                    upload(sparql_endpoint, file, f"urn:file:{file.name}", http_client=http_client)
                else:
                    upload(sparql_endpoint, file, graph_id if graph_id is not None else "default", http_client=http_client)  # str and None handled by upload()
            except Exception as err:
                console.print(
                    f"[bold red]ERROR[/bold red] Failed to upload file {file}."
                )
                raise err
