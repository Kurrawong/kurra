from pathlib import Path
from pickle import dump, load

import httpx
from pyshacl import validate as v
from rdflib import Dataset, Graph, URIRef
from rdflib.namespace import SDO
from srl.engine import RuleEngine
from srl.parser import SRLParser

import kurra.sparql
from kurra.db.gsp import get as gsp_get
from kurra.sparql import query
from kurra.utils import load_graph


def validate(
    data_file_or_dir_or_graph_or_list: Path | Graph | list[Path] | list[Graph],
    shacl_graph_or_file_or_url_or_id: Graph | Path | str | int,
) -> tuple[bool, Graph, str]:
    """Validates a data graph using a shapes graph.

    Args:
        data_file_or_dir_or_graph_or_list: The path to an RDF data file, a graph, a list of Paths or a list of Graphs to validate. List items will be merged
        shacl_graph_or_file_or_url_or_id: The sHACL shapes to validate with

    Returns:
        Tuple[bool, Graph, str]: The validation status, results graph and message, all from pySHACL

    Raises:
        ValueError: If the ID of the SHACL validator is invalid
        RuntimeError: If the IRI of the SHACL validator cannot be resolved locally or against the Semantic Background's validators
    """
    kurra_cache = Path().home() / ".kurra"
    validators_cache = kurra_cache / "validators.pkl"

    data_graph = None
    shapes_graph = None

    def _get_shapes_from_iri(iri):
        local_validators = list_local_validators()
        for local_validator in local_validators.keys():
            if iri == local_validator:
                cv = load(open(validators_cache, "rb"))
                return cv.get_graph(URIRef(iri))

    def _get_shapes_from_id(id):
        id = int(id)
        local_validators = list_local_validators()
        max = len(local_validators.keys())
        if id < 0 or id > max:
            raise ValueError(f"shacl graph id value out of range. Must be <= {max}")
        for k, x in local_validators.items():
            if int(x["id"]) == id:
                cv = load(open(validators_cache, "rb"))
                return cv.get_graph(URIRef(k))

    # Try and resolve a validator IRI or string ID to a graph
    if isinstance(shacl_graph_or_file_or_url_or_id, str):
        if shacl_graph_or_file_or_url_or_id.startswith("http"):
            shapes_graph = _get_shapes_from_iri(shacl_graph_or_file_or_url_or_id)
        elif shacl_graph_or_file_or_url_or_id.isnumeric():
            shapes_graph = _get_shapes_from_id(shacl_graph_or_file_or_url_or_id)
        else:
            shapes_graph = get_validator_graph(shacl_graph_or_file_or_url_or_id)

    # Try and resolve an int validator ID to a graph
    elif isinstance(shacl_graph_or_file_or_url_or_id, int):
        shapes_graph = _get_shapes_from_id(shacl_graph_or_file_or_url_or_id)

    # Try and load the file/URL/path directly - Path
    else:
        shapes_graph = get_validator_graph(shacl_graph_or_file_or_url_or_id)

    # If the shapes graph is not yet loaded, try updating validators from the Semantic Background and try again
    if shapes_graph is None:
        # Try and resolve a validator IRI to a graph
        if isinstance(shacl_graph_or_file_or_url_or_id, str):
            if shacl_graph_or_file_or_url_or_id.startswith("http"):
                shapes_graph = _get_shapes_from_iri(shacl_graph_or_file_or_url_or_id)

    if shapes_graph is None:
        raise RuntimeError(
            f"Not able to load shapes graph: {shacl_graph_or_file_or_url_or_id}"
        )

    if isinstance(data_file_or_dir_or_graph_or_list, (Path, Graph)):
        data_graph = load_graph(data_file_or_dir_or_graph_or_list)
    elif isinstance(data_file_or_dir_or_graph_or_list, list):
        data_graph = Graph()
        for x in data_file_or_dir_or_graph_or_list:
            data_graph += load_graph(x)

    return v(data_graph, shacl_graph=shapes_graph, allow_warnings=True)


def list_local_validators() -> dict[str, dict[str, int]] | None:
    """Lists SHACL validators - IRI & name - stored in the local system's calidator cache.

    This function does not connect over the Internet."""
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
    """Checks the Semantic Background's read-only SPARQL Endpoint, currently https://fuseki.dev.kurrawong.ai/semback/sparql, for validators.

    It then checks local storage, using list_local_calidators(), to see which, if any, of those validators are stored locally.

    For any missing, it pulls down and stores a copy locally.
    """
    kurra_cache = Path().home() / ".kurra"
    validators_cache = kurra_cache / "validators.pkl"
    validator_ids_cache = kurra_cache / "validator_ids.pkl"
    semback_sparql_endpoint = "https://fuseki.dev.kurrawong.ai/semback/sparql"

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


def check_validator_known(validator_iri: str) -> bool:
    """Checks first locally and then in the Semantic Background to if a validator, identified by IRI, is known"""
    local_validators = list_local_validators()
    for local_validator in local_validators.keys():
        if validator_iri == local_validator:
            return True

    sync_validators()

    local_validators = list_local_validators()
    for local_validator in local_validators.keys():
        if validator_iri == local_validator:
            return True

    return False


def infer(
    data: Graph | Path | str, rules: Graph | Path | str, include_base=False
) -> Graph:
    """Applies rules to the data graph and returns a graph of calculated results

    Args:
        data: the data to apply the rules to
        rules: the rules to apply, in SHACL Rules SPARQL syntax
        include_base: whether to include the data triples in output

    Returns:
    """
    data_graph = load_graph(data)

    if not isinstance(rules, (Path, str)):
        raise NotImplementedError(
            "Only SHACL Rules in files ending .srl or as a string containing the Shape Rules Language (SRL) syntax is "
            "currently supported. The RDF format will be supported soon."
        )

    if isinstance(rules, Path):
        if rules.suffix == ".srl":
            rules = rules.read_text()
        else:
            raise ValueError(
                f"You have specified an unknown file type for the rules. It must end with .srl. You supplied a file with: {rules.suffix}"
            )

    if "DELETE" in rules:
        if isinstance(rules, Path):
            rules = rules.read_text()

        return kurra.sparql.query(data_graph, rules)

    interim_result = RuleEngine(SRLParser().parse(rules)).evaluate(
        data_graph, inplace=False
    )

    if include_base:
        return interim_result
    else:
        return interim_result - data_graph
