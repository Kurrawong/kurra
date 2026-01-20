from pathlib import Path

from typer.testing import CliRunner

from kurra.cli import app

runner = CliRunner()


def test_infer():
    INFER_DATA_DIR = Path(__file__).parent.parent.resolve() / "shacl" / "infer"

    result = runner.invoke(
        app,
        [
            "shacl",
            "infer",
            f"{INFER_DATA_DIR / '01-data.ttl'}",
            f"{INFER_DATA_DIR / '01-rules.srl'}",
        ],
    )

    assert "ns1:grandParent" in result.output
