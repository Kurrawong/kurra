# SPARQL

## Validate query and update syntax

Use `kurra.sparql.validate(q)` to check SPARQL syntax without executing a query or update. The `q` argument accepts
SPARQL text, a `pathlib.Path`, or a string containing a file path, matching the query input used by `query()`.

```python
from kurra.sparql import validate

validate("SELECT * WHERE { ?s ?p ?o }")
validate("INSERT DATA { <urn:s> <urn:p> <urn:o> }")
validate("query.sparql")
```

The function returns `None` on success. Invalid syntax raises `pyparsing.ParseBaseException`, whose `lineno`, `col`,
and `msg` attributes describe the error. Validation uses RDFLib's `parseQuery()` and, if needed, `parseUpdate()`.
It checks syntax; it does not resolve undeclared prefixes or check endpoint capabilities.

Remote queries and updates are validated before they are sent to an endpoint, after supplied namespaces are added.
Local queries and updates use RDFLib's existing parsing during execution, avoiding an additional validation pass.

## Python reference

::: kurra.sparql
