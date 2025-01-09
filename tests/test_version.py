from typer.testing import CliRunner

from kurra import __version__
from kurra.cli import app

runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output == f"{__version__}\n"
