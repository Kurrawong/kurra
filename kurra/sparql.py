import json
from pathlib import Path

import httpx
from rdflib import BNode, Graph, Literal, URIRef

from kurra.db import sparql
from kurra.utils import load_graph


def query(
    path_str_graph_or_sparql_endpoint: Path | str | Graph,
    q: str,
    http_client: httpx.Client = None,
    return_python: bool = False,
    return_bindings_only: bool = False,
):
    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = None
    if str(path_str_graph_or_sparql_endpoint).startswith("http"):
        p = str(path_str_graph_or_sparql_endpoint)
        r = sparql(p, q, http_client, True, False)

    if r is None:
        r = {"head": {"vars": []}, "results": {"bindings": []}}
        x = load_graph(path_str_graph_or_sparql_endpoint).query(q)
        if x.vars is not None:
            for var in x.vars:
                r["head"]["vars"].append(str(var))

            for row in x.bindings:
                new_row = {}
                for k in r["head"]["vars"]:
                    v = row.get(k)
                    if v is not None:
                        if isinstance(v, URIRef):
                            new_row[str(k)] = {"type": "uri", "value": str(v)}
                        elif isinstance(v, BNode):
                            new_row[str(k)] = {"type": "bnode", "value": str(v)}
                        elif isinstance(v, Literal):
                            val = {"type": "literal", "value": str(v)}
                            if v.language is not None:
                                val["xml:lang"] = v.language
                            if v.datatype is not None:
                                val["datatype"] = v.datatype
                            new_row[str(k)] = val

                r["results"]["bindings"].append(new_row)
        else:
            r = {
                "head": {},
                "boolean": True if x.askAnswer else False,
            }

    if close_http_client:
        http_client.close()

    match (return_python, return_bindings_only):
        case (True, True):
            if r.get("results") is not None:
                return r["results"]["bindings"]
            elif r.get("boolean") is not None:  # ASK
                return r["boolean"]
            else:
                return r
        case (True, False):
            return r
        case (False, True):
            if r.get("results") is not None:
                return json.dumps(r["results"]["bindings"])
            elif r.get("boolean") is not None:  # ASK
                return json.dumps(r["boolean"])
            else:
                return json.dumps(r)
        case _:
            return json.dumps(r)
