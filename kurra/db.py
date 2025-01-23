from io import TextIOBase
from pathlib import Path
from textwrap import dedent
from typing import Union

import httpx
from rdflib import RDF, Graph, URIRef

from kurra.utils import load_graph

suffix_map = {
    ".nt": "application/n-triples",
    ".nq": "application/n-quads",
    ".ttl": "text/turtle",
    ".trig": "application/trig",
    ".json": "application/ld+json",
    ".jsonld": "application/ld+json",
    ".xml": "application/rdf+xml",
}


class FusekiError(Exception):
    """An error that occurred while interacting with Fuseki."""

    def __init__(self, message_context: str, message: str, status_code: int) -> None:
        self.message = f"{status_code} {message_context}. {message}"
        super().__init__(self.message)


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
    http_client: httpx.Client | None = None,
) -> None:
    """This function uploads a file to a SPARQL Endpoint using the Graph Store Protocol.

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


def list_dataset(
    base_url: str,
    http_client: httpx.Client | None = None,
) -> dict:
    """
    List the datasets in a Fuseki server.

    :param base_url: The base URL of the Fuseki server. E.g., http://localhost:3030
    :param http_client: The synchronous httpx client to be used. If this is not provided, a temporary one will be created.
    :raises FusekiError: If the datasets fail to list or the server responds with an invalid data structure.
    :returns: The Fuseki listing of datasets as a dictionary.
    """
    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    headers = {"accept": "application/json"}
    response = http_client.get(f"{base_url}/$/datasets", headers=headers)
    status_code = response.status_code

    if status_code != 200:
        raise FusekiError(
            f"Failed to list datasets at {base_url}", response.text, status_code
        )

    if close_http_client:
        http_client.close()

    try:
        datasets = response.json()["datasets"]
        return datasets
    except KeyError:
        raise FusekiError(
            f"Failed to parse datasets response from {base_url}",
            response.text,
            status_code,
        )


def create_dataset(
    url: str,
    dataset_name_or_config_file: str | TextIOBase | Path,
    dataset_type: str = "tdb2",
    http_client: httpx.Client | None = None,
) -> str:
    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    if isinstance(dataset_name_or_config_file, str):
        data = {"dbName": dataset_name_or_config_file, "dbType": dataset_type}
        response = http_client.post(f"{url}/$/datasets", data=data)
        status_code = response.status_code
        if response.status_code != 200 and response.status_code != 201:
            raise FusekiError(
                f"Failed to create dataset {dataset_name_or_config_file} at {url}",
                response.text,
                status_code,
            )
        msg = f"{dataset_name_or_config_file} created at"
    else:
        if isinstance(dataset_name_or_config_file, TextIOBase):
            data = dataset_name_or_config_file.read()
        else:
            with open(dataset_name_or_config_file, "r") as file:
                data = file.read()

        graph = Graph().parse(data=data, format="turtle")
        fuseki_service = graph.value(
            None, RDF.type, URIRef("http://jena.apache.org/fuseki#Service")
        )
        dataset_name = graph.value(
            fuseki_service, URIRef("http://jena.apache.org/fuseki#name")
        )

        response = http_client.post(
            f"{url}/$/datasets",
            content=data,
            headers={"Content-Type": "text/turtle"},
        )
        status_code = response.status_code
        if response.status_code != 200 and response.status_code != 201:
            raise FusekiError(
                f"Failed to create dataset {dataset_name} at {url}",
                response.text,
                status_code,
            )

        msg = f"{dataset_name} created using assembler config at"

    if close_http_client:
        http_client.close()

    return f"Dataset {msg} {url}."


def clear_graph(url: str, named_graph: str, http_client: httpx.Client):
    query = "CLEAR ALL" if named_graph == "all" else f"CLEAR GRAPH <{named_graph}>"
    headers = {"content-type": "application/sparql-update"}
    response = http_client.post(url, headers=headers, content=query)
    status_code = response.status_code

    if status_code != 204:
        raise RuntimeError(
            f"Received status code {status_code}. Message: {response.text}"
        )


def delete_dataset(
    base_url: str, dataset_name: str, http_client: httpx.Client | None = None
) -> str:
    """
    Delete a Fuseki dataset.

    :param base_url: The base URL of the Fuseki server. E.g., http://localhost:3030
    :param dataset_name: The dataset to be deleted
    :param http_client: The synchronous httpx client to be used. If this is not provided, a temporary one will be created.
    :raises FusekiError: If the dataset fails to delete.
    :returns: A message indicating the successful deletion of the dataset.
    """
    if not dataset_name:
        raise ValueError("You must supply a dataset name")

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    response = http_client.delete(f"{base_url}/$/datasets/{dataset_name}")
    status_code = response.status_code

    if status_code != 200:
        raise FusekiError(
            f"Failed to delete dataset '{dataset_name}'", response.text, status_code
        )

    if close_http_client:
        http_client.close()

    return f"Dataset {dataset_name} deleted."


def sparql(
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
