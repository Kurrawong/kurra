from kurra.cli.app import app
from kurra.cli.commands.db import app as db_app
from kurra.cli.commands.file import app as file_app
from kurra.cli.commands.shacl import app as shacl_app
from kurra.cli.commands.sparql import app as sparql_app

app.add_typer(db_app, name="db")
app.add_typer(file_app, name="file")
app.add_typer(shacl_app, name="shacl")
app.add_typer(sparql_app)
