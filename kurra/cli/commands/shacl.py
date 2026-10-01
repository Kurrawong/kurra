"""CLI commands for SHACL validation and inference."""

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
    """Convert a CLI SHACL value to the type expected by `validate`."""
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
    advanced: Annotated[
        bool,
        typer.Option(
            "--advanced",
            "-a",
            help="Enable SHACL Advanced Features (SHACL Rules, SPARQL-based constraints/targets/functions)",
        ),
    ] = False,
    return_type: Annotated[
        Literal["basic", "summary", "provenance"],
        typer.Option(
            "--return",
            "-r",
            help="What to return: the full validation results, a summary table/graph, or a PROV-O provenance graph",
        ),
    ] = "basic",
    output_format: Annotated[
        Literal["table", "rdf"],
        typer.Option(
            "--format",
            "-f",
            help="Output format: a Rich table or Long Turtle RDF. Has no effect if --return-type is provenance, which is always output as Turtle",
        ),
    ] = "table",
) -> None:
    """Validate an RDF file, files, or directory of files against a SHACL file, directory, or registered validator.

    Args:
        data: The file, files, or directory of RDF files to be validated.
        shacl: The file, directory of files, IRI of, or kurra ID for the SHACL graph to validate with.
        hide_warnings: If True, hide SHACL results of severity Warning and Info.
        advanced: If True, enable SHACL Advanced Features (SHACL Rules, SPARQL-based constraints/targets/functions).
        summary: If True, print a summary table instead of the full validation results.
        output_format: `table` (default) to print Rich table, or `rdf` for longturtle.
    """
    valid, g, txt, *extra_graph = validate(
        data,
        shacl,
        hide_warnings=hide_warnings,
        advanced=advanced,
        return_type=return_type,
    )
    extra_graph = extra_graph[0] if extra_graph else None

    if return_type == "provenance":
        console.print(extra_graph.serialize(format="longturtle"))
        return

    output_graph = extra_graph if return_type == "summary" else g
    if output_format == "rdf":
        console.print(output_graph.serialize(format="longturtle"))
    else:
        if valid:
            console.print("The data is valid")
        else:
            console.print("The data is NOT valid")
            console.print("The errors are:")

            if return_type == "summary":
                console.print(format_shacl_summary_as_rich_table(extra_graph))
            else:
                console.print(format_shacl_graph_as_rich_table(g))


@app.command(
    name="listv",
    help="Lists all known SHACL validators",
)
def listv_command():
    """Print a table of all known SHACL validators with ID, Name, IRI, and nested validator dependency rows."""
    l = list_local_validators()
    if l is None:
        console.print("No local validators found")
        return

    t = Table()
    t.add_column("ID")
    t.add_column("Name")
    t.add_column("IRI")

    def add_rows_with_deps(iri: str, prefix: str = "", connector: str = ""):
        t.add_row(l[iri]["id"], f"{prefix}{connector}{l[iri]['name']}", iri)

        children = [
            child for child in l[iri]["imports"] if child in l
        ]  # skips non-validator imports, but could skip unregistered validators or validators skipped by incomplete syncs
        for i, child in enumerate(children):
            last = i == len(children) - 1
            add_rows_with_deps(
                child,
                prefix
                + ("    " if connector == "└── " else "│   " if connector else ""),
                "└── " if last else "├── ",
            )

    for iri in l:
        add_rows_with_deps(iri)

    console.print(t)


@app.command(
    name="syncv",
    help="Synchronizes SHACL validators",
)
def syncv_command():
    """Refresh the local SHACL validator cache from the KurrawongAI Semantic Background."""
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
    """Infer new triples from RDF data using a SHACL Rules (SRL) file.

    Args:
        data: The path to a Turtle (`.ttl`) file containing the data to apply the rules to.
        rules: The path to a SHACL Rules (`.srl`) file containing the rules to apply.
        include_base: Whether to include the original data triples in the output, as the string `"true"` or `"false"`.
    """
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
