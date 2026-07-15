from pathlib import Path
from typing import Literal as LiteralType

import httpx

from kurra import __version__
from kurra.utils import (
    add_namespaces_to_query_or_data,
    convert_sparql_json_to_python,
    is_construct_or_describe_query,
    is_select_or_ask_query,
    is_update_query,
    make_sparql_dataframe,
    make_system_specific_sparql_endpoint,
    sparql_statement_return_type,
    statement_type_for_query,
)

USER_AGENT_STRING = (
    f"kurra/{__version__} (https://pypi.org/project/kurra/; info@kurrawong.ai)"
)


def query(
    sparql_endpoint: str,
    q: str | Path,
    namespaces: dict[str, str] | None = None,
    http_client: httpx.Client = None,
    return_format: LiteralType["original", "python", "dataframe"] = "original",
    return_bindings_only: bool = False,
    user_agent: str = USER_AGENT_STRING,
):
    """Pose a SPARQL query to a SPARQL Endpoint"""
    if sparql_endpoint is None:
        raise ValueError("You must supply a sparql_endpoint")

    if q is None:
        raise ValueError("You must supply a query")

    if isinstance(q, str):
        if len(q) < 260:
            if Path(q).is_file():
                q = Path(q).read_text()

    if return_format not in ["original", "python", "dataframe"]:
        raise ValueError(
            f"return_format {return_format} must be either 'original', 'python' or 'dataframe'"
        )

    if namespaces is not None:
        q = add_namespaces_to_query_or_data(q, namespaces)

    if http_client is None:
        http_client = httpx.Client()

    headers = {}
    headers["Content-Type"] = "application/sparql-update"

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
        headers["Content-Type"] = "application/sparql-update"
    else:
        headers = {"Content-Type": "application/sparql-query"}

    headers["Accept"] = sparql_statement_return_type(q, statement)
    headers["User-Agent"] = user_agent

    ssse = make_system_specific_sparql_endpoint(sparql_endpoint, q, statement)

    r = http_client.post(
        ssse,
        headers=headers,
        content=q,
        follow_redirects=True,
        timeout=25,
    )

    status_code = r.status_code

    # in case the endpoint doesn't allow POST
    if 400 <= status_code < 600:
        r = http_client.get(
            sparql_endpoint,
            headers=headers,
            params={"query": q},
            follow_redirects=True,
            timeout=25,
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
