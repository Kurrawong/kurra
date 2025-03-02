from pathlib import Path
from typing import Annotated

import typer

from kurra.cli.console import console
from kurra.cli.utils import (
    format_sparql_response_as_json,
    format_sparql_response_as_rich_table,
)
from kurra.sparql import query

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
    if str(path_or_url).startswith("http"):
        path_or_url = str(path_or_url).replace(":/", "://")

    r = query(
        path_or_url,
        q,
        username,
        password,
        timeout,
        return_python=True
    )

    if response_format == "table":
        console.print(format_sparql_response_as_rich_table(r))
    else:
        console.print(format_sparql_response_as_json(r))
    # except Exception as err:
    #     console.print(
    #         f"[bold red]ERROR[/bold red] SPARQL query to {path_or_url} failed: {err}."
    #     )
    #     raise err
