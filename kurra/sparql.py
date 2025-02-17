from enum import Enum
from pathlib import Path
from textwrap import dedent

import httpx
from rdflib import BNode, Graph, Literal, URIRef

from kurra.db import sparql
from kurra.utils import load_graph


def query(
    path_str_graph_or_sparql_endpoint: Path | str | Graph,
    q: str,
    username: str = None,
    password: str = None,
    timeout: int = None,
    return_python: bool = False,
    return_bindings_only: bool = False,
):
    auth = (
        (username, password) if username is not None and password is not None else None
    )
    r = None
    if str(path_str_graph_or_sparql_endpoint).startswith("http"):
        with httpx.Client(auth=auth, timeout=timeout) as client:
            p = str(path_str_graph_or_sparql_endpoint)
            r = sparql(p, q, client, True, False)

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
                "head" : { } ,
                "boolean" : True if x.askAnswer else False,
            }


    match (return_python, return_bindings_only):
        case (True, True):
            return r.json()["results"]["bindings"]
        case (True, False):
            return r.json()
        case (False, True):
            return dedent(r.text.split('"bindings": [')[1].split("]")[0])
        case _:
            return dict(r)
