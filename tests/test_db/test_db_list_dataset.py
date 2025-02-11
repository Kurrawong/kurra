import pytest

from kurra.db import FusekiError, list_dataset


def test_db_list_datasets(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}"
    return_value = list_dataset(base_url, http_client)
    assert "/ds" in list(map(lambda x: x["ds.name"], return_value))


def test_db_list_datasets_non_existent(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}/some-url"
    with pytest.raises(FusekiError) as exc_info:
        list_dataset(base_url, http_client)

    assert (
        f"Failed to list datasets at http://localhost:{port}/some-url"
        in exc_info.value.message
    )
