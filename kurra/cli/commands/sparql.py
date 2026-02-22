from pathlib import Path
from typing import Annotated

import httpx
import rdflib
import typer

from kurra.cli.console import console
from kurra.cli.utils import (
    format_sparql_response_as_json,
    format_sparql_response_as_rich_table,
)
from kurra.sparql import query

app = typer.Typer(context_settings={"terminal_width": 10000})
# app = typer.Typer()


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

    if isinstance(q, str):
        if len(q) < 260:
            if Path(q).is_file():
                q = Path(q).read_text()

    auth = (
        (username, password) if username is not None and password is not None else None
    )
    with httpx.Client(auth=auth, timeout=timeout) as http_client:
        r = query(path_or_url, q, http_client=http_client, return_format="python")

        if r == "":
            console.print("Operation completed successfully")
            return

        # if it is a graph, just print return the serialized form plainly, not via console.print()
        # to avoid terminal width breaking long literals, as per Issue 37
        if isinstance(r, rdflib.Graph):
            print(r.serialize(format="longturtle"))
        elif response_format == "table":
            console.print(format_sparql_response_as_rich_table(r, q))
        else:
            console.print(format_sparql_response_as_json(r))
