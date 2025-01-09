from json import loads

from rdflib.plugins.sparql.processor import SPARQLResult
from rich.table import Table


def format_sparql_response_as_rich_table(response):
    t = Table()

    # if it's a SPARQL query to a Graph() object
    # first de-serialize it into a dict
    if isinstance(response, SPARQLResult):
        response = loads(response.serialize(format="json").decode())

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
