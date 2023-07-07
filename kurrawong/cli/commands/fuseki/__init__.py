import typer

from . import upload
from . import dataset

app = typer.Typer()
app.add_typer(upload.app, name="upload", help="Fuseki upload.")
app.add_typer(dataset.app, name="dataset", help="Fuseki Dataset commands.")
