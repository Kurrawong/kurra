"""SHACL functions."""

from pathlib import Path
from pickle import dump, load
from random import choice

import httpx
from pyshacl import validate as v
from rdflib import BNode, Dataset, Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, SDO, SH
from srl.engine import RuleEngine
from srl.parser import SRLParser

import kurra.sparql
from kurra.db.gsp import get as gsp_get
from kurra.sparql import query
from kurra.utils import load_graph

EX = Namespace("http://example.com/")


def _summarize_validation_results(validation_report: Graph) -> Graph:
    """Create a compact summary of a pySHACL validation results graph."""
    sg = Graph()
    sg.bind("ex", EX)
    sg.bind("sh", SH)

    results = set(
        validation_report.subjects(predicate=RDF.type, object=SH.ValidationResult)
    )
    report_summary = BNode()
    sg.add((report_summary, RDF.type, EX.ValidationReportSummary))

    summary = BNode()
    sg.add((summary, RDF.type, EX.ValidationCounts))
    sg.add((report_summary, EX["counts"], summary))

    for severity, predicate in (
        (SH.Violation, EX.violationCount),
        (SH.Warning, EX.warningCount),
        (SH.Info, EX.infoCount),
    ):
        count = sum(
            1
            for result in results
            if (result, SH.resultSeverity, severity) in validation_report
        )
        sg.add((summary, predicate, Literal(count)))

    results_by_shape = {}
    for result in results:
        for shape in validation_report.objects(result, SH.sourceShape):
            results_by_shape.setdefault(shape, []).append(result)

    for shape, shape_results in results_by_shape.items():
        s = BNode()
        sg.add((s, RDF.type, EX.ValidationResultSummary))
        sg.add((report_summary, EX["result"], s))
        sg.add((s, EX["count"], Literal(len(shape_results))))
        sg.add((s, SH.sourceShape, shape))

        examples = [
            (focus_node, message)
            for result in shape_results
            for focus_node in validation_report.objects(result, SH.focusNode)
            for message in validation_report.objects(result, SH.resultMessage)
        ]
        if examples:
            focus_node, message = choice(examples)
            sg.add((s, EX.exampleNode, focus_node))
            sg.add((s, SH.resultMessage, message))

    return sg


def _load_pickle(path: Path):
    with path.open("rb") as pickle_file:
        return load(pickle_file)


def validate(
    data: Path | Graph | list[Path] | list[Graph],
    shacl: Graph | Path | str | int,
    hide_warnings: bool = False,
    advanced: bool = False,
) -> tuple[bool, Graph, str, Graph]:
    """Validate a data graph using a shapes graph.

    Args:
        data: An RDF data file, Graph, or a list of files/Graphs to validate. List items are merged before validation.
        shacl: The SHACL shapes to validate with as a Graph, a file or directory path, a validator IRI, or a local validator ID.
        hide_warnings: If True, hide SHACL results of severity Warning and Info.
        advanced: If True, enable SHACL Advanced Features (SHACL Rules, SPARQL-based constraints/targets/functions).

    Returns:
        The validation status, results graph, message, and summary graph.

    Raises:
        ValueError: If a given local validator ID is out of range.
        RuntimeError: If the shapes graph cannot be resolved, locally or from the Semantic Background.
    """
    kurra_cache = Path().home() / ".kurra"
    validators_cache = kurra_cache / "validators.pkl"

    data_graph = None
    shapes_graph = None

    def _get_shapes_from_iri(iri: str):
        local_validators = list_local_validators()
        for local_validator in local_validators.keys():
            if iri == local_validator:
                cv = _load_pickle(validators_cache)
                return cv.graph(URIRef(iri))

    def _get_shapes_from_id(id: str | int):
        id = int(id)
        local_validators = list_local_validators()
        max = len(local_validators.keys())
        if id < 0 or id > max:
            raise ValueError(f"shacl graph id value out of range. Must be <= {max}")
        for k, x in local_validators.items():
            if int(x["id"]) == id:
                cv = _load_pickle(validators_cache)
                return cv.graph(URIRef(k))

    # Try and resolve a validator IRI or string ID to a graph
    if isinstance(shacl, str):
        if shacl.startswith("http"):
            shapes_graph = _get_shapes_from_iri(shacl)
        elif shacl.isnumeric():
            shapes_graph = _get_shapes_from_id(shacl)
        else:
            shapes_graph = get_validator_graph(shacl)

    # Try and resolve an int validator ID to a graph
    elif isinstance(shacl, int):
        shapes_graph = _get_shapes_from_id(shacl)

    # Try and load the file/URL/path directly - Path
    else:
        shapes_graph = get_validator_graph(shacl)

    # If the shapes graph is not loaded and is online iri, try updating validators from the Semantic Background and try again
    if shapes_graph is None and isinstance(shacl, str) and shacl.startswith("http"):
        sync_validators()
        shapes_graph = _get_shapes_from_iri(shacl)

    if shapes_graph is None:
        raise RuntimeError(f"Not able to load shapes graph: {shacl}")

    if isinstance(data, (Path, Graph)):
        data_graph = load_graph(data)
    elif isinstance(data, list):
        data_graph = Graph()
        for x in data:
            data_graph += load_graph(x)

    tf, g, msg = v(
        data_graph, shacl_graph=shapes_graph, allow_warnings=True, advanced=advanced
    )

    if hide_warnings:
        for s in g.subjects(predicate=RDF.type, object=SH.ValidationResult):
            if not g.value(subject=s, predicate=SH.resultSeverity) == SH.Violation:
                g = g - g.cbd(s)

    return tf, g, msg, _summarize_validation_results(g)


