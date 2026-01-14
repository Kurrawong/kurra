# OLIS API

from rdflib import URIRef, Graph, Dataset, Literal
from rdflib.namespace import DefinedNamespace, Namespace, RDF, SDO, XSD
from datetime import datetime
import httpx
from pathlib import Path
from rdflib.plugins.parsers.notation3 import BadSyntax
import kurra.db.gsp
from kurra.utils import load_graph, get_system_graph, put_system_graph

OLIS = Namespace("https://olis.dev/")
SYSTEM_GRAPH_IRI = URIRef("https://olis.dev/SystemGraph")
BACKGROUND_GRAPH_IRI = URIRef("http://background")


class OLIS(DefinedNamespace):
    _NS = Namespace("https://olis.dev/")
    _fail = True

    RealGraph: URIRef
    VirtualGraph: URIRef

    includes: URIRef
    hasBaseGRaph: URIRef
    hasGraphRole: URIRef


class OLIS_GRAPH_ROLES(DefinedNamespace):
    _NS = Namespace("http://olis.dev/GraphRoles/")
    _fail = True

    Original: URIRef
    Inferred: URIRef
    Added: URIRef
    Removed: URIRef


class OLIS_GRAPH_ACTIONS(DefinedNamespace):
    _NS = Namespace("http://olis.dev/GraphActions/")
    _fail = True

    Original: URIRef
    Inferred: URIRef
    Added: URIRef
    Removed: URIRef


def include(
        including_graph_iri: URIRef|str,
        graphs_to_include_iris: list[URIRef|str],
        system_graph_source: str | Path | Dataset | Graph = None,
        include_background_graph: bool = True,
        http_client: httpx.Client | None = None,
)->Graph|None:
    """Creates a Virtual Graph with IRI of subsuming_graph_iri that contains all the graphs given in graph_iris.

    Args:
        including_graph_iri: the IRI of the graph that will include the other graphs
        graphs_to_include_iris: the IRIs of each graph to be included in the including graph
        system_graph_source: the SPARQL Endpoint, file (RDFLib Graph or Dataset) or an RDFLib Graph or Dataset object to both read and write System Graph info to. If None, a new System Graph object will be returned
        include_background_graph: whether to include http://background in the subsumption
        http_client: an optional HTTPX Client to contain credentials if needed to access the SPARQL Endpoint

    Returns:
        If a system_graph_target is given, the updates System Graph information will be written to it or a
        new System Graph, RDFLib Graph object will be returned

    """
    if including_graph_iri is None:
        raise ValueError("You must specify an including_graph_iri as a string or a URIRef")

    if graphs_to_include_iris is None:
        raise ValueError("You must specify at least one string or URIRef in the list variable graphs_to_include_iris")

    if isinstance(including_graph_iri, str):
        including_graph_iri = URIRef(including_graph_iri)

    if isinstance(graphs_to_include_iris[0], str):
        graphs_to_include_iris = [URIRef(x) for x in graphs_to_include_iris]

    """
    To extend http://graph-a to include graph-a content and http://graph-b content:
    
    include_graph("http://graph-a", ["http://graph-b"])
    
    This will:
    
    * learn that http://graph-a is a Virtual Graph - since it includes things
    * move any existing http://graph-a content, if it's a Real Graph, to a new Real Graph - http://graph-a-real - by convention
    * state that http://graph-a includes http://graph-a-real and all graphs in the graphs_to_include_iris list 
    """
    system_graph = get_system_graph(system_graph_source, http_client=http_client)

    """
    if including_graph_iri in system_graph:
        if it is an RG:
            pop out RG content and include
    else:
        create it
        
    include all graphs_to_include_iris
    """
    if (including_graph_iri, RDF.type, OLIS.RealGraph) in system_graph:
        # swap out all triples targeting the RG to the new RG
        new_including_graph_real_iri = URIRef(str(including_graph_iri) + "-real")

        for p, o in system_graph.subject_objects(including_graph_iri):
            system_graph.remove((including_graph_iri, p, o))
            system_graph.add((new_including_graph_real_iri, p, o))

        for s, p in system_graph.subject_predicates(including_graph_iri):
            system_graph.remove((s, including_graph_iri, p))
            system_graph.add((s, new_including_graph_real_iri, p))

        # create the new VG
        system_graph.add((including_graph_iri, RDF.type, OLIS.VirtualGraph))

        # include the new RG in the VG
        system_graph.add((including_graph_iri, OLIS.includes, new_including_graph_real_iri))
        system_graph.add((new_including_graph_real_iri, RDF.type, OLIS.RealGraph))
        system_graph.add((new_including_graph_real_iri, SDO.description, Literal(f"Graph containing triples from <{str(including_graph_iri)}>")))
    elif (including_graph_iri, RDF.type, OLIS.VirtualGraph) in system_graph:
        pass  # we will add to the VG below
    else:  # the including_graph_iri is not present in the system_graph so create it
        system_graph.add((including_graph_iri, RDF.type, OLIS.VirtualGraph))
        system_graph.add((including_graph_iri, SDO.dateCreated, Literal(datetime.now().isoformat()[:19], datatype=XSD.dateTime)))

    # in all cases now...
    for graph_to_include_iri in graphs_to_include_iris:
        system_graph.add((including_graph_iri, OLIS.includes, graph_to_include_iri))

    system_graph.remove((including_graph_iri, SDO.dateModified, None))
    system_graph.add((including_graph_iri, SDO.dateModified, Literal(datetime.now().isoformat()[:19], datatype=XSD.dateTime)))

    if include_background_graph:
        system_graph.add((including_graph_iri, OLIS.includes, BACKGROUND_GRAPH_IRI))

    # write System Graph to remote system graph or return System Graph object
    return put_system_graph(system_graph, system_graph_source, http_client=http_client)


def exclude(
        including_graph_iri: URIRef | str,
        graphs_to_exclude_iris: list[URIRef | str],
        system_graph_source: str | Path | Dataset | Graph = None,
        http_client: httpx.Client | None = None,
):
    """
        including_graph_iri: str,
        graphs_to_exclude_iris: list[str],
        include_background_graph: bool = True,
        sparql_endpoint: str = None,
        http_client: httpx.Client | None = None,
        write_to_endpoint: bool = True,
    """
    if including_graph_iri is None:
        raise ValueError("You must specify an including_graph_iri as a string or a URIRef")

    if graphs_to_exclude_iris is None:
        raise ValueError("You must specify at least one string or URIRef in the list variable graphs_to_include_iris")

    if isinstance(including_graph_iri, str):
        including_graph_iri = URIRef(including_graph_iri)

    if isinstance(graphs_to_exclude_iris[0], str):
        graphs_to_exclude_iris = [URIRef(x) for x in graphs_to_exclude_iris]

    system_graph = get_system_graph(system_graph_source, http_client=http_client)

    if not (including_graph_iri, RDF.type, OLIS.VirtualGraph) in system_graph:
        return ValueError("The including_graph_iri is not known as a VirtualGraph in the system_graph_source")

    system_graph.remove((including_graph_iri, SDO.dateModified, None))
    system_graph.add((including_graph_iri, SDO.dateModified, Literal(datetime.now().isoformat()[:19], datatype=XSD.dateTime)))

    for graph_to_exclude_iri in graphs_to_exclude_iris:
        system_graph.remove((including_graph_iri, OLIS.includes, graph_to_exclude_iri))

    return put_system_graph(system_graph, system_graph_source, http_client=http_client)