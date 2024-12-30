import typer
from typing_extensions import Annotated

from kurra.cli import app as main_app
from kurra import __version__
from kurra.cli.console import console

app = typer.Typer()


@app.command(name="version", help="Show the version of the kurra CLI app.")
def version_command():
    console.print(f"kurra version {__version__}")


def version_callback(value: bool):
    if value:
        from kurra.cli.commands import version

        version.version_command()
        raise typer.Exit()


@main_app.callback(invoke_without_command=True)
def main(
    version: Annotated[
        bool, typer.Option("--version", callback=version_callback, is_eager=True)
    ] = False,
):
    """Main callback for the CLI app."""
    pass
