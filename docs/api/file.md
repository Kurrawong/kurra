# File operations

## Reformatting with a JSON-LD context

`reformat()` accepts an optional `context` as a Python dict, a JSON string, or a `pathlib.Path` to a UTF-8 JSON file.
Use either a complete `{"@context": {...}}` statement or a bare context mapping. The context must be valid JSON-LD;
invalid contexts raise `ValueError` before output files are written. A directory input applies the context to every RDF file.

For Turtle (including the default `longturtle`) and N3 output, namespace prefixes from the context are bound to the graph
so serializers can shorten IRIs. For example, supply a prefix mapping when reformatting Turtle:

```python
from pathlib import Path

from kurra.file import reformat

context = {"@context": {"ex": "https://example.org/"}}
reformat(
    Path("input.ttl"),
    check=False,
    output_filename=Path("prefixed.ttl"),
    context=context,
)
```

An IRI such as `https://example.org/alice` can then be written as `ex:alice`, with the corresponding prefix declaration.

For JSON-LD output, PyLD's `compact()` uses the context to compact terms and IRIs. `indent` defaults to `4` spaces and
only affects JSON-LD output when a context is supplied. Load a context from a file and request two-space indentation:

```python
reformat(
    Path("input.ttl"),
    check=False,
    output_format="json-ld",
    output_filename=Path("compacted.jsonld"),
    context=Path("context.jsonld"),
    indent=2,
)
```

Alternatively, pass inline JSON as `context='{"@context": {"ex": "https://example.org/"}}'`.

::: kurra.file

