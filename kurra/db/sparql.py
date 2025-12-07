import httpx
from .utils import _guess_return_type_for_sparql_query, _guess_query_is_update, make_sparql_dataframe
from rdflib import Literal
from typing import Literal as LiteralType


def query(
    sparql_endpoint: str,
    q: str,
    http_client: httpx.Client = None,
    return_format: LiteralType["original", "python", "dataframe"] = "original",
    return_bindings_only: bool = False,
):
    """Poses a SPARQL query to a SPARQL Endpoint"""
    if return_format not in ["original", "python", "dataframe"]:
        raise ValueError("return_format must be either 'original', 'python' or 'dataframe'")

    if return_format == "dataframe":
        if "CONSTRUCT" in q or "DESCRIBE" in q or "INSERT" in q or "DELETE" in q or "DROP" in q:
            raise ValueError("Only SELECT and ASK queries can have return_format set to \"dataframe\"")

        try:
            from pandas import DataFrame
        except ImportError:
            raise ValueError("You selected the output format \"dataframe\" by the pandas Python package is not installed.")

    if http_client is None:
        http_client = httpx.Client()

    if q is None:
        raise ValueError("You must supply a query")

    if _guess_query_is_update(q):
        headers = {"Content-Type": "application/sparql-update"}
    else:
        headers = {"Content-Type": "application/sparql-query"}

    headers["Accept"] = _guess_return_type_for_sparql_query(q)

    r = http_client.post(
        sparql_endpoint,
        headers=headers,
        content=q,
    )

    status_code = r.status_code

    # in case the endpoint doesn't allow POST
    if status_code == 405 or status_code == 422:
        r = http_client.get(
            sparql_endpoint,
            headers=headers,
            params={"query": q},
        )

        status_code = r.status_code

    if status_code != 200 and status_code != 201 and status_code != 204:
        raise RuntimeError(f"ERROR {status_code}: {r.text}")

    if status_code == 204:
        return ""

    if return_format == "python":
        r = r.json()
        if r.get("results") is not None:  # SELECT
            for row in r["results"]["bindings"]:
                for k, v in row.items():
                    if v["type"] == "literal":
                        if v.get("datatype") is not None:
                            row[k] = Literal(v["value"], datatype=v["datatype"]).toPython()
                        else:
                            row[k] = Literal(v["value"]).toPython()
                    elif v["type"] == "uri":
                        row[k] = v["value"]
            if return_bindings_only:
                r = r["results"]["bindings"]
            return r
        elif r.get("boolean") is not None:  # ASK
            if return_bindings_only:
                return bool(r["boolean"])
            else:
                return r

    elif return_format == "dataframe":
        return make_sparql_dataframe(r.json())

    # original format - JSON
    return r.text