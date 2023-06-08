import typer

from kurrawong.cli.commands import fuseki

app = typer.Typer()
app.add_typer(fuseki.app, name="fuseki", help="Fuseki commands.")
