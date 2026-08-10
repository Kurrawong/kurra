from pathlib import Path
from typing import Annotated, Literal

import typer
from rich.table import Table

import kurra.shacl
from kurra.cli.console import console
from kurra.cli.utils import (
    format_shacl_graph_as_rich_table,
    format_shacl_summary_as_rich_table,
)
from kurra.shacl import list_local_validators, sync_validators, validate

app = typer.Typer(help="SHACL commands")


def _parse_shacl(value: str | Path | int) -> Path | str | int:
    """Convert a CLI SHACL value to the type expected by ``validate``."""
    if isinstance(value, (Path, int)):
        return value
    if value.isdigit():
        return int(value)

    path = Path(value)
    return path if path.exists() else value


@app.command(
    name="validate",
    help="Validate a given file or directory of RDF files using a given SHACL file or directory of files",
)
def validate_command(
    data: Annotated[
        list[Path],
        typer.Argument(
            help="The file, files or directory of RDF files to be validated"
        ),
    ],
    shacl: Annotated[
        str,
        typer.Option(
            "--shacl",
            "-s",
            callback=_parse_shacl,
            help="The file, directory of files, IRI of or the kurra ID for the SHACL graph to validate with",
        ),
    ],
    hide_warnings: Annotated[
        bool,
        typer.Option(
            "--hide-warnings", "-hw", help="Hides Shapes results of Warning and Info"
        ),
    ] = False,
    summary: Annotated[
        bool,
        typer.Option(
            "--summary",
            "-y",
            help="Print a summary table instead of the full validation results",
        ),
    ] = False,
    output_format: Annotated[
        Literal["table", "rdf"],
        typer.Option(
            "--format",
            "-f",
            help="Output format: a Rich table or Long Turtle RDF",
        ),
    ] = "table",
) -> None:
    """Validate a given file or directory of files using a given SHACL file or directory of files"""
    valid, g, txt, summary_graph = validate(data, shacl, hide_warnings=hide_warnings)

    output_graph = summary_graph if summary else g

    if output_format == "rdf":
        console.print(output_graph.serialize(format="longturtle"))
    else:
        if valid:
            console.print("The data is valid")
        else:
            console.print("The data is NOT valid")
            console.print("The errors are:")

            if summary:
                console.print(format_shacl_summary_as_rich_table(summary_graph))
            else:
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
