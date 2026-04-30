import subprocess
from pathlib import Path


def test_reformat_cli():
    subprocess.check_output(
        [
            "kurra",
            "file",
            "reformat",
            "--output-format",
            "json-ld",
            str(Path(__file__).parent.parent.resolve() / "file/minimal1.ttl"),
        ]
    )

    comparison = """[
  {
    "@id": "http://example.com/a",
    "http://example.com/b": [
      {
        "@id": "http://example.com/c"
      }
    ]
  }
]"""

    output_file = Path(__file__).parent.parent.resolve() / "file/minimal1.jsonld"

    assert open(output_file).read() == comparison

    Path.unlink(output_file)
