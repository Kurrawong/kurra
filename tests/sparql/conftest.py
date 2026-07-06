import time
from pathlib import Path

import docker
import httpx
import pytest
from testcontainers.core.container import DockerContainer

FUSEKI_IMAGE = "ghcr.io/kurrawong/fuseki-geosparql:git-main-e642d849"
GRAPHDB_IMAGE = "khaller/graphdb-free:10.0.0"
REPOSITORY_CONFIG = """
@prefix rep: <http://www.openrdf.org/config/repository#>.
@prefix sr: <http://www.openrdf.org/config/repository/sail#>.
@prefix sail: <http://www.openrdf.org/config/sail#>.
@prefix graphdb: <http://www.ontotext.com/config/graphdb#>.

[] a rep:Repository ;
   rep:repositoryID "test" ;
   rdfs:label "Test Repository" ;
   rep:repositoryImpl [
      rep:repositoryType "graphdb:SailRepository" ;
      sr:sailImpl [
         sail:sailType "graphdb:Sail"
      ]
   ] .
"""


def wait_for_logs(container, text, timeout=30, interval=0.5):
    """
    Wait until the container emits a log line containing `text`.
    """
    client = docker.from_env()
    start_time = time.time()

    logs_seen = ""

    while True:
        # Read logs incrementally
        logs = client.containers.get(container._container.id).logs().decode("utf-8")
        if text in logs:
            return True

        if time.time() - start_time > timeout:
            raise TimeoutError(f"Timed out waiting for log: {text}")

        time.sleep(interval)


@pytest.fixture(scope="function")
def fuseki_container(request: pytest.FixtureRequest):
    container = DockerContainer(FUSEKI_IMAGE)
    container.with_volume_mapping(
        str(Path(__file__).parent.parent / "sparql" / "shiro.ini"),
        "/fuseki/shiro.ini",
    )
    container.with_volume_mapping(
        str(Path(__file__).parent.parent / "db" / "config.ttl"),
        "/fuseki/config.ttl",
    )
    container.with_exposed_ports(3030)
    container.start()
    wait_for_logs(container, "Started")

    def cleanup():
        container.stop()

    request.addfinalizer(cleanup)
    return container


@pytest.fixture(scope="function")
def http_client(request: pytest.FixtureRequest):
    _http_client = httpx.Client(auth=("admin", "admin"))

    def cleanup():
        _http_client.close()

    request.addfinalizer(cleanup)
    return _http_client


class GraphDBContainer(DockerContainer):
    def __init__(self, image=GRAPHDB_IMAGE):
        super().__init__(image)
        self.with_exposed_ports(7200)

    @property
    def endpoint(self):
        host = self.get_container_host_ip()
        port = self.get_exposed_port(7200)
        return f"http://{host}:{port}"

    def wait_until_ready(self, timeout=60):
        import time

        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                response = httpx.get(f"{self.endpoint}/protocol")
                if response.status_code == 200:
                    return
            except Exception as e:
                pass

            time.sleep(1)

        raise RuntimeError("GraphDB did not become ready")


@pytest.fixture(scope="function")
def graphdb_container():
    """
    Starts a fresh GraphDB container for each test and tears it down
    automatically afterwards.
    """
    with GraphDBContainer() as container:
        container.wait_until_ready()

        response = httpx.post(
            f"{container.endpoint}/rest/repositories",
            files={
                "config": ("repo-config.ttl", REPOSITORY_CONFIG, "text/turtle"),
            },
        )

        if response.is_success:
            yield container
        else:
            raise RuntimeError(
                f"Failed to create GraphDB test repository: "
                f"{response.status_code} {response.text}"
            )
