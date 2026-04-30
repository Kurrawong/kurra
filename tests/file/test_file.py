import warnings
from pathlib import Path
from textwrap import dedent

from rdflib import Dataset, Graph, URIRef

import kurra.file
from kurra.file import _format_file, export_quads, make_dataset, reformat
from kurra.utils import load_graph


def test_reformat_rdf_one():
    input_file = Path(__file__).parent / "minimal1.ttl"
    output_file = Path(__file__).parent / "minimal1-out.ttl"
    comparison = """PREFIX ex: <http://example.com/>

ex:a
    ex:b ex:c ;
."""

    _format_file(input_file, False, output_filename=output_file)
    output_file_text = output_file.read_text().strip().replace("ns1", "ex")

    assert output_file_text == comparison

    output_file.unlink(missing_ok=True)

    input_file = Path(__file__).parent / "minimal1b.ttl"
    output_file = Path(__file__).parent / "minimal1b-out.ttl"
    # same comparison data

    _format_file(input_file, False, output_filename=output_file)
    output_file_text = output_file.read_text().strip().replace("ns1", "ex")

    assert output_file_text == comparison

    output_file.unlink(missing_ok=True)


def test_reformat_headers():
    input_file = Path(__file__).parent / "header.ttl"
    output_file = input_file.with_suffix(".2.ttl")
    kurra.file.reformat(input_file, False, output_filename=output_file)

    expected = dedent(
        """
        # some pointless comment
        
        # another
        
        PREFIX ex: <http://example.com/>
        
        ex:a
            ex:b ex:c ;
        .
        """
    ).strip()

    with open(output_file) as f:
        actual = f.read().strip()

    assert expected == actual

    Path.unlink(output_file, missing_ok=True)


def test_make_dataset():
    g = load_graph(
        """
        PREFIX ex: <http://example.com/>
        
        ex:a ex:b ex:c . 
        """
    )

    d = make_dataset(g, "http://graph.com/a")

    for t in d.quads():
        assert t[0] == URIRef("http://example.com/a")
        assert t[1] == URIRef("http://example.com/b")
        assert t[2] == URIRef("http://example.com/c")
        assert t[3] == URIRef("http://graph.com/a")


def test_export_quads():
    g = Graph()
    g.parse(
        data="""
            PREFIX ex: <http://example.com/>

            ex:a ex:b ex:c . 
            """,
        format="turtle",
    )

    d = make_dataset(g, "http://graph.com/a")

    qds = export_quads(d)

    warnings.filterwarnings(
        "ignore", category=DeprecationWarning
    )  # ignore RDFLib's ConjunctiveGraph warning
    d2 = Dataset()
    d2.parse(data=qds, format="trig")

    for t in d.quads():
        assert t[0] == URIRef("http://example.com/a")
        assert t[1] == URIRef("http://example.com/b")
        assert t[2] == URIRef("http://example.com/c")
        assert t[3] == URIRef("http://graph.com/a")


def test_sparql():
    # x = subprocess.check_output(
    #     ["kurra", "query", "--f", "table", "tests/minimal1.ttl", "ASK { ?s ?p ?o}"]
    # )
    #
    # print(x)
    pass


# TODO: NC: solution not found yet to carry the namespaces from the graph through to serialization
def test_prefixes():
    input_file = Path(__file__).parent / "prefixes-test.ttl"
    output_file = Path(__file__).parent / "prefixes-test-out.ttl"
    comparison = dedent(
        """
        PREFIX ex: <http://example.com/>
        PREFIX other: <http://other.com/>
        PREFIX sss: <https://schema.org/>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        
        ex:a
            ex:b other:c ;
        .
        
        ex:x 
            a skos:ConceptScheme ; 
            ex:b sss:y ;
        .
        """
    )

    _format_file(input_file, False, output_filename=output_file)

    # assert output_file == comparison

    output_file.unlink(missing_ok=True)


def test_directory():
    d = Path(__file__).parent

    expected_files = d.glob("**/*.jsonld")

    reformat(d, False, output_format="json-ld")

    # keep the input JSON-LD file
    for ef in expected_files:
        if ef.name != "minimal5.jsonld":
            print(f"removing {ef}")
            ef.unlink()
