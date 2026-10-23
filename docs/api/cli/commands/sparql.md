# SPARQL commands

## Validate syntax

```shell
kurra sparql validate 'SELECT * WHERE { ?s ?p ?o }'
kurra sparql validate 'INSERT DATA { <urn:s> <urn:p> <urn:o> }'
kurra sparql validate query.sparql
```

The required positional argument `q` accepts SPARQL text or a path to a file containing a query or update, just like
`q` in `kurra sparql <path-or-url> <q>`. Quote inline SPARQL text so the shell passes it as one argument.

Successful validation prints `Valid SPARQL syntax` and exits with status `0`. Invalid syntax produces an error with
the line and column and exits with a nonzero status. The command checks syntax without executing the statement or
contacting an endpoint.

## Run queries and updates

The existing invocation remains supported:

```shell
kurra sparql data.ttl 'SELECT * WHERE { ?s ?p ?o }'
```

An explicit `query` subcommand is also available:

```shell
kurra sparql query data.ttl 'SELECT * WHERE { ?s ?p ?o }'
```

Use `kurra sparql --help`, `kurra sparql query --help`, or `kurra sparql validate --help` for command help.

## Command reference

::: kurra.cli.commands.sparql
