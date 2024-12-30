import json
from pathlib import Path
from typing import Union
from textwrap import dedent
from rdflib import Graph

import httpx

from kurra.utils import guess_format_from_data, load_graph

suffix_map = {
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
    elif "CONSTRUCT" in query:
        return "text/turtle"
    else:
        return "application/sparql-results+json"


def upload(
    url: str,
    file_or_str_or_graph: Union[Path, str, Graph],
    graph_name: str = None,
    append: bool = False,
    http_client: httpx.Client = None,
) -> None:
    """This function uploads a file to a Fuseki server using the Graph Store Protocol.

    It will upload it into a graph named graph_name (an IRI). If no graph_name is given, it will be uploaded into
    the Fuseki default graph.

    By default, it will replace all content in the Named Graph or default graph. If append is set to True, it will
    add it to existing content in the graph_name Named Graph.

    An httpx Client may be supplied for efficient client reuse, else each call to this function will recreate a new
    Client."""

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    params = {"graph": graph_name} if graph_name else "default"

    data = load_graph(file_or_str_or_graph).serialize(format="longturtle")
    headers = {"content-type": "text/turtle"}

    if append:
        response = http_client.post(url, params=params, headers=headers, content=data)
    else:
        response = http_client.put(url, params=params, headers=headers, content=data)

    status_code = response.status_code

    if status_code != 200 and status_code != 201 and status_code != 204:
        message = (
            str(file_or_str_or_graph)
            if isinstance(file_or_str_or_graph, Path)
            else "content"
        )
        raise RuntimeError(
            f"Received status code {status_code} for file {message} at url {url}. Message: {response.text}"
        )

    if close_http_client:
        http_client.close()


def dataset_list(
    url: str,
    http_client: httpx.Client,
) -> str:
    headers = {"accept": "application/json"}
    response = http_client.get(f"{url}/$/datasets", headers=headers)
    status_code = response.status_code

    if status_code != 200:
        raise RuntimeError(
            f"Received status code {status_code}. Message: {response.text}"
        )

    return json.dumps(response.json(), indent=2)


def dataset_create(
    url: str, http_client: httpx.Client, dataset_name: str, dataset_type: str = "tdb2"
) -> str:
    data = {"dbName": dataset_name, "dbType": dataset_type}
    response = http_client.post(f"{url}/$/datasets", data=data)
    status_code = response.status_code

    if response.status_code != 200 and response.status_code != 201:
        raise RuntimeError(
            f"Received status code {status_code}. Message: {response.text}"
        )

    return f"Dataset {dataset_name} created at {url}."


def clear_graph(url: str, http_client: httpx.Client, named_graph: str):
    query = "CLEAR ALL" if named_graph == "all" else f"CLEAR GRAPH <{named_graph}>"
    headers = {"content-type": "application/sparql-update"}
    response = http_client.post(url, headers=headers, content=query)
    status_code = response.status_code

    if status_code != 204:
        raise RuntimeError(
            f"Received status code {status_code}. Message: {response.text}"
        )


def query(
    sparql_endpoint: str,
    query: str,
    http_client: httpx.Client = None,
    return_python: bool = False,
    return_bindings_only: bool = False,
):
    """Poses a SPARQL query to the Fuseki server."""

    if http_client is None:
        http_client = httpx.Client()

    if query is None:
        raise ValueError("You must supply a query")

    if _guess_query_is_update(query):
        headers = {"Content-Type": "application/sparql-update"}
    else:
        headers = {"Content-Type": "application/sparql-query"}

    headers["Accept"] = _guess_return_type_for_sparql_query(query)

    response = http_client.post(
        sparql_endpoint,
        headers=headers,
        content=query,
    )

    status_code = response.status_code

    if status_code != 200 and status_code != 201 and status_code != 204:
        raise RuntimeError(f"ERROR {status_code}: {response.text}")

    match (return_python, return_bindings_only):
        case (True, True):
            return response.json()["results"]["bindings"]
        case (True, False):
            return response.json()
        case (False, True):
            return dedent(response.text.split('"bindings": [')[1].split("]")[0])
        case _:
            return response.text
