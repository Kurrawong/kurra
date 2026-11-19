"""CLI commands for working with RDF files."""

import sys
from pathlib import Path
from typing import Annotated

import typer

from kurra.cli.commands.sparql import sparql_command as gsp_sparql_command
from kurra.cli.console import console
from kurra.file import (
    FailOnChangeError,
    export_quads,
    hierarchy,
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
    context: str | None = typer.Option(
        None,
        "--context",
        "-t",
        help="A JSON-LD context as inline JSON or a path to a JSON file.",
    ),
    indent: int = typer.Option(
        4,
        "--indent",
        min=0,
        help="Number of spaces used to indent compacted JSON-LD output.",
    ),
) -> None:
    """Reformat one RDF file or every RDF file in a directory to a given format.

    Args:
        file_or_dir: The file or directory of RDF files to be formatted.
        check: If True, check whether files will be changed by this command without applying the effect.
        output_format: The RDF serialization to write. See `RDF_FILE_SUFFIXES` for the available formats.
        output_filename: The name of the file to write the reformatted content to.
        context: An inline JSON-LD context or a path to a context file, supplied
            with `--context` or `-t`. Validated before writing. Prefix mappings
            shorten IRIs in Turtle/N3; JSON-LD output is compacted with PyLD.
        indent: Nonnegative indentation for compacted JSON-LD output. Defaults
            to 4 spaces. Only applies when a context and JSON-LD output are selected.

    Raises:
        SystemExit: With status 1, if `check` is set and reformatting would change a file.
    """
    context_value = context
    if context is not None:
        # JSON objects can be longer than the filesystem's filename limit.
        # Only attempt a path lookup when the value does not look like JSON.
        if not context.lstrip().startswith(("{", "[", '"')) and context != "null":
            context_value = Path(context)
    try:
        reformat(
            file_or_dir,
            check,
            output_format,
            output_filename,
            context=context_value,
            indent=indent,
        )
    except (ValueError, OSError) as err:
        raise typer.BadParameter(str(err)) from err
    except FailOnChangeError as err:
        print(err)
        sys.exit(1)


@app.command(name="merge", help="Merge RDF files")
def merge_command(
    files: Annotated[list[Path], typer.Argument(help="The RDF files to merge")],
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
            help=f"The RDFLib serialization format for the merged RDF. Available are {', '.join(RDF_FILE_SUFFIXES)}.",
        ),
    ] = "longturtle",
) -> None:
    """Merge multiple RDF files into a single graph or dataset document.

    Args:
        files: The RDF files to merge.
        destination: The output file path. If omitted, the merged RDF is printed.
        output_format: The RDFLib serialization format for the merged RDF. See `RDF_FILE_SUFFIXES` for the available formats.
    """
    merge(*files, destination=destination, output_format=output_format)


@app.command(name="hierarchy", help="Print an RDF class, property or concept hierarchy")
def hierarchy_command(
    path_or_url: Annotated[
        str,
        typer.Argument(help="An RDF file path or HTTP URL"),
    ],
    graph_iri: Annotated[
        str | None,
        typer.Option(
            "--graph-iri",
            "-g",
            help="The named graph to use from a remote, TriG or JSON-LD source.",
        ),
    ] = None,
    use_names: Annotated[
        bool,
        typer.Option(
            "--use-names",
            "-u",
            help="Display resource names instead of IRIs when available.",
        ),
    ] = False,
) -> None:
    """Print the class, property, or concept hierarchy found in an RDF source.

    Args:
        path_or_url: An RDF file path or HTTP URL.
        graph_iri: The named graph to use, for remote, TriG, or JSON-LD sources.
        use_names: If True, display resource names instead of IRIs where available.
    """
    source = path_or_url if path_or_url.startswith("http") else Path(path_or_url)
    hierarchy(source, graph_iri=graph_iri, use_names=use_names)


@app.command(
    name="quads",
    help="Exports (prints or saves) triples as quads with a given identifier",
)
def quads_command(
    path_or_str: Path,
    graph_iri: str,
    destination: Annotated[
        Path,
        typer.Option(
            "--destination",
            "-d",
            help="The path of the file to save. None prints to screen",
        ),
    ] = None,
):
    """Export (prints or saves) triples from an RDF source as quads under a given graph identifier.

    Args:
        path_or_str: The RDF file to read triples from.
        graph_iri: The graph IRI to assign to every exported quad.
        destination: The path of the file to save the quads to. If omitted, the result is printed to the console.
    """
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
    """Run a SPARQL query against a local RDF file or a remote SPARQL endpoint.

    Args:
        path_or_url: A local RDF file path or a SPARQL endpoint URL to query.
        q: A SPARQL query string, or the path to a file containing one.
        response_format: The response format of the SPARQL query. Either `table` (default) or `json`.
        username: Fuseki username, if the endpoint requires authentication.
        password: Fuseki password, if the endpoint requires authentication.
        timeout: Timeout per request, in seconds.
    """
    try:
        if Path(q).is_file():
            q = Path(q).read_text()
    except Exception:
        pass
    gsp_sparql_command(path_or_url, q, response_format, username, password, timeout)
