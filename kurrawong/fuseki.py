from pathlib import Path

import httpx

suffix_map = {
    ".nt": "application/n-triples",
    ".nq": "application/n-quads",
    ".ttl": "text/turtle",
    ".trig": "application/trig",
    ".json": "application/ld+json",
    ".jsonld": "application/ld+json",
    ".xml": "application/rdf+xml",
}


def upload_file(
    url: str,
    file: Path,
    http_client: httpx.Client,
    graph_name: str = None,
) -> None:
    params = {"graph": graph_name} if graph_name else None

    headers = {"content-type": suffix_map[file.suffix]}
    with open(file, "r", encoding="utf-8") as f:
        data = f.read()
        response = http_client.put(url, params=params, headers=headers, data=data)
        status_code = response.status_code

        if status_code != 200 and status_code != 201 and status_code != 204:
            raise RuntimeError(
                f"Received status code {status_code} for file {file} at url {url}. Message: {response.text}"
            )


def dataset_list(
    url: str,
    http_client: httpx.Client,
) -> str:
    response = http_client.get(f"{url}/$/datasets")
    status_code = response.status_code

    if response.status_code != 200:
        raise RuntimeError(
            f"Received status code {status_code}. Message: {response.text}"
        )

    return response.text
