"""The kurra command-line application entry point."""

from typing import Annotated

import typer

from kurra import __version__
from kurra.cli.console import console

app = typer.Typer(
    invoke_without_command=True,
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[bool, typer.Option("--version", "-v", is_eager=True)] = False,
):
    """Entry point callback for the kurra CLI, run before any subcommand.

    Args:
        version: If True, print the installed kurra version and exit.

    Raises:
        typer.Exit: Raised after printing the version when `version` is True.
    """
    if version:
        console.print(__version__)
        raise typer.Exit()
