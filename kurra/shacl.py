"""SHACL functions."""

from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from pickle import dump, load
from random import choice
from typing import Literal, overload

import httpx
from pyshacl import validate as v
from rdflib import BNode, Dataset, Graph, Literal as RDFLiteral, Namespace, URIRef
from rdflib.namespace import OWL, PROV, RDF, SDO, SH, XSD, DefinedNamespace
from srl.engine import RuleEngine
from srl.parser import SRLParser

import kurra.sparql
from kurra.db.gsp import get as gsp_get
from kurra.sparql import query
from kurra.utils import load_graph

EX = Namespace("http://example.com/")


class SH12(DefinedNamespace):
    """SHACL 1.2 Profiling vocabulary terms not yet in rdflib's DefinedNamespace SH."""

    _NS = Namespace(str(SH))
    _fail = True

    DataGraph: URIRef
    ShapesGraph: URIRef
    ValidationAgent: URIRef
    ValidationActivity: URIRef
    usedDataGraph: URIRef
    usedShapesGraph: URIRef


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
        sg.add((summary, predicate, RDFLiteral(count)))

    results_by_shape = {}
    for result in results:
        for shape in validation_report.objects(result, SH.sourceShape):
            results_by_shape.setdefault(shape, []).append(result)

    for shape, shape_results in results_by_shape.items():
        s = BNode()
        sg.add((s, RDF.type, EX.ValidationResultSummary))
        sg.add((report_summary, EX["result"], s))
        sg.add((s, EX["count"], RDFLiteral(len(shape_results))))
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


def _extract_data_graph_nodes(
    data: Path | Graph | list[Path] | list[Graph],
) -> list[URIRef | BNode]:
    """Identifies the Data Graph(s) supplied to validate(), by file location if known."""
    items = data if isinstance(data, list) else [data]
    return [
        URIRef(item.resolve().as_uri()) if isinstance(item, Path) else BNode()
        for item in items
    ]


def _extract_shapes_graph_node(shacl: Graph | Path | str | int) -> URIRef | BNode:
    """Identifies the Shapes Graph supplied to validate(): its Semantic Background IRI if
    resolved via one, its file location if given as a path, otherwise a blank node."""
    if isinstance(shacl, str) and shacl.startswith("http"):
        return URIRef(shacl)

    if isinstance(shacl, int) or (isinstance(shacl, str) and shacl.isnumeric()):
        local_validators = list_local_validators()
        for iri, info in local_validators.items():
            if int(info["id"]) == int(shacl):
                return URIRef(iri)

    if isinstance(shacl, Path):
        return URIRef(shacl.resolve().as_uri())

    if isinstance(shacl, str) and Path(shacl).exists():
        return URIRef(Path(shacl).resolve().as_uri())

    return BNode()


def _build_provenance_graph(
    report_graph: Graph,
    data_graph_nodes: list[URIRef | BNode],
    shapes_graph_node: URIRef | BNode,
    started_at: datetime,
    ended_at: datetime,
) -> Graph:
    """Builds a PROV-O provenance graph for a validation run, following the activity-centric
    pattern in the SHACL 1.2 Profiling vocabulary's persisting validation results guidance."""
    pg = Graph()
    pg += report_graph
    pg.bind("prov", PROV)
    pg.bind("sh", SH12)

    report_node = pg.value(predicate=RDF.type, object=SH.ValidationReport)

    agent_node = URIRef(f"https://pypi.org/project/pyshacl/{version('pyshacl')}/")
    pg.add((agent_node, RDF.type, SH12.ValidationAgent))

    for data_graph_node in data_graph_nodes:
        pg.add((data_graph_node, RDF.type, SH12.DataGraph))

    pg.add((shapes_graph_node, RDF.type, SH12.ShapesGraph))

    activity_node = BNode()
    pg.add((activity_node, RDF.type, SH12.ValidationActivity))
    pg.add((activity_node, PROV.wasAssociatedWith, agent_node))
    for data_graph_node in data_graph_nodes:
        pg.add((activity_node, SH12.usedDataGraph, data_graph_node))
    pg.add((activity_node, SH12.usedShapesGraph, shapes_graph_node))
    if report_node is not None:
        pg.add((activity_node, PROV.generated, report_node))
    pg.add(
        (
            activity_node,
            PROV.startedAtTime,
            RDFLiteral(started_at.isoformat()[:19], datatype=XSD.dateTime),
        )
    )
    pg.add(
        (
            activity_node,
            PROV.endedAtTime,
            RDFLiteral(ended_at.isoformat()[:19], datatype=XSD.dateTime),
        )
    )

    return pg


