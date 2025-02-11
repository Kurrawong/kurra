from pathlib import Path
from typing import Annotated

import httpx
import typer
from rdflib import Graph

from kurra.cli.console import console
from kurra.cli.utils import (
    format_shacl_graph_as_rich_table,
    format_sparql_response_as_json,
    format_sparql_response_as_rich_table,
)
from kurra.db import sparql
from kurra.shacl import validate
from kurra.utils import load_graph

app = typer.Typer(help="SHACL commands")


@app.command(
    name="validate",
    help="Validate a given file or directory of RDF files using a given SHACL file or directory of files",
)
def shacl_command(
    file_or_dir: Path = typer.Argument(
        ..., help="The file or directory of RDF files to be validated"
    ),
    shacl_file_or_dir: Path = typer.Argument(
        ..., help="The file or directory of SAHCL files to validate with"
    ),
) -> None:
    """Validate a given file or directory of files using a given SHACL file or directory of files"""
    valid, g, txt = validate(file_or_dir, shacl_file_or_dir)
    if valid:
        console.print("The data is valid")
    else:
        console.print("The data is NOT valid")
        console.print("The errors are:")
        console.print(format_shacl_graph_as_rich_table(g))
