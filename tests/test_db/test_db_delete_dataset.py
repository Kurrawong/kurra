import pytest

from kurra.db import FusekiError, delete_dataset


def test_db_delete_dataset(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}"
    dataset_name = "ds"
    return_value = delete_dataset(base_url, dataset_name, http_client)
    assert return_value == f"Dataset {dataset_name} deleted."


def test_db_delete_dataset_non_existent(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}"
    dataset_name = "non-existent"

    with pytest.raises(FusekiError) as exc_info:
        delete_dataset(base_url, dataset_name, http_client)

    assert f"Failed to delete dataset '{dataset_name}'" in exc_info.value.message
