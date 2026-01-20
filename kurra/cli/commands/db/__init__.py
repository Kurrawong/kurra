from pathlib import Path
from typing import Annotated

import typer

from kurra.cli.commands.db.fuseki import app
from kurra.cli.commands.sparql import sparql_command

app = typer.Typer(help="RDF Database commands")


@app.command(name="sparql", help="SPARQL query an RDF database")
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
