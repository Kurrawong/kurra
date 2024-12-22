import typer

from .dataset import app as dataset_app

app = typer.Typer()

app.add_typer(dataset_app, name="dataset", help="Fuseki Dataset commands.")
