import sys

import typer

from kurra.format import FailOnChangeError, format_rdf, RDF_FILE_SUFFIXES

app = typer.Typer()


@app.command(name="format", help="Format RDF files using one of several common RDF formats.")
def format_command(
    file_or_dir: str = typer.Argument(
        ..., help="The file or directory of RDF files to be formatted"
    ),
    check: bool = typer.Option(
        False,
        "--check",
        "-c",
        help="Check whether files will be formatted without applying the effect."
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
        format_rdf(file_or_dir, check, output_format, output_filename)
    except FailOnChangeError as err:
        print(err)
        sys.exit(1)
