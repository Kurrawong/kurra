import itertools
from pathlib import Path
from typing import Literal as TypingLiteral
from typing import Optional, Tuple, Union

from rdflib import Dataset, Graph, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS

from kurra.utils import (
    RDF_FILE_SUFFIXES,
    _parse_dataset,
    _serialize_dataset,
    load_graph,
)


class FailOnChangeError(Exception):
    """
    This exception is raised when running format and the
    check bool is set to true and the file has resulted in a change.
    """


def merge(
    *files: Path,
    destination: Optional[Path] = None,
    output_format: TypingLiteral[
        "longturtle", "turtle", "xml", "json-ld", "nt"
    ] = "longturtle",
) -> None:
    """Merge RDF files and serialize their triples in a single RDF document.

    RDFLib infers each input format from its filename. The merged graph is printed
    when ``destination`` is not supplied; otherwise it is written to that path.
    """
    if output_format not in ["longturtle", "turtle", "xml", "json-ld", "nt"]:
        raise ValueError(
            "If you supply an output_format value, it must be one of 'turtle', 'xml', 'json-ld' or 'nt'"
        )

    g = Graph()
    for file in files:
        g.parse(source=Path(file))

    serialized = g.serialize(format=output_format)

    if destination is None:
        print(serialized, end="" if serialized.endswith("\n") else "\n")
    else:
        Path(destination).write_text(serialized, encoding="utf-8")


def do_format(
    content: str, output_format: RDF_FILE_SUFFIXES.keys() = "longturtle"
) -> Tuple[str, bool]:
    if output_format in ["turtle", "longturtle", "ttl", "nt", "n3"]:
        lines = content.split("\n")
        comments = []
        for i, line in enumerate(lines):
            if line.startswith("#") or line == "":
                comments.append(line)
            else:
                break

        content_no_comments = "\n".join(lines[len(comments) :])
        graph = load_graph(content_no_comments)
        if comments != []:
            header = "\n".join(comments) + "\n"
        else:
            header = ""
        new_content = header + graph.serialize(format=output_format, canon=True)
    else:
        clean_content = ""
        for line in content.split("\n"):
            if not line.startswith("#") and line != "":
                clean_content += line + "\n"

        graph = load_graph(clean_content)
        new_content = graph.serialize(format=output_format, canon=True)

    changed = content != new_content
    return new_content, changed


def _format_file(
    file: Path,
    check: bool = False,
    output_format: RDF_FILE_SUFFIXES.keys() = "longturtle",
    output_filename: Path = None,
) -> bool:
    """Inner format function - not to be used directly"""
    if not file.is_file():
        raise ValueError(f"{file} is not a file.")

    if file.suffix not in RDF_FILE_SUFFIXES.values():
        raise ValueError(
            f"File {file} is not a RDF file. Must have one of the following suffixes: {RDF_FILE_SUFFIXES.values()}"
        )

    path = Path(file).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path.absolute()}")

    if output_filename is None:
        output_filename = path.with_suffix(RDF_FILE_SUFFIXES[output_format])

    Path(output_filename).touch(exist_ok=True)

    with open(path, "r", encoding="utf-8") as fread:
        content = fread.read()

        content, changed = do_format(content, output_format)
        if check:
            raise FailOnChangeError(
                f"The file {path} contains changes that can be formatted."
            )
        else:
            # Didn't fail and file has changed, so write to file.
            with open(output_filename, "w", encoding="utf-8") as fwrite:
                fwrite.write(content)

    return changed


def reformat(
    path: Path,
    check: bool,
    output_format: RDF_FILE_SUFFIXES.keys() = "longturtle",
    output_filename: Path = None,
) -> None:
    """Reformats a file or all files in a given path according to the output format"""
    path = Path(path).resolve()

    if path.is_dir():
        if output_filename is not None:
            raise ValueError(
                "You cannot specify an output filename if converting multiple files"
            )

        types = [f"**/*{ft}" for ft in RDF_FILE_SUFFIXES.values()]
        files = list(
            itertools.chain.from_iterable(path.glob(pattern) for pattern in types)
        )

        changed_files = []

        for file in files:
            try:
                changed = _format_file(
                    file,
                    check,
                    output_format=output_format,
                    output_filename=output_filename,
                )
                if changed:
                    changed_files.append(file)
            except FailOnChangeError as err:
                print(err)
                changed_files.append(file)

        if check and changed_files:
            if changed_files:
                raise FailOnChangeError(
                    f"{len(changed_files)} out of {len(files)} files will change."
                )
            else:
                print(
                    f"{len(changed_files)} out of {len(files)} files will change.",
                )
        else:
            print(
                f"{len(changed_files)} out of {len(files)} files changed.",
            )
    else:
        try:
            _format_file(
                path,
                check,
                output_format=output_format,
                output_filename=output_filename,
            )
        except FailOnChangeError as err:
            print(err)


