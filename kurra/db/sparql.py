from typing import Literal as LiteralType

import httpx

from kurra.utils import (
    _guess_query_is_update,
    _guess_return_type_for_sparql_query,
    add_namespaces_to_query_or_data,
    convert_sparql_json_to_python,
    make_sparql_dataframe,
)


def query(
    sparql_endpoint: str,
    q: str,
    namespaces: dict[str, str] | None = None,
    http_client: httpx.Client = None,
    return_format: LiteralType["original", "python", "dataframe"] = "original",
    return_bindings_only: bool = False,
):
    """Pose a SPARQL query to a SPARQL Endpoint"""
    if sparql_endpoint is None:
        raise ValueError("You must supply a sparql_endpoint")

    if q is None:
        raise ValueError("You must supply a query")

    if return_format not in ["original", "python", "dataframe"]:
        raise ValueError(
            f"return_format {return_format} must be either 'original', 'python' or 'dataframe'"
        )

    if namespaces is not None:
        q = add_namespaces_to_query_or_data(q, namespaces)

    if http_client is None:
        http_client = httpx.Client()

    if return_format == "dataframe":
        if (
            "CONSTRUCT" in q
            or "DESCRIBE" in q
            or "INSERT" in q
            or "DELETE" in q
            or "DROP" in q
        ):
            raise ValueError(
                'Only SELECT and ASK queries can have return_format set to "dataframe"'
            )

        try:
            from pandas import DataFrame
        except ImportError:
            raise ValueError(
                'You selected the output format "dataframe" by the pandas Python package is not installed.'
            )

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

    if "CONSTRUCT" in q or "DESCRIBE" in q:
        return r.text

    if return_format == "python":
        return convert_sparql_json_to_python(r, return_bindings_only)

    elif return_format == "dataframe":
        return make_sparql_dataframe(r.json())

    # original format - JSON
    return r.text
