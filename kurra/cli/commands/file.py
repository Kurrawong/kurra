import sys
from pathlib import Path
from typing import Annotated

import typer

from kurra.cli.commands.db.gsp import upload_command as gsp_upload_command
from kurra.cli.commands.sparql import sparql_command as gsp_sparql_command
from kurra.cli.console import console
from kurra.file import (
    FailOnChangeError,
    export_quads,
    make_dataset,
    reformat,
)
from kurra.utils import RDF_FILE_SUFFIXES

app = typer.Typer(help="RDF file commands")


@app.command(name="reformat", help="Reformat RDF files")
def reformat_command(
    file_or_dir: str = typer.Argument(
        ..., help="The file or directory of RDF files to be formatted"
    ),
    check: bool = typer.Option(
        False,
        "--check",
        "-c",
        help="Check whether files will be formatted without applying the effect.",
    ),
    output_format: str = typer.Option(
        "longturtle",
        "--output-format",
        "-f",
        help=f"Indicate the output RDF format. Available are {list(RDF_FILE_SUFFIXES.keys())}.",
    ),
    output_filename: str = typer.Option(
        None,
        "--output-filename",
        "-o",
        help="the name of the file you want to write the reformatted content to",
    ),
) -> None:
    try:
        reformat(file_or_dir, check, output_format, output_filename)
    except FailOnChangeError as err:
        print(err)
        sys.exit(1)


@app.command(name="upload", help="Upload files to a database repository")
def upload_command(
    path: Path = typer.Argument(
        ..., help="The path of a file or directory to be uploaded."
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
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Timeout per request")
    ] = 60,
) -> None:
    gsp_upload_command(path, sparql_endpoint, username, password, timeout)


@app.command(
    name="quads",
    help="Exports (prints or saves) triples as quads with a given identifier",
)
def quads_command(path_or_str: Path, identifier: str, destination: Path = None):
    r = export_quads(make_dataset(path_or_str, identifier), destination)
    if not destination:
        console.print(r)


@app.command(name="sparql", help="SPARQL queries to local RDF files or a database")
def query_command(
    path_or_url: Path,
    q: Annotated[
        str,
        typer.Option(
            help="A SPARQL query in a string on the command line or the path to a file containing a SPARQL query"
        ),
    ],
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
    try:
        if Path(q).is_file():
            q = Path(q).read_text()
    except:
        pass
    gsp_sparql_command(path_or_url, q, response_format, username, password, timeout)
