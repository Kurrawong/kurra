import sys
from pathlib import Path
from typing import Annotated

import typer
from rdflib.plugin import plugins
from rdflib.serializer import Serializer

from kurra.cli.commands.db.gsp import upload_command as gsp_upload_command
from kurra.cli.commands.sparql import sparql_command as gsp_sparql_command
from kurra.cli.console import console
from kurra.file import (
    FailOnChangeError,
    export_quads,
    make_dataset,
    merge,
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


@app.command(name="merge", help="Merge RDF files")
def merge_command(
    files: Annotated[
        list[Path], typer.Argument(help="The RDF files to merge")
    ],
    destination: Annotated[
        Path | None,
        typer.Option(
            "--destination",
            "-d",
            help="The output file path. If omitted, the merged RDF is printed.",
        ),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option(
            "--output-format",
            "-f",
            help=f"The RDFLib serialization format for the merged RDF. Available are {', '.join(["turtle", "xml", "json-ld", "nt"] )}.",
        ),
    ] = "turtle",
) -> None:
    merge(*files, destination=destination, output_format=output_format)


@app.command(
    name="quads",
    help="Exports (prints or saves) triples as quads with a given identifier",
)
def quads_command(
    path_or_str: Path,
    graph_iri: str,
    destination: Annotated[
        Path, typer.Option("--destination", "-d", help="The path of the file to save. None prints to screen")
    ] = None,
):
    r = export_quads(make_dataset(path_or_str, graph_iri), destination)
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
