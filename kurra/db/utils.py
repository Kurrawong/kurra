from rdflib import Literal

rdf_suffix_map = {
    ".nt": "application/n-triples",
    ".nq": "application/n-quads",
    ".ttl": "text/turtle",
    ".trig": "application/trig",
    ".json": "application/ld+json",
    ".jsonld": "application/ld+json",
    ".xml": "application/rdf+xml",
}


def _guess_query_is_update(query: str) -> bool:
    if any(x in query for x in ["DROP", "INSERT", "DELETE"]):
        return True
    else:
        return False


def _guess_return_type_for_sparql_query(query: str) -> str:
    if any(x in query for x in ["SELECT", "INSERT", "ASK"]):
        return "application/sparql-results+json"
    elif "CONSTRUCT" in query or "DESCRIBE" in query:
        return "text/turtle"
    else:
        return "application/sparql-results+json"


def make_sparql_dataframe(sparql_result: dict):
    try:
        from pandas import DataFrame
    except ImportError:
        raise ValueError(
            'You selected the output format "dataframe" by the pandas Python package is not installed.'
        )

    if sparql_result.get("results") is not None:  # SELECT
        df = DataFrame(columns=sparql_result["head"]["vars"])
        for i, row in enumerate(sparql_result["results"]["bindings"]):
            new_row = {}
            for k, v in row.items():
                if v["type"] == "literal":
                    if v.get("datatype") is not None:
                        new_row[k] = Literal(
                            v["value"], datatype=v["datatype"]
                        ).toPython()
                    else:
                        new_row[k] = Literal(v["value"]).toPython()
                else:
                    new_row[k] = v["value"]
            df.loc[i] = new_row
        return df
    else:  # ASK
        df = DataFrame(columns=["boolean"])
        df.loc[0] = sparql_result["boolean"]

    return df
