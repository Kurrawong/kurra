import json
from pathlib import Path

from rdflib import Graph
from rdflib.compare import isomorphic

from kurra.utils import (
    RenderFormat,
    guess_format_from_data,
    load_graph,
    render_sparql_result,
)


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

    g5 = load_graph("https://raw.githubusercontent.com/RDFLib/prez/refs/heads/main/prez/reference_data/profiles/ogc_records_profile.ttl")

    assert len(g5) > 10


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


def test_render_sparql_result():
    # simple Python
    r1 = {
        "head": {"vars": ["iri", "value"]},
        "results": {
            "bindings": [
                {
                    "iri": {
                        "type": "uri",
                        "value": "https://linked.data.gov.au/dataset/qld-addr/address/605bf8e7-315a-562b-af4c-16a870732daf",
                    },
                    "value": {
                        "type": "literal",
                        "value": "72 Yundah Street, Shorncliffe, Queensland, Australia",
                    },
                },
                {
                    "iri": {
                        "type": "uri",
                        "value": "https://linked.data.gov.au/dataset/qld-addr/address/005fd678-6957-5953-975b-983515d3c145",
                    },
                    "value": {
                        "type": "literal",
                        "value": "104 Yundah Street, Shorncliffe, Queensland, Australia",
                    },
                },
            ]
        },
    }

    assert "| --- | --- |" in render_sparql_result(r1)

    # simple JSON
    r2 = """
{
  "head": {
    "vars": [
      "s",
      "p",
      "o"
    ]
  },
  "results": {
    "bindings": [
      {
        "s": {
          "type": "uri",
          "value": "http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode/accepted"
        },
        "p": {
          "type": "uri",
          "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
        },
        "o": {
          "type": "uri",
          "value": "http://www.w3.org/2004/02/skos/core#Concept"
        }
      },
      {
        "s": {
          "type": "uri",
          "value": "http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode/accepted"
        },
        "p": {
          "type": "uri",
          "value": "http://purl.org/linked-data/registry#status"
        },
        "o": {
          "type": "uri",
          "value": "http://def.isotc211.org/19135/-1/2015/CoreModel/code/RE_ItemStatus/stable"
        }
      },
      {
        "s": {
          "type": "uri",
          "value": "http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode/accepted"
        },
        "p": {
          "type": "uri",
          "value": "http://www.w3.org/2000/01/rdf-schema#isDefinedBy"
        },
        "o": {
          "type": "uri",
          "value": "http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode"
        }
      },
      {
        "s": {
          "type": "uri",
          "value": "http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode/accepted"
        },
        "p": {
          "type": "uri",
          "value": "http://www.w3.org/2004/02/skos/core#definition"
        },
        "o": {
          "type": "literal",
          "xml:lang": "en",
          "value": "Missing"
        }
      },
      {
        "s": {
          "type": "uri",
          "value": "http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode/accepted"
        },
        "p": {
          "type": "uri",
          "value": "http://www.w3.org/2004/02/skos/core#historyNote"
        },
        "o": {
          "type": "literal",
          "xml:lang": "en",
          "value": "Presented in the original standard's codelist"
        }
      },
      {
        "s": {
          "type": "uri",
          "value": "http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode/accepted"
        },
        "p": {
          "type": "uri",
          "value": "http://www.w3.org/2004/02/skos/core#inScheme"
        },
        "o": {
          "type": "uri",
          "value": "http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode"
        }
      },
      {
        "s": {
          "type": "uri",
          "value": "http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode/accepted"
        },
        "p": {
          "type": "uri",
          "value": "http://www.w3.org/2004/02/skos/core#prefLabel"
        },
        "o": {
          "type": "literal",
          "xml:lang": "en",
          "value": "accepted"
        }
      },
      {
        "s": {
          "type": "uri",
          "value": "http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode/accepted"
        },
        "p": {
          "type": "uri",
          "value": "http://www.w3.org/2004/02/skos/core#topConceptOf"
        },
        "o": {
          "type": "uri",
          "value": "http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode"
        }
      },
      {
        "s": {
          "type": "uri",
          "value": "http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode/accepted"
        },
        "p": {
          "type": "uri",
          "value": "https://schema.org/identifier"
        },
        "o": {
          "type": "literal",
          "datatype": "http://www.w3.org/2001/XMLSchema#token",
          "value": "accepted"
        }
      },
      {
        "s": {
          "type": "uri",
          "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
        },
        "p": {
          "type": "uri",
          "value": "https://schema.org/description"
        },
        "o": {
          "type": "literal",
          "value": "The subject is an instance of a class."
        }
      }
    ]
  }
}        
        """
    assert "| --- | --- | --- |" in render_sparql_result(r2)

    # OPTIONAL values / no values
    # multiple language literals
    r3 = """
{
  "head": {
    "vars": [
      "cs",
      "c",
      "pl",
      "al"
    ]
  },
  "results": {
    "bindings": [
      {
        "cs": {
          "type": "uri",
          "value": "https://example.com/demo-vocabs/language-test"
        },
        "c": {
          "type": "uri",
          "value": "https://example.com/demo-vocabs/language-test/en-variant"
        },
        "pl": {
          "type": "literal",
          "xml:lang": "eng",
          "value": "English prefLabel eng"
        }
      },
      {
        "cs": {
          "type": "uri",
          "value": "https://example.com/demo-vocabs/language-test"
        },
        "c": {
          "type": "uri",
          "value": "https://example.com/demo-vocabs/language-test/en-variant"
        },
        "pl": {
          "type": "literal",
          "xml:lang": "en-AU",
          "value": "English prefLabel en-au"
        }
      },
      {
        "cs": {
          "type": "uri",
          "value": "https://example.com/demo-vocabs/language-test"
        },
        "c": {
          "type": "uri",
          "value": "https://example.com/demo-vocabs/language-test/altlabels"
        },
        "pl": {
          "type": "literal",
          "xml:lang": "en",
          "value": "English prefLabel"
        },
        "al": {
          "type": "literal",
          "xml:lang": "pl",
          "value": "Polski prefLabel"
        }
      },
      {
        "cs": {
          "type": "uri",
          "value": "https://example.com/demo-vocabs/language-test"
        },
        "c": {
          "type": "uri",
          "value": "https://example.com/demo-vocabs/language-test/altlabels"
        },
        "pl": {
          "type": "literal",
          "xml:lang": "en",
          "value": "English prefLabel"
        },
        "al": {
          "type": "literal",
          "xml:lang": "ar",
          "value": "العربيةالعلامة المفضلة"
        }
      }
    ]
  }
}        
        """

    assert "| --- | --- | --- | --- |" in render_sparql_result(r3)

    r4 = """
        {
          "head": {},
          "boolean": true
        }
        """

    assert render_sparql_result(r4) == "True"

    r5 = """
        {
          "head": {},
          "boolean": false
        }        
        """

    assert render_sparql_result(r5) == "False"

    r6 = Graph().parse(
        data="""
            <https://pid.geoscience.gov.au/def/voc/ga/BoreholeStatus/completed> <http://schema.org/name> "completed"@en .
            <http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode/accepted> <http://schema.org/name> "accepted"@en .
            <http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode/completed> <http://schema.org/name> "completed"@en .            
            """,
        format="turtle",
    )

    assert render_sparql_result(r6).startswith("```")

    r7 = """
        {
          "head": {},
          "boolean": false
        }        
        """

    expected = {"head": {}, "boolean": False}

    assert json.loads(render_sparql_result(r7, RenderFormat.json)) == expected

    assert (
        '"@id": "http://def.isotc211.org/19115/-1/2014/IdentificationInformation/code/MD_ProgressCode/completed"'
        in str(render_sparql_result(r6, RenderFormat.json))
    )
