from json import loads

from rdflib import Graph
from rdflib.namespace import RDF, RDFS, SH
from rdflib.plugins.sparql.processor import SPARQLResult
from rich.table import Table


def format_sparql_response_as_rich_table(response):
    t = Table()

    # ASK
    if not response.get("results"):
        t.add_column("Ask")
        t.add_row(str(response["boolean"]))
    else:  # SELECT
        for x in response["head"]["vars"]:
            t.add_column(x)
        for row in response["results"]["bindings"]:
            cols = []
            for k, v in row.items():
                cols.append(v["value"])
            t.add_row(*tuple(cols))

    return t


def format_sparql_response_as_json(response):
    if isinstance(response, SPARQLResult):
        response = loads(response.serialize(format="json").decode())

    return response


def format_shacl_graph_as_rich_table(g: Graph):
    t = Table(padding=(1, 0))
    t.add_column("No.")
    t.add_column("Error")
    t.add_column("Message")
    errs = 0
    for vr in g.subjects(RDF.type, SH.ValidationResult):
        errs += 1
        t.add_row(
            str(errs),
            g.value(vr, SH.focusNode),
            g.value(vr, SH.resultMessage),
        )

    return t
