import json
from pathlib import Path
from sys import stdout
from typing import Annotated, Literal

import typer

from kurra.cli.console import console
from kurra.labels import find_missing_labels, get_labels, jsonld_context
from kurra.utils import load_graph

app = typer.Typer(help="Labelling commands")
from rich.table import Table


@app.command(name="find", help="Find IRIs missing labels")
def find_command(
    f: str = typer.Argument(
        ..., help="The RDF file to fine IRIs missing labels within"
    ),
    local_context: str = typer.Option(
        None,
        "--local-context",
        "-l",
        help="An RDF file or directory of RDF files containing labels",
    ),
) -> None:
    """Find IRIs missing labels"""
    if Path(f).is_file() or Path(f).is_dir():
        if local_context is not None:
            if Path(local_context).is_file() or Path(local_context).is_dir():
                for iri in find_missing_labels(Path(f), Path(local_context)):
                    console.print(iri)
            else:
                console.print(
                    "[red]If a value for local context is given, it must be an existing file or directory[/red]"
                )
        else:
            for iri in find_missing_labels(Path(f)):
                console.print(iri)
    else:
        console.print(
            "[red]The value for f must be an existing file or directory[/red]"
        )


@app.command(
    name="get",
    help="Gets labels for IRIs missing them from a given context or the KurrawongAI Semantic Background",
)
def get_command(
    f: str = typer.Argument(
        ..., help="The RDF file to fine IRIs missing labels within"
    ),
    local_context: str = typer.Option(
        None,
        "--local-context",
        "-l",
        help="An RDF file or directory of RDF files containing labels",
    ),
    additional_context: str = typer.Option(
        "https://fuseki.dev.kurrawong.ai/semback/sparql",
        "--additional-context",
        "-c",
        help="An additional source of labels",
    ),
    return_type: str = typer.Option(
        "graph",
        "--return-type",
        "-r",
        help="Return RDF in the longturtle format or a printed table of IRIs and labels. Either 'graph' or 'table'",
    ),
) -> None:
    """Gets labels for IRIs missing them from a given context or the KurrawongAI Semantic Background"""
    iris = []
    if Path(f).is_file() or Path(f).is_dir():
        if local_context is not None:
            if Path(local_context).is_file() or Path(local_context).is_dir():
                iris = find_missing_labels(Path(f), Path(local_context))
            else:
                console.print(
                    "[red]If a value for local context is given, it must be an existing file or directory[/red]"
                )
        else:
            iris = find_missing_labels(Path(f))
    else:
        console.print(
            "[red]The value for f must be an existing file or directory[/red]"
        )

    if iris:
        if Path(additional_context).is_file() or Path(additional_context).is_dir():
            rdf = get_labels(iris, Path(additional_context, return_type))
        else:
            rdf = get_labels(iris, additional_context, return_type)

        if return_type == "graph":
            console.print(rdf.serialize(format="longturtle"))
        else:
            t = Table(show_header=True, header_style="b")
            t.add_column("IRI", no_wrap=True)
            t.add_column("Label", no_wrap=True)
            for iri, label in rdf.items():
                t.add_row(iri, label)
            console.print(t)
    else:
        console.print("No IRIs missing labels")


@app.command(
    "context", help="Generate a JSON-LD context based on the labels in a given RDF file"
)
def context_command(
    rdf: Annotated[
        Path, typer.Argument(help="The RDF file to generate a JSON-LD context from")
    ],
    local_context: Annotated[
        Path | None,
        typer.Option(
            "--local-context",
            "-l",
            help="An RDF file or directory of RDF files containing labels",
        ),
    ] = None,
) -> None:
    """
    Generate a JSON-LD context based on the labels in a given RDF file. If local_context is supplied then labels from that context will be used too.
    """
    if local_context is not None:
        ctx = jsonld_context(load_graph(rdf), load_graph(local_context))
    else:
        ctx = jsonld_context(load_graph(rdf))
    json.dump(ctx, stdout, indent=4)
