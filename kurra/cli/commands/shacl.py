from pathlib import Path

import typer
from rich.table import Table

import kurra.shacl
from kurra.cli.console import console
from kurra.cli.utils import (
    format_shacl_graph_as_rich_table,
)
from kurra.shacl import list_local_validators, sync_validators, validate
from kurra.utils import load_graph

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
        ...,
        help="The file, directory of files, IRI of or the kurra ID for the SHACL graph to validate with",
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


@app.command(
    name="infer",
    help="Infer new triples from given data using SHACL Rules (SRL syntax only)",
)
def infer_command(
    data: str = typer.Argument(
        ...,
        help="The path of file to apply the rules to. Turtle files ending .ttl only",
    ),
    rules: str = typer.Argument(
        ...,
        help="The path of the file containing the rules to apply to the data. SHACL Rules ending .srl only",
    ),
    include_base: str = typer.Option(
        "false",
        "--include-base",
        "-ib",
        help="whether to include the data triples in output",
    ),
):
    data = Path(data)
    rules = Path(rules)

    if not Path(data).is_file() or not Path(data).suffix == ".ttl":
        console.print("You must provide a path to a .ttl file for the data")

    if not Path(rules).is_file() or not Path(rules).suffix == ".srl":
        console.print("You must provide a path to a .srl file for the rules")

    results_graph = kurra.shacl.infer(
        data, rules, include_base=True if include_base == "true" else False
    )
    console.print(results_graph.serialize(format="longturtle"))
