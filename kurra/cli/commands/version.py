import typer

from kurra import __version__
from kurra.cli.console import console

app = typer.Typer()


@app.command(name="version", help="Show the version of the kurra app.")
def version_command():
    console.print(f"{__version__}")


def version_callback(value: bool):
    if value:
        from kurra.cli.commands import version

        version.version_command()
        raise typer.Exit()