def make_dataset(
    path_str_or_graph: Union[Path, str, Graph], graph_iri: Union[str, URIRef]
) -> Dataset:
    """Returns a given Graph, or string or file of triples, as a Dataset, with the supplied graph IRI"""

    # TODO: make a Dataset from a Graph or Datatset
    # - override option to replace existing graph
    # - set default union graph
    # - set default graph
    if not isinstance(graph_iri, URIRef):
        graph_iri = URIRef(graph_iri)

    g = load_graph(path_str_or_graph)

    d = Dataset()
    for s, p, o in g:
        d.add((s, p, o, graph_iri))

    return d


def hierarchy(
    path_str_or_graph: Union[Path, str, Graph],
    graph_iri: Optional[Union[str, URIRef]] = None,
    use_names: bool = False,
) -> None:
    """Print the class, property and concept hierarchies in an RDF graph.

    ``path_str_or_graph`` may be an RDF file, serialized RDF, or an RDFLib
    graph. ``graph_iri`` selects one named graph and is only valid for a remote
    URL or a ``.trig``/``.jsonld`` file. Without it, the source is parsed as a
    context-less graph. Resources are displayed as namespace-qualified names
    when possible. If ``use_names`` is true, names are selected in order from
    ``skos:prefLabel``, ``dcterms:title``, ``schema:name`` and ``rdfs:label``,
    with IRIs used as a fallback. Separate hierarchy roots (and separate
    hierarchy kinds) are divided by a blank line.
    """
    is_remote = isinstance(path_str_or_graph, str) and path_str_or_graph.startswith(
        "http"
    )
    is_named_graph_file = isinstance(path_str_or_graph, Path) and (
        path_str_or_graph.suffix.lower() in {".trig", ".jsonld"}
    )

    if graph_iri is not None:
        if not (is_remote or is_named_graph_file):
            raise ValueError(
                "graph_iri is only allowed for a remote HTTP source or a "
                ".trig/.jsonld file"
            )
        if not isinstance(graph_iri, URIRef):
            graph_iri = URIRef(graph_iri)
        dataset = _parse_dataset(path_str_or_graph)
        graph = dataset.graph(graph_iri)
    elif isinstance(path_str_or_graph, Graph):
        graph = Graph()
        for prefix, namespace in path_str_or_graph.namespaces():
            graph.bind(prefix, namespace)
        for triple in path_str_or_graph:
            graph.add(triple)
    elif isinstance(path_str_or_graph, Path):
        graph = Graph().parse(path_str_or_graph)
    else:
        graph = load_graph(path_str_or_graph)

    class_types = {OWL.Class, RDFS.Class}
    property_types = {
        RDF.Property,
        URIRef(f"{RDFS}Property"),
        OWL.ObjectProperty,
        OWL.DatatypeProperty,
        OWL.AnnotationProperty,
        OWL.FunctionalProperty,
        OWL.InverseFunctionalProperty,
        OWL.SymmetricProperty,
        OWL.TransitiveProperty,
    }

    def typed_resources(types: set[URIRef]) -> set:
        return {subject for rdf_type in types for subject in graph.subjects(RDF.type, rdf_type)}

    def display_name(resource) -> str:
        if use_names:
            name_predicates = (
                SKOS.prefLabel,
                DCTERMS.title,
                URIRef("https://schema.org/name"),
                RDFS.label,
            )
            for predicate in name_predicates:
                values = sorted(graph.objects(resource, predicate), key=str)
                if values:
                    return str(values[0])
        if isinstance(resource, URIRef):
            try:
                return graph.namespace_manager.normalizeUri(resource)
            except Exception:  # RDFLib may reject an IRI it cannot compact.
                return f"<{resource}>"
        return resource.n3(graph.namespace_manager)

    def forests(
        nodes: set,
        predicates: tuple[URIRef, ...],
        inverse=(),
        root_links: tuple[URIRef, ...] = (),
        inverse_root_links: tuple[URIRef, ...] = (),
        membership_predicate: Optional[URIRef] = None,
        container_roots: set = frozenset(),
    ) -> list[str]:
        children = {node: set() for node in nodes}
        parents = {node: set() for node in nodes}

        def add_edge(parent, child) -> None:
            if parent in nodes and child in nodes:
                children[parent].add(child)
                parents[child].add(parent)

        for predicate in predicates:
            for child, parent in graph.subject_objects(predicate):
                add_edge(parent, child)
        for predicate in inverse:
            for parent, child in graph.subject_objects(predicate):
                add_edge(parent, child)
        for predicate in root_links:
            for child, parent in graph.subject_objects(predicate):
                add_edge(parent, child)
        for predicate in inverse_root_links:
            for parent, child in graph.subject_objects(predicate):
                add_edge(parent, child)

        if membership_predicate is not None:
            for child, parent in graph.subject_objects(membership_predicate):
                # inScheme expresses membership, not a direct hierarchy edge.
                # Attach only concepts that do not already have a broader
                # concept or an explicit top-concept relationship.
                if child in nodes and not parents[child]:
                    add_edge(parent, child)

        # Ontologies do not have a standard predicate linking them to every
        # declared class or property. Likewise, some SKOS sources omit
        # inScheme/top-concept links. When there is one unambiguous container,
        # place all otherwise top-level resources beneath it.
        if len(container_roots) == 1:
            container = next(iter(container_roots))
            for node in sorted(nodes - container_roots, key=display_name):
                if not parents[node]:
                    add_edge(container, node)

        visited = set()
        active = []
        active_set = set()

        def check_for_cycle(node) -> None:
            if node in active_set:
                cycle_start = active.index(node)
                cycle = active[cycle_start:] + [node]
                raise ValueError(
                    "Cycle detected in hierarchy: "
                    + " -> ".join(display_name(item) for item in cycle)
                )
            if node in visited:
                return
            active.append(node)
            active_set.add(node)
            for child in sorted(children[node], key=display_name):
                check_for_cycle(child)
            active.pop()
            active_set.remove(node)
            visited.add(node)

        for node in sorted(nodes, key=display_name):
            check_for_cycle(node)

        connected = {node for node in nodes if children[node] or parents[node]}
        roots = sorted(
            (node for node in connected if not parents[node]), key=display_name
        )
        covered = set()
        output = []

        def render(node, prefix="", connector=""):
            output.append(f"{prefix}{connector}{display_name(node)}")
            covered.add(node)
            descendants = sorted(children[node], key=display_name)
            for index, child in enumerate(descendants):
                last = index == len(descendants) - 1
                render(
                    child,
                    prefix + ("    " if connector == "└── " else "│   " if connector else ""),
                    "└── " if last else "├── ",
                )

        for root in roots:
            if output:
                output.append("")
            render(root)

        # This also covers a component reached from an already-rendered node in
        # a hierarchy where a resource has more than one parent.
        for node in sorted(connected - covered, key=display_name):
            if node in covered:
                continue
            if output:
                output.append("")
            render(node)
        return output

    sections = []
    ontologies = typed_resources({OWL.Ontology})
    class_lines = forests(
        typed_resources(class_types) | ontologies,
        (RDFS.subClassOf,),
        container_roots=ontologies,
    )
    if class_lines:
        sections.append("\n".join(class_lines))
    property_lines = forests(
        typed_resources(property_types) | ontologies,
        (RDFS.subPropertyOf,),
        container_roots=ontologies,
    )
    if property_lines:
        sections.append("\n".join(property_lines))
    concepts = typed_resources({SKOS.Concept})
    concept_schemes = typed_resources({SKOS.ConceptScheme})
    concept_lines = forests(
        concepts | concept_schemes,
        (SKOS.broader,),
        (SKOS.narrower,),
        root_links=(SKOS.topConceptOf,),
        inverse_root_links=(SKOS.hasTopConcept,),
        membership_predicate=SKOS.inScheme,
        container_roots=concept_schemes,
    )
    if concept_lines:
        sections.append("\n".join(concept_lines))

    if sections:
        print("\n\n".join(sections))


def export_quads(
    path_str_or_dataset: Union[Path, str, Dataset], destination: Optional[Path] = None
) -> bool | str:
    """Exports a given Dataset, or quads in trig format or a quads file specified by a path, either as
    quads to a string, if no destination is given, or a file, if one is"""
    if isinstance(path_str_or_dataset, Path):
        d = _parse_dataset(path_str_or_dataset)
    elif isinstance(path_str_or_dataset, str):
        d = _parse_dataset(data=path_str_or_dataset, format="trig")
    else:  # Dataset
        d = path_str_or_dataset

    if destination is not None:
        if Path(destination).is_file():
            d2 = _parse_dataset(destination)
            d3 = d + d2
            _serialize_dataset(d3, destination=destination)
        else:
            _serialize_dataset(d, destination=destination)

        return True
    else:
        return _serialize_dataset(d)