@overload
def validate(
    data: Path | Graph | list[Path] | list[Graph],
    shacl: Graph | Path | str | int,
    hide_warnings: bool = False,
    advanced: bool = False,
    return_type: Literal["basic"] = "basic",
) -> tuple[bool, Graph, str]: ...


@overload
def validate(
    data: Path | Graph | list[Path] | list[Graph],
    shacl: Graph | Path | str | int,
    hide_warnings: bool,
    advanced: bool,
    return_type: Literal["summary"],
) -> tuple[bool, Graph, str, Graph]: ...


@overload
def validate(
    data: Path | Graph | list[Path] | list[Graph],
    shacl: Graph | Path | str | int,
    hide_warnings: bool,
    advanced: bool,
    return_type: Literal["provenance"],
) -> tuple[bool, Graph, str, Graph]: ...


def validate(
    data: Path | Graph | list[Path] | list[Graph],
    shacl: Graph | Path | str | int,
    hide_warnings: bool = False,
    advanced: bool = False,
    return_type: Literal["basic", "summary", "provenance"] = "basic",
):
    """Validates a data graph using a shapes graph.

    Args:
        data: The path to an RDF data file, a graph, a list of Paths or a list of Graphs to validate. List items will be merged
        shacl: The SHACL shapes to validate with
        return_type: What to return alongside the validation status, results graph and message.
            "basic" (the default) returns just those three. "summary" adds a compact summary graph.
            "provenance" adds a PROV-O provenance graph, per the SHACL 1.2 Profiling vocabulary's
            persisting validation results guidance.

    Returns:
        The validation status, results graph and message, plus a summary graph or a provenance
        graph if requested via return_type.

    Raises:
        ValueError: If the ID of the SHACL validator is invalid
        RuntimeError: If the IRI of the SHACL validator cannot be resolved locally or against the Semantic Background's validators
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

    started_at = datetime.now()
    tf, g, msg = v(
        data_graph, shacl_graph=shapes_graph, allow_warnings=True, advanced=advanced
    )
    ended_at = datetime.now()

    if hide_warnings:
        for s in g.subjects(predicate=RDF.type, object=SH.ValidationResult):
            if not g.value(subject=s, predicate=SH.resultSeverity) == SH.Violation:
                g = g - g.cbd(s)

    result = [tf, g, msg]
    if return_type == "summary":
        result.append(_summarize_validation_results(g))
    elif return_type == "provenance":
        result.append(_build_provenance_graph(
            g,
            _extract_data_graph_nodes(data),
            _extract_shapes_graph_node(shacl),
            started_at,
            ended_at,
        ))
    return tuple(result)


def list_local_validators() -> dict[str, dict[str, int]] | None:
    """Lists SHACL validators - IRI, name, and imports - stored in the local system's calidator cache.

    This function does not connect over the Internet."""
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


def sync_validators(http_client: httpx.Client | None = None):
    """Checks the Semantic Background's read-only SPARQL Endpoint, currently https://fuseki.dev.kurrawong.ai/semback/sparql, for validators.

    It then checks local storage, using ``list_local_calidators()``, to see which, if any, of those validators are stored locally.

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
    data: Graph | Path | str,
    rules: Graph | Path | str,
    include_base: bool = False,
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
