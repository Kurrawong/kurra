from pathlib import Path
from pickle import dump, load

import httpx
from pyshacl import validate as v
from rdflib import Dataset, Graph, URIRef
from rdflib.namespace import SDO

from kurra.db.gsp import get as gsp_get
from kurra.sparql import query
from kurra.utils import load_graph


def validate(
    data_file_or_dir_or_graph: Path | Graph,
    shacl_graph_or_file_or_url_or_id: Graph | Path | str | int,
) -> tuple[bool, Graph, str]:
    """Runs pySHACL's validate() function with some preset values"""
    data_graph = load_graph(data_file_or_dir_or_graph)
    shapes_graph = get_validator_graph(shacl_graph_or_file_or_url_or_id)
    if shapes_graph is None:
        raise RuntimeError(
            f"Not able to load shapes graph: {shacl_graph_or_file_or_url_or_id}"
        )

    return v(data_graph, shacl_graph=shapes_graph, allow_warnings=True)


def list_local_validators() -> dict[str, dict[str, int]] | None:
    kurra_cache = Path().home() / ".kurra"
    validators_cache = kurra_cache / "validators.pkl"
    validator_ids_cache = kurra_cache / "validator_ids.pkl"

    if Path.is_file(validators_cache):
        local_validators = {}
        cv = load(open(validators_cache, "rb"))
        cv: Dataset
        validator_iris = [
            x.identifier
            for x in cv.graphs()
            if str(x.identifier) not in ["urn:x-rdflib:default"]
        ]

        validator_ids = load(open(validator_ids_cache, "rb"))

        for validator_iri in sorted(validator_iris):
            validator_id = validator_ids[validator_iri]
            validator_name = load_graph(cv.get_graph(validator_iri)).value(
                subject=validator_iri, predicate=SDO.name
            )
            local_validators[str(validator_iri)] = {
                "name": str(validator_name),
                "id": str(validator_id),
            }

        return local_validators
    else:
        return {}


def sync_validators(http_client: httpx.Client | None = None):
    """Checks the Semantic Background, currently https://fuseki.dev.kurrawong.ai/semback, for known validators.

    It then checks local storage to see which, if any, of those validators are stored locally.

    For any missing, it pulls down and stores a copy locally and updates the known list of available validators.
    """
    kurra_cache = Path().home() / ".kurra"
    validators_cache = kurra_cache / "validators.pkl"
    validator_ids_cache = kurra_cache / "validator_ids.pkl"
    semback_sparql_endpoint = "https://api.data.kurrawong.ai/sparql"

    # get list of remote validators
    q = """
        PREFIX schema: <https://schema.org/>
        
        SELECT * 
        WHERE { 
          <https://data.kurrawong.ai/sb/validators> schema:hasPart ?p
        }
        """
    r = query(semback_sparql_endpoint, q, None, http_client, "python", True)

    remote_validators = [row["p"] for row in r]

    # get list of local validators
    local_validators = list_local_validators()

    # diff the lists
    unknown_validators = list(set(remote_validators) - set(local_validators.keys()))

    # prepare to cache
    if len(unknown_validators) > 0:
        if not kurra_cache.exists():
            Path(kurra_cache).mkdir()

        # get & add unknown remote validators to local
        if validators_cache.exists():
            d = load(open(validators_cache, "rb"))
        else:
            d = Dataset()

        for v in unknown_validators:
            g = gsp_get(semback_sparql_endpoint, v, http_client=http_client)
            if g == 422:
                raise NotImplementedError(
                    "The KurrawongAI Semantic Background set of validators is not available yet."
                )
            if not isinstance(g, Graph):
                raise RuntimeError(
                    f"The graph {v} was not obtained from the SPARQL Endpoint {semback_sparql_endpoint}"
                )
            d.add_graph(g)
            print(f"Caching validator {g.identifier}")

        with open(validators_cache, "wb") as f:
            dump(d, f)

        validator_ids = {}
        for i, v in enumerate(sorted([x.identifier for x in d.graphs()])):
            validator_ids[v] = i + 1

        with open(validator_ids_cache, "wb") as f2:
            print("Dumping validator IDs")
            dump(validator_ids, f2)

    local_validators = list_local_validators()

    return local_validators


def get_validator_graph(
    graph_or_file_or_url_or_id: Graph | Path | str | int,
) -> Graph | None:
    kurra_cache = Path().home() / ".kurra"
    validators_cache = kurra_cache / "validators.pkl"
    validator_ids_cache = kurra_cache / "validator_ids.pkl"

    # it's a local ID so look it up in cache
    if isinstance(graph_or_file_or_url_or_id, int) or (
        isinstance(graph_or_file_or_url_or_id, str)
        and graph_or_file_or_url_or_id.isdigit()
    ):
        validator_ids = load(open(validator_ids_cache, "rb"))
        validator_iris = [
            key
            for key, value in validator_ids.items()
            if value == int(graph_or_file_or_url_or_id)
        ]
        if len(validator_iris) != 1:
            raise ValueError(
                f"Could not find validator for {graph_or_file_or_url_or_id}"
            )

        cv = load(open(validators_cache, "rb"))
        cv: Dataset
        return cv.graph(URIRef(validator_iris[0]))

    # cater for CLI making paths strings
    if isinstance(graph_or_file_or_url_or_id, str):
        if Path(graph_or_file_or_url_or_id).exists():
            return load_graph(Path(graph_or_file_or_url_or_id))

    try:
        return load_graph(graph_or_file_or_url_or_id)
    except:
        return None
