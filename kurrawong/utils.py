def _guess_rdf_data_format(rdf: str):
    if rdf is not None:
        rdf = rdf.strip()
        if rdf.startswith("PREFIX") or rdf.startswith("@prefix"):
            return "text/turtle"
        elif rdf.startswith("{") or rdf.startswith("["):
            return "application/ld+json"
        elif rdf.startswith("<?xml") or rdf.startswith("<rdf"):
            return "application/rdf+xml"
        else:
            return "application/n-triples"
    else:
        return None
