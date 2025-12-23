# OLIS API

from rdflib import URIRef
from rdflib.namespace import DefinedNamespace, Namespace

OLIS = Namespace("https://olis.dev/")


class OLIS_GRAPH_ROLES(DefinedNamespace):
    _NS = Namespace("http://olis.dev/GraphRoles/")
    _fail = True

    Original: URIRef
    Inferred: URIRef
    Added: URIRef
    Removed: URIRef
