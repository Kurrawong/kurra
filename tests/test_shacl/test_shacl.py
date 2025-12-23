import shutil
from pathlib import Path
from pickle import dump, load

import pytest
from rdflib import Dataset, URIRef
from rdflib.namespace import RDF, SH

from kurra.shacl import list_local_validators, sync_validators, validate
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


@pytest.mark.xfail
def test_sync_validators():
    kurra_cache = Path().home() / ".kurra"
    validators_cache = kurra_cache / "validators.pkl"

    if Path.is_dir(kurra_cache):
        shutil.rmtree(kurra_cache)

    known_validators = sync_validators()

    assert len(known_validators) == 10

    d = load(open(validators_cache, "rb"))
    d: Dataset
    d.remove_graph(d.get_graph(URIRef("https://prez.dev/manifest-validator")))
    with open(validators_cache, "wb") as f:
        dump(d, f)

    assert len(list_local_validators().keys()) == 9

    known_validators = sync_validators()

    assert len(known_validators) == 10


@pytest.mark.xfail
def test_list_local_validators():
    pm_cache = Path().home() / ".pm"

    if Path.is_dir(pm_cache):
        shutil.rmtree(pm_cache)

    sync_validators()

    assert len(list_local_validators().keys()) == 10


@pytest.mark.xfail
def test_validate_by_id():
    """Awaiting sync_validators()"""
    kurra_cache = Path().home() / ".kurra"
    validators_cache = kurra_cache / "validators.pkl"

    sync_validators()

    valid, g, txt = validate(SHACL_TEST_DIR / "vocab-valid.ttl", 9)
    assert (
        len(list(g.subjects(predicate=RDF.type, object=SH.ValidationResult))) == 1
    )  # Warning

    valid, g, txt = validate(SHACL_TEST_DIR / "vocab-invalid.ttl", 9)
    assert len(list(g.subjects(predicate=RDF.type, object=SH.ValidationResult))) == 6
