from kurrawong.cli.app import app
from kurrawong.cli.commands.format import app as format_app
from kurrawong.cli.commands.version import app as version_app
from kurrawong.cli.commands.fuseki.app import app as fuseki_app

app.add_typer(fuseki_app)
app.add_typer(format_app)
app.add_typer(version_app)
