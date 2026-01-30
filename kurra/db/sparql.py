from typing import Literal as LiteralType

import httpx

from kurra.utils import (
    add_namespaces_to_query_or_data,
    convert_sparql_json_to_python,
    is_construct_or_describe_query,
    is_select_or_ask_query,
    is_update_query,
    make_sparql_dataframe,
    sparql_statement_return_type,
    statement_type_for_query,
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

    statement = statement_type_for_query(q)

    if return_format == "dataframe":
        if not is_select_or_ask_query(q, statement):
            raise ValueError(
                'Only SELECT and ASK queries can have return_format set to "dataframe"'
            )

        try:
            from pandas import DataFrame
        except ImportError:
            raise ValueError(
                'You selected the output format "dataframe" but the pandas Python package is not installed.'
            )

    if is_update_query(q, statement):
        headers = {"Content-Type": "application/sparql-update"}
    else:
        headers = {"Content-Type": "application/sparql-query"}

    headers["Accept"] = sparql_statement_return_type(q, statement)

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

    if is_construct_or_describe_query(q, statement):
        return r.text

    if return_format == "python":
        return convert_sparql_json_to_python(r, return_bindings_only)

    elif return_format == "dataframe":
        return make_sparql_dataframe(r.json())

    # original format - JSON
    return r.text
