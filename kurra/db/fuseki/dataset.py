from io import TextIOBase
from pathlib import Path

import httpx
from rdflib import RDF, Graph, URIRef

from .utils import FusekiError


def dataset_list(
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


def create(
        sparql_endpoint: str,
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
        response = http_client.post(f"{sparql_endpoint}/$/datasets", data=data)
        status_code = response.status_code
        if response.status_code != 200 and response.status_code != 201:
            raise FusekiError(
                f"Failed to create dataset {dataset_name_or_config_file} at {sparql_endpoint}",
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
            f"{sparql_endpoint}/$/datasets",
            content=data,
            headers={"Content-Type": "text/turtle"},
        )
        status_code = response.status_code
        if response.status_code != 200 and response.status_code != 201:
            raise FusekiError(
                f"Failed to create dataset {dataset_name} at {sparql_endpoint}",
                response.text,
                status_code,
            )

        msg = f"{dataset_name} created using assembler config at"

    if close_http_client:
        http_client.close()

    return f"Dataset {msg} {sparql_endpoint}."


def delete(
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
