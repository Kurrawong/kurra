import typer

from . import dataset

app = typer.Typer()
app.add_typer(dataset.app, name="dataset", help="Fuseki Dataset commands.")

# Avoid circular import
import kurrawong.cli.commands.fuseki.upload
import kurrawong.cli.commands.fuseki.clear
