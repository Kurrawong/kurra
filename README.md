# Kurra

A Python package of RDF data manipulation and data management functions that can be called from the command line or
other software.

This library uses the [RDFLib](https://pypi.org/project/rdflib/) under-the-hood to process
[RDF](https://www.w3.org/RDF/) data. It supplies functions to:

* manipulate local RDF files
* send commands to RDF databases "triplestores"
* SPARQL query files or databases
* SHACL validate or apply rules to RDF data

kurra is for convenience: the functions it provides are simple but kurra saves you having to reinvent wheels.

## CLI app

kurra presents a Command Line Interface that can be used on Mac, Linux and Windows (WSL) command prompts.

Once you have installed kurra (see below), you can ask it to tell you what commands it supports 
by using the `--help` or just `-h`, command, e.g.:

```bash
kurra -h
```

which will return something like:

```
╭─ Options ─────────────────────────────────────────────────────────────────────────────────╮
│ --version             -v                                                                  │
│ --help                -h        Show this message and exit.                               │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────────────────────────╮
│ db       RDF database commands                                                            │
│ file     RDF file commands                                                                │
│ shacl    SHACL commands                                                                   │
│ sparql   SPARQL queries to local RDF files or a database                                  │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
```

To find out more about the specific options within `db`, `file`, `shacl` & `sparql`, run the help command at the next
level, like this:

```bash
kurra db -h
```

or

```bash
kurra file -h
```

etc. for `shacl` & `sparql`

To get further help for the particular commands. For `db`, you will see something like this:

```bash
 Usage: kurra db [OPTIONS] COMMAND [ARGS]...
                                
 RDF database commands
 
╭─ Options ─────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                 │
╰───────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────────────╮
│ sparql   SPARQL query an RDF database                                         │
│ fuseki   Fuseki database commands                                             │
│ gsp      Graph Store Protocol commands                                        │
│ olis     Olis commands                                                        │
╰───────────────────────────────────────────────────────────────────────────────╯
```

## Installation

### CLI App

The recommended way to manage and run Python CLI apps is to use the Python package uv which you will need to install
first, see the [uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/). then:

```bash
uv tool install kurra
```

Now you can invoke `kurra` anywhere in your terminal as long as `~/.local/bin` is in your `PATH`.

See the uv documentation on [installing tools](https://docs.astral.sh/uv/guides/tools/#installing-tools) for more
information.

### Library

You can also install `kurra` as a Python library for used of its functions in other applications

```bash
pip install kurra
```

Use the relevant command to add dependencies to your project if you are using a tool like uv, poetry, or conda.

Then import it and use in your code, e.g. for the format functions:

```python
from kurra.file import reformat, make_dataset, export_quads
```

## Development

Install the Poetry project and its dependencies:

```bash
task install
```

Format code:

```bash
task format
```

Test:

```
task test
```

You can test the command like app while in development with:

```
uv tool kurra {COMMANDS}
```

With `{COMMANDS}` as per the usual kurra CLI.

### Releasing

To build a new release:

* format code: `task format`
* pass tests: `task test`
* update version in pyproject.toml
* Git commit & push all updates
* Git tag with release version
  * `git tag 2.2.4`
  * `git push --tags`
* make GitHub release
  * this will trigger pypi.yml workflow to publish to PyPI
* update version in pyproject.toml to next release alpha and push
  * with message `2.2.4 post release`

## License

[BSD-3-Clause](https://opensource.org/license/bsd-3-clause/) license. See [LICENSE](LICENSE).

## Contact & Support

kurra is maintained by:

**KurrawongAI**  
<http://kurrawong.ai>  
<info@kurrawong.ai>

Please contact them for all use & support issues.

You can also log issues at the kurra issue tracker:

* <https://github.com/Kurrawong/kurra/issues>
