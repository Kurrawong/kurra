import sys

import typer

from kurrawong.cli import app
from kurrawong.format import FailOnChangeError, format_rdf


@app.command(name="format", help="Format Turtle files using the longturtle format.")
def format_command(
    file_or_dir: str = typer.Argument(
        ..., help="The file or directory of RDF files to be formatted"
    ),
    check: bool = typer.Option(
        False, help="Check whether files will be formatted without applying the effect."
    ),
    output_format: str = typer.Option(
        "longturtle",
        help="Indicate the output RDF format. Available are 'turtle', 'longturtle', 'xml', 'n-triples' & 'json-ld'.",
    ),
    output_filename: str = typer.Option(
        None,
        help="the name of the file you want to write the reformatted content to",
    ),
) -> None:
    try:
        format_rdf(file_or_dir, check, output_format, output_filename)
    except FailOnChangeError as err:
        print(err)
        sys.exit(1)
