from pathlib import Path
from typing import Annotated

import httpx
import typer

from kurra.cli.console import console
from kurra.cli.utils import (
    format_sparql_response_as_json,
    format_sparql_response_as_rich_table,
)
from kurra.db import sparql
from kurra.utils import load_graph

app = typer.Typer()


@app.command(name="sparql", help="SPARQL queries to local RDF files or a database")
def sparql_command(
    path_or_url: Path,
    q: str,
    response_format: str = typer.Option(
        "table",
        "--response-format",
        "-f",
        help="The response format of the SPARQL query. Either 'table' (default) or 'json'",
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
    """SPARQL queries a local file or SPARQL Endpoint"""
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as client:
        try:
            r = None
            if str(path_or_url).startswith("http"):
                path_or_url = str(path_or_url).replace(":/", "://")
                r = sparql(str(path_or_url), q, client, True, False)

            if r is None:
                r = load_graph(path_or_url).query(q)

            if response_format == "table":
                console.print(format_sparql_response_as_rich_table(r))
            else:
                console.print(format_sparql_response_as_json(r))
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] SPARQL query to {path_or_url} failed: {err}."
            )
            raise err
