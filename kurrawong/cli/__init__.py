import typer

from kurrawong.cli import commands

app = typer.Typer()
app.add_typer(commands.fuseki.app, name="fuseki", help="Fuseki commands.")

# Avoid circular import
import kurrawong.cli.commands.format
