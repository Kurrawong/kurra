import sys

import typer

from kurrawong.cli import app
from kurrawong.format import FailOnChangeError, format_rdf


@app.command(name="format", help="Format Turtle files using the longturtle format.")
def format_command(
    file_or_dir: str = typer.Argument(
        ..., help="The file or directory of Turtle files to be formatted"
    ),
    check: bool = typer.Option(
        False, help="Check whether files will be formatted without applying the effect."
    ),
) -> None:
    try:
        format_rdf(file_or_dir, check)
    except FailOnChangeError as err:
        print(err)
        sys.exit(1)
