import shutil
from pathlib import Path
from pickle import dump, load

from rdflib import Dataset, Literal, Namespace, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import RDF, SH

from kurra.shacl import (
    check_validator_known,
    list_local_validators,
    sync_validators,
    validate,
)
from kurra.sparql import query
from kurra.utils import load_graph

SHACL_TEST_DIR = Path(__file__).parent.resolve()
EX = Namespace("http://example.com/")


def test_validate_simple():
    shacl_graph = load_graph(SHACL_TEST_DIR / "validator-vocpub-410.ttl")

    data_file = SHACL_TEST_DIR / "vocab-valid.ttl"
    valid, g, txt, summary = validate(data_file, shacl_graph)
    assert valid

    data_file2 = SHACL_TEST_DIR / "vocab-invalid.ttl"
    valid2, g2, txt2, summary2 = validate(data_file2, shacl_graph)
    assert not valid2
    results = set(g2.subjects(RDF.type, SH.ValidationResult))
    assert len(summary2) > 0
    report_summary = summary2.value(
        predicate=RDF.type, object=EX.ValidationReportSummary, any=False
    )
    counts = summary2.value(report_summary, EX["counts"], any=False)
    assert (counts, RDF.type, EX.ValidationCounts) in summary2

    for severity, count_predicate in (
        (SH.Violation, EX.violationCount),
        (SH.Warning, EX.warningCount),
        (SH.Info, EX.infoCount),
    ):
        expected = sum(
            1 for result in results if (result, SH.resultSeverity, severity) in g2
        )
        assert (counts, count_predicate, Literal(expected)) in summary2

    for result_summary in summary2.subjects(RDF.type, EX.ValidationResultSummary):
        assert (report_summary, EX["result"], result_summary) in summary2
        shape = summary2.value(result_summary, SH.sourceShape)
        shape_results = {
            result for result in results if (result, SH.sourceShape, shape) in g2
        }
        assert summary2.value(result_summary, EX["count"]) == Literal(
            len(shape_results)
        )
        messages = list(summary2.objects(result_summary, SH.resultMessage))
        assert len(messages) == 1
        example_node = summary2.value(result_summary, EX.exampleNode)
        assert any(
            (result, SH.focusNode, example_node) in g2
            and (result, SH.resultMessage, messages[0]) in g2
            for result in shape_results
        )

    data_file3 = SHACL_TEST_DIR / "vocab-invalid2.ttl"
    valid3, g3, txt3, summary3 = validate(data_file3, shacl_graph)
    assert not valid3


def test_validate_multiple_data_files():
    data_files = [
        Path(__file__).parent / "vocab-invalid.ttl",
        Path(__file__).parent / "vocab-invalid-additions.ttl",
    ]
    v = validate(data_files, "https://linked.data.gov.au/def/vocpub/validator")
    assert v[0]


