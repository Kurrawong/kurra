from pathlib import Path

import typer
from rich.table import Table

from kurra.cli.console import console
from kurra.cli.utils import (
    format_shacl_graph_as_rich_table,
)
from kurra.shacl import list_local_validators, sync_validators, validate

app = typer.Typer(help="SHACL commands")


@app.command(
    name="validate",
    help="Validate a given file or directory of RDF files using a given SHACL file or directory of files",
)
def validate_command(
    file_or_dir: Path = typer.Argument(
        ..., help="The file or directory of RDF files to be validated"
    ),
    shacl_graph_or_file_or_url_or_id: str = typer.Argument(
        ..., help="The file or directory of SHACL files to validate with"
    ),
) -> None:
    """Validate a given file or directory of files using a given SHACL file or directory of files"""
    valid, g, txt = validate(file_or_dir, shacl_graph_or_file_or_url_or_id)
    if valid:
        console.print("The data is valid")
    else:
        console.print("The data is NOT valid")
        console.print("The errors are:")
        console.print(format_shacl_graph_as_rich_table(g))


@app.command(
    name="listv",
    help="Lists all known SHACL validators",
)
def listv_command():
    l = list_local_validators()
    if l is None:
        console.print("No local validators found")
    else:
        t = Table()
        t.add_column("ID")
        t.add_column("IRI")
        t.add_column("Name")
        for k, v in list_local_validators().items():
            t.add_row(v["id"], k, v["name"])
        console.print(t)


@app.command(
    name="syncv",
    help="Synchronizes SHACL validators",
)
def syncv_command():
    sync_validators()

    console.print("Synchronizing SHACL validators")
