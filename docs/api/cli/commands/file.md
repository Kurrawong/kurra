# File commands

## Reformatting with context and indentation

`kurra file reformat` accepts `--context` (short flag `-t`) as inline JSON or a path to a UTF-8 JSON context file.
The value must contain a valid JSON-LD context, either wrapped in `@context` or as a bare mapping. Invalid contexts
produce a CLI error before output files are written. When the input is a directory, the context applies to every RDF file.

For Turtle and N3 output, the context's namespace prefixes are used to shorten IRIs. This example adds the `ex` prefix
to the default `longturtle` output, allowing `https://example.org/alice` to be written as `ex:alice`:

```sh
kurra file reformat input.ttl -o prefixed.ttl -t '{"@context": {"ex": "https://example.org/"}}'
```

For JSON-LD output, the context is passed to PyLD's `compact()`. Use a context file and `--indent` to choose the number
of spaces for indentation (default `4`, minimum `0`):

```sh
kurra file reformat input.ttl -f json-ld -o compacted.jsonld --context context.jsonld --indent 2
```

For example, `context.jsonld` can contain:

```json
{
    "@context": {
        "ex": "https://example.org/",
        "name": "https://example.org/name"
    }
}
```

`--indent` only affects JSON-LD output when `--context` is supplied.

::: kurra.cli.commands.file

