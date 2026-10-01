"""CLI commands for the Olis API (placeholder)."""

import typer

from kurra.cli.console import console

app = typer.Typer(help="Olis commands")


@app.command(name="stub", help="Placeholder command")
def exists_command():
    """Print a placeholder message.

    Reserved for a future Olis API integration; not yet implemented.
    """
    console.print("This is the Olis API's placeholder command")