def test_sync_validators():
    kurra_cache = Path().home() / ".kurra"
    validators_cache = kurra_cache / "validators.pkl"

    # get number of SemBack validators
    q = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX schema: <https://schema.org/>
        
        SELECT (COUNT(*) AS ?count)
        WHERE {
          <https://data.kurrawong.ai/sb/validators>
                schema:hasPart ?o ;
          .
          
          ?o a owl:Ontology .
        }
        """
    num_remote_validators = query(
        "https://fuseki.dev.kurrawong.ai/semback/sparql",
        q,
        return_format="python",
        return_bindings_only=True,
    )[0]["count"]

    if Path.is_dir(kurra_cache):
        shutil.rmtree(kurra_cache)

    known_validators = sync_validators()

    assert len(known_validators) == num_remote_validators

    d = load(open(validators_cache, "rb"))
    d: Dataset
    d.remove_graph(d.get_graph(URIRef("https://prez.dev/manifest-validator")))
    with open(validators_cache, "wb") as f:
        dump(d, f)

    assert len(list_local_validators().keys()) == (num_remote_validators - 1)

    known_validators = sync_validators()

    assert len(known_validators) == num_remote_validators


def test_list_local_validators():
    pm_cache = Path().home() / ".pm"

    if Path.is_dir(pm_cache):
        shutil.rmtree(pm_cache)

    sync_validators()

    assert len(list_local_validators().keys()) == 87


def test_validate_by_id():
    """Awaiting sync_validators()"""
    sync_validators()

    valid, g, txt, summary = validate(SHACL_TEST_DIR / "vocab-valid.ttl", 83)
    assert (
        len(list(g.subjects(predicate=RDF.type, object=SH.ValidationResult))) == 0
    )  # Warning

    valid, g, txt, summary = validate(SHACL_TEST_DIR / "vocab-invalid.ttl", 83)
    assert len(list(g.subjects(predicate=RDF.type, object=SH.ValidationResult))) == 3


def test_check_validator_known():
    assert check_validator_known("https://linked.data.gov.au/def/vocpub/validator")
    assert not check_validator_known("https://linked.data.gov.au/def/vocpub/validatorx")


def test_summary(monkeypatch):
    # don't select a random node, select the first, ordered by string value
    # to ensure the exampleNode values in the expected and actual are the same
    monkeypatch.setattr(
        "kurra.shacl.choice",
        lambda examples: sorted(examples, key=lambda x: tuple(map(str, x)))[0],
    )

    expected = load_graph(
        """
        PREFIX ex: <http://example.com/>
        PREFIX schema: <https://schema.org/>
        PREFIX sh: <http://www.w3.org/ns/shacl#>
        
        [] a ex:ValidationReportSummary ;
            ex:counts [
                a ex:ValidationCounts ;
                ex:infoCount 0 ;
                ex:violationCount 1971 ;
                ex:warningCount 1314
            ] ;
            ex:result
                [
                    a ex:ValidationResultSummary ;
                    ex:count 657 ;
                    ex:exampleNode schema:AMRadioChannel ;
                    sh:resultMessage "Node :AMRadioChannel must conform to one or more shapes in <https://linked.data.gov.au/def/ontpub/req/2.2.1-prefLabel> , <https://linked.data.gov.au/def/ontpub/req/2.2.1-name>" ;
                    sh:sourceShape <https://linked.data.gov.au/def/ontpub/req/2.2.1>
                ],
                [
                    a ex:ValidationResultSummary ;
                    ex:count 657 ;
                    ex:exampleNode schema:AMRadioChannel ;
                    sh:resultMessage "Node :AMRadioChannel must conform to one or more shapes in <https://linked.data.gov.au/def/ontpub/req/2.2.2-property-shape-01> , <https://linked.data.gov.au/def/ontpub/req/2.2.2-property-shape-02>" ;
                    sh:sourceShape <https://linked.data.gov.au/def/ontpub/req/2.2.2>
                ],
                [
                    a ex:ValidationResultSummary ;
                    ex:count 657 ;
                    ex:exampleNode schema:AMRadioChannel ;
                    sh:resultMessage "Node :AMRadioChannel must conform to one or more shapes in <https://linked.data.gov.au/def/ontpub/req/2.2.3-property-shape-01> , <https://linked.data.gov.au/def/ontpub/req/2.2.3-property-shape-02> , <https://linked.data.gov.au/def/ontpub/req/2.2.3-property-shape-03>" ;
                    sh:sourceShape <https://linked.data.gov.au/def/ontpub/req/2.2.3>
                ],
                [
                    a ex:ValidationResultSummary ;
                    ex:count 657 ;
                    ex:exampleNode schema:AMRadioChannel ;
                    sh:resultMessage "Requirement 2.1.16: All sh:NodeShape and sh:PropertyShape instances MUST indicate the ontology that defines then with the rdfs:isDefinedBy property." ;
                    sh:sourceShape <https://linked.data.gov.au/def/ontpub/req/2.1.16-property-shape>
                ],
                [
                    a ex:ValidationResultSummary ;
                    ex:count 657 ;
                    ex:exampleNode schema:AMRadioChannel ;
                    sh:resultMessage "Requirement 2.2.4: Each element in an ontology SHOULD have at least one example of use indicated with a skos:example property that should be a text literal, preferably showing RDF source code." ;
                    sh:sourceShape <https://linked.data.gov.au/def/ontpub/req/2.2.4-property>
                ] .
             """
    )
    _, _, _, summary = validate(
        SHACL_TEST_DIR / "sdo-orig.ttl",
        "https://linked.data.gov.au/def/ontpub/validator",
    )

    assert isomorphic(summary, expected)
