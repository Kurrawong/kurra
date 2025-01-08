import httpx
import typer
from typing_extensions import Annotated

from kurra.cli.commands.fuseki.app import app
from kurra.cli.console import console
from kurra.fuseki import clear_graph


@app.command(name="clear", help="Clear graph in the Fuseki dataset.")
def clear_command(
    named_graph: str = typer.Argument(
        ..., help="Named graph. If 'all' is supplied, it will remove all named graphs."
    ),
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki base URL. E.g. http://localhost:3030"
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
):
    auth = (
        (username, password) if username is not None and password is not None else None
    )

    with httpx.Client(auth=auth, timeout=timeout) as client:
        try:
            clear_graph(fuseki_url, client, named_graph)
        except Exception as err:
            console.print(
                f"[bold red]ERROR[/bold red] Failed to run clear command with '{named_graph}' at {fuseki_url}."
            )
            raise err
