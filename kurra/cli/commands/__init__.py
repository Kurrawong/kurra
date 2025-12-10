from kurra.cli.commands.db import app
from kurra.cli.commands.db.fuseki import app as fuseki_app
from kurra.cli.commands.db.gsp import app as gsp_app

app.add_typer(gsp_app, name="gsp")
app.add_typer(fuseki_app, name="fuseki")