def list_local_validators() -> dict[str, dict[str, int]] | None:
    """List the SHACL validators cached locally, without contacting the Semantic Background.

    Returns:
        A dict keyed by validator IRI, each value holding `id`, `name`, and `imports` (a list of imported validator IRIs). Empty if nothing is cached yet.
    """
    kurra_cache = Path().home() / ".kurra"
    validators_cache = kurra_cache / "validators.pkl"
    validator_ids_cache = kurra_cache / "validator_ids.pkl"

    if Path.is_file(validators_cache):
        local_validators = {}
        cv = _load_pickle(validators_cache)
        cv: Dataset
        validator_iris = [
            x.identifier
            for x in cv.graphs()
            if str(x.identifier) not in ["urn:x-rdflib:default"]
        ]

        validator_ids = _load_pickle(validator_ids_cache)

        for validator_iri in sorted(validator_iris):
            validator_id = validator_ids[validator_iri]
            validator_name = load_graph(cv.graph(validator_iri)).value(
                subject=validator_iri, predicate=SDO.name
            )
            validator_imports = [
                str(obj)
                for obj in load_graph(cv.graph(validator_iri)).objects(
                    subject=validator_iri, predicate=OWL.imports
                )
            ]
            local_validators[str(validator_iri)] = {
                "name": str(validator_name),
                "id": str(validator_id),
                "imports": validator_imports,
            }

        return local_validators
    else:
        return {}


def sync_validators(
    http_client: httpx.Client | None = None,
) -> dict[str, dict[str, str | list[str]]]:
    """Refresh the local SHACL validator cache from the Semantic Background, downloading any validators not already cached locally.

    Args:
        http_client: An optional HTTPX client to contain credentials if needed to access a SPARQL endpoint as context. A new one is created if not given.

    Returns:
        The refreshed local validator listing, in the same form as `list_local_validators`.

    Raises:
        NotImplementedError: If the Semantic Background's validator set is not yet available.
        RuntimeError: If a validator's graph could not be fetched from the SPARQL endpoint.
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
    r = query(
        semback_sparql_endpoint,
        q,
        http_client=http_client,
        return_format="python",
        return_bindings_only=True,
    )

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
            d = _load_pickle(validators_cache)
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
    """Resolve a validator reference to its shapes graph.

    Args:
        graph_or_file_or_url_or_id: A Graph, RDF file path, local validator ID, or path/URL string.

    Returns:
        The resolved shapes Graph, or None if it could not be resolved.
    """
    kurra_cache = Path().home() / ".kurra"
    validators_cache = kurra_cache / "validators.pkl"
    validator_ids_cache = kurra_cache / "validator_ids.pkl"

    # it's a local ID so look it up in cache
    if isinstance(graph_or_file_or_url_or_id, int) or (
        isinstance(graph_or_file_or_url_or_id, str)
        and graph_or_file_or_url_or_id.isdigit()
    ):
        validator_ids = _load_pickle(validator_ids_cache)
        validator_iris = [
            key
            for key, value in validator_ids.items()
            if value == int(graph_or_file_or_url_or_id)
        ]
        if len(validator_iris) != 1:
            raise ValueError(
                f"Could not find validator for {graph_or_file_or_url_or_id}"
            )

        cv = _load_pickle(validators_cache)
        cv: Dataset
        return cv.graph(URIRef(validator_iris[0]))

    # cater for CLI making paths strings
    if isinstance(graph_or_file_or_url_or_id, str):
        if Path(graph_or_file_or_url_or_id).exists():
            return load_graph(Path(graph_or_file_or_url_or_id))

    try:
        return load_graph(graph_or_file_or_url_or_id)
    except Exception:
        return None


def check_validator_known(validator_iri: str) -> bool:
    """Check whether a validator identified by IRI is known either locally or via the Semantic Background. If not found locally the cache is synced to the Semantic Background for a recheck.

    Args:
        validator_iri: The IRI of the validator to check.

    Returns:
        True if the validator is known, either locally or after syncing from the Semantic Background.
    """
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
    data: Graph | Path | str,
    rules: Graph | Path | str,
    include_base: bool = False,
) -> Graph:
    """Apply SHACL Rules (SRL) to a data graph and return the inferred triples.

    If `rules` contains a SPARQL `DELETE` statement, it is run directly as a SPARQL update instead of being parsed as SRL.

    Args:
        data: The data graph to apply the rules to.
        rules: The SRL rules to apply, as a string or a path to a `.srl` file, or a raw SPARQL update if it contains `DELETE`.
        include_base: If True, include the original data triples in the result.

    Returns:
        The inferred triples, or (if `include_base`) the inferred triples plus the original data.

    Raises:
        NotImplementedError: If `rules` is a Graph (not yet supported).
        ValueError: If `rules` is a Path without a `.srl` suffix.
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
