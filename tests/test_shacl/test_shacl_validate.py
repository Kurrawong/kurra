from pathlib import Path

from kurra.shacl import validate
from kurra.utils import load_graph

SHACL_TEST_DIR = Path(__file__).parent.resolve()


def test_validate_simple():
    shacl_graph = load_graph(SHACL_TEST_DIR / "validator-vocpub-410.ttl")

    data_file = SHACL_TEST_DIR / "vocab-valid.ttl"
    valid, g, txt = validate(data_file, shacl_graph)
    assert valid

    data_file2 = SHACL_TEST_DIR / "vocab-invalid.ttl"
    valid2, g2, txt2 = validate(data_file2, shacl_graph)
    assert not valid2

    data_file3 = SHACL_TEST_DIR / "vocab-invalid2.ttl"
    valid3, g3, txt3 = validate(data_file3, shacl_graph)
    assert not valid3
