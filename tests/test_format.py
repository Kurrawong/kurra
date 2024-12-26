from kurrawong.format import format_rdf, format_file, do_format
from pathlib import Path

import subprocess


def test_format_rdf_one():
    input_file = Path(__file__).parent / "minimal1.ttl"
    output_file = Path(__file__).parent / "minimal1-out.ttl"
    comparison = """PREFIX ex: <http://example.com/>

ex:a
    ex:b ex:c ;
."""

    format_file(input_file, False, output_filename=output_file)
    output_file_text = output_file.read_text().strip()

    assert output_file_text == comparison

    output_file.unlink(missing_ok=True)


def test_format_cli():
    subprocess.check_output(
        ["kurra", "format", "--output-format", "json-ld", "tests/minimal1.ttl"]
    )

    comaprison = """[
  {
    "@id": "http://example.com/a",
    "http://example.com/b": [
      {
        "@id": "http://example.com/c"
      }
    ]
  }
]"""

    output_file = Path(__file__).parent / "minimal1.jsonld"

    assert open(output_file).read() == comaprison

    Path.unlink(output_file)
