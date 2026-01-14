# OLIS API

from rdflib import URIRef, Graph, Dataset, Literal
from rdflib.namespace import DefinedNamespace, Namespace, RDF, SDO, XSD
from datetime import datetime
import httpx
from pathlib import Path
from rdflib.plugins.parsers.notation3 import BadSyntax
import kurra.db.gsp
from kurra.utils import load_graph

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
        system_graph_target: str | Path | Dataset | Graph = None,
        include_background_graph: bool = True,
        http_client: httpx.Client | None = None,
)->Graph|None:
    """Creates a Virtual Graph with IRI of subsuming_graph_iri that contains all the graphs given in graph_iris.

    Args:
        including_graph_iri: the IRI of the graph that will include the other graphs
        graphs_to_include_iris: the IRIs of each graph to be included in the including graph
        system_graph_target: the SPARQL Endpoint, file (RDFLib Graph or Dataset) or an RDFLib Graph or Dataset object to both read and write System Graph info to. If None, a new System Graph object will be returned
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
    system_graph = Graph(identifier=SYSTEM_GRAPH_IRI)
    system_graph.bind("olis", OLIS)
    if system_graph_target is None:
        # no incoming System Graph
        pass
    elif isinstance(system_graph_target, Path):
        # we have a Graph or Dataset file, so read it
        if not system_graph_target.is_file():
            return ValueError("system_graph_target must be an existing RDF file")

        try:
            system_graph += load_graph(system_graph_target)
            local_dataset = False
        except BadSyntax as e:
            raise e
        except Exception:
            try:
                local_dataset = Dataset().parse(system_graph_target, format="trig")
                system_graph += local_dataset.get_graph(SYSTEM_GRAPH_IRI)

            except BadSyntax as e:
                raise e
            except Exception:
                raise ValueError(
                    "Could not load the given system_graph_target Path as an RDFLib Graph "
                    "or Trig/N-Quads as an RDFLib Dataset")
    elif isinstance(system_graph_target, Graph):
        # we have a Graph, so assume it's a System Graph and load it
        system_graph += system_graph_target
    elif isinstance(system_graph_target, Dataset):
        # we have a Dataset object, so load its system Graph
        system_graph += system_graph_target.get_graph(str(SYSTEM_GRAPH_IRI))
    elif system_graph_target and system_graph_target.startswith("http"):
        # we have a remote SPARQL Endpoint, so read the System Graph
        system_graph = kurra.db.gsp.get(str(system_graph_target), SYSTEM_GRAPH_IRI, http_client=http_client)
    else:
        raise ValueError(
            "The parameter system_graph_target must be either None, a Path to an RDF Graph or Dataset serialised "
            "in Turtle or Trig, an RDFLib Graph object assumed to be a System Graph, an RDFLib Dataset object containing"
            "a System Graph or a string URL for a SPARQL Endpoint.")

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
    if system_graph_target is None:
        return system_graph
    elif isinstance(system_graph_target, Path):
        if not local_dataset:
            system_graph.serialize(destination=system_graph_target, format="longturtle")
        else:
            local_dataset.remove_graph(SYSTEM_GRAPH_IRI)
            local_dataset.add_graph(system_graph)
            local_dataset.serialize(destination=system_graph_target, format="trig")
        return None
    elif isinstance(system_graph_target, Graph):
        system_graph_target = system_graph
        return None
    elif isinstance(system_graph_target, Dataset):
        system_graph_target.remove_graph(SYSTEM_GRAPH_IRI)
        system_graph_target.add_graph(system_graph)
        return None
    elif system_graph_target and system_graph_target.startswith("http"):
        kurra.db.gsp.put(system_graph_target, system_graph, SYSTEM_GRAPH_IRI, http_client=http_client)
        return None
    else:
        return None


def exclude(
        including_graph_iri: URIRef | str,
        graphs_to_exclude_iris: list[URIRef | str],
        system_graph_target: str | Path | Dataset | Graph = None,
        include_background_graph: bool = True,
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
    return NotImplementedError("Coming soon")