from kurrawong.cli import app
from kurrawong import __version__


@app.command(name="version", help="Show the version of the kurra CLI app.")
def version_command():
    print(f"kurra version {__version__}")
