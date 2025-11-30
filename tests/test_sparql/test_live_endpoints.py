from kurra.sparql import query


def test_gswa():
    # this ednpoint doesn't allow POST and replies with 405
    SPARQL_ENDPOINT = "https://api.vocabulary.gswa.kurrawong.ai/sparql"

    q = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT *
    WHERE {
        ?s a skos:Concept
    } LIMIT 10
    """

    r = query(SPARQL_ENDPOINT, q, return_format="python", return_bindings_only=True)
    assert len(r) == 10


def test_idn():
    # this ednpoint doesn't allow POST and replies with 422
    SPARQL_ENDPOINT = "https://api.idnau.org/sparql"

    q = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT *
    WHERE {
        ?s a skos:Concept
    } LIMIT 10
    """

    r = query(SPARQL_ENDPOINT, q, return_format="python", return_bindings_only=True)
    assert len(r) == 10
