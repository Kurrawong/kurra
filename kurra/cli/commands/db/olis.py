import typer

from kurra.cli.console import console

app = typer.Typer(help="Olis commands")


@app.command(name="stub", help="Placeholder command")
def exists_command():
    console.print("This is the Olis API's placeholder command")
