from rdflib import Graph
from rdflib.compare import isomorphic
from kurra.utils import guess_format_from_data, load_graph
from pathlib import Path


def test_guess_format_from_data():
    s = """
        PREFIX ex: <http://example.com/>
        
        ex:a ex:b ex:c .
        """

    assert guess_format_from_data(s) == "text/turtle"

    s2 = """
        @prefix ex: <http://example.com/> .

        ex:a ex:b ex:c .
        """

    assert guess_format_from_data(s2) == "text/turtle"

    s3 = """
        [
          {
            "@id": "http://example.com/a",
            "http://example.com/b": [
              {
                "@id": "http://example.com/c"
              }
            ]
          }
        ]
        """

    assert guess_format_from_data(s3) == "application/ld+json"

    s4 = """
        <http://example.com/a> <http://example.com/b> <http://example.com/c> .
        """

    assert guess_format_from_data(s4) == "application/n-triples"

    s5 = """
        <?xml version="1.0" encoding="utf-8"?>
        <rdf:RDF
           xmlns:ex="http://example.com/"
           xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        >
          <rdf:Description rdf:about="http://example.com/a">
            <ex:b rdf:resource="http://example.com/c"/>
          </rdf:Description>
        </rdf:RDF>
        """

    assert guess_format_from_data(s5) == "application/rdf+xml"

    # TODO: properly handle detection of HexTuples
    sx = """
        ["http://example.com/a", "http://example.com/b", "http://example.com/c", "globalId", "", ""]
        """

    assert guess_format_from_data(sx) == "application/ld+json"


def test_load_graph():
    g = Graph()
    g.parse(
        data="""
            PREFIX ex: <http://example.com/>
            
            ex:a ex:b ex:c .
            """
    )

    # load from a given Graph
    g2 = load_graph(g)

    assert isomorphic(g2, g)

    # load an RDF file
    g3 = load_graph(Path(__file__).parent / "test_file" / "minimal1.ttl")

    assert isomorphic(g3, g)

    # load data
    g4 = load_graph(
        """
            PREFIX ex: <http://example.com/>
            
            ex:a ex:b ex:c .
            """
    )

    assert isomorphic(g4, g)


def test_load_graph_dir():
    DIR_OF_RDF = Path(__file__).parent / "dir_of_rdf"
    g = Graph()
    g.parse(DIR_OF_RDF / "rdf_1.ttl")
    g.parse(DIR_OF_RDF / "rdf_2.ttl")
    g.parse(DIR_OF_RDF / "rdf_3.ttl")

    g2 = load_graph(DIR_OF_RDF)

    assert len(g2) == len(g)

    g.parse(DIR_OF_RDF / "subdir" / "rdf_4.ttl")

    g3 = load_graph(DIR_OF_RDF, recursive=True)

    assert len(g3) == len(g)
