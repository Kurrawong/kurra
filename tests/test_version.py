from typer.testing import CliRunner

from kurrawong.cli import app
from kurrawong import __version__

runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.output == f"kurra version {__version__}\n"
