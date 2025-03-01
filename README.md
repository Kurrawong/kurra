# Kurra Python Library

A Python package of RDF data manipulation functions that can be called from the command line or other software.

This library uses the [RDFLib](https://pypi.org/project/rdflib/) under-the-hood to process 
[RDF](https://www.w3.org/RDF/) data. It supplies functions to:

* manipulate local RDF files
* send commands to RDF databases "triplestores"
* SPARQL query files or databases

kurra is for convenience: the functions it provides are simple but kurra saves you having to reinvent wheels.


## CLI app

kurra presents a Command Line Interface that can be used on Mac, Linux and Windows (WSL) command prompts. 

The hierarchy of functions provided is:

* **db** - run commands against RDF databases
  * list
  * create
  * upload
  * clear
  * delete
  * sparql
* **file** - run commands on local RDF files
  * format
  * upload
  * quads
  * sparql
* **shacl**
  * validate - SHACL validate a file
* **sparql** - SPARQL query files or databases

Once you have installed kurra (see below), you can ask it to tell you what each command does and what inputs are needed by using the `--help` or just `-h`, command, e.g.:

```bash
kurra -h
```

which will return something like:

```
╭─ Options ─────────────────────────────────────────────────────────────────────────────────╮
│ --version             -v                                                                  │
│ --install-completion            Install completion for the current shell.                 │
│ --show-completion               Show completion for the current shell, to copy it or ...  │
│ --help                -h        Show this message and exit.                               │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────────────────────────╮
│ db       RDF database commands                                                            │
│ file     RDF file commands                                                                │
│ sparql   SPARQL queries to local RDF files or a database                                  │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
```

To find out more about the specific options within `db`, `file` & `sparql`, run the help command at the lext level, like this:

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
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                                 │
╰───────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────────────────────────────╮
│ list     Get the list of database repositories                                                │
│ create   Create a new database repository                                                     │
│ upload   Upload files to a database repository                                                │
│ clear    Clear a database repository                                                          │
│ delete   Delete a database repository                                                         │
│ sparql   Query a database repository                                                          │
╰───────────────────────────────────────────────────────────────────────────────────────────────╯
```


## Installation

### CLI App

The recommended way to manage and run Python CLI apps is to use the Python package uv which you will need to install first, see the [uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/). then:

```bash
uv tool install kurra
```

Now you can invoke `kurra` anywhere in your terminal as long as `~/.local/bin` is in your `PATH`.

See the uv documentation on [installing tools](https://docs.astral.sh/uv/guides/tools/#installing-tools) for more information.

### Library

You can also install `kurra` as a Python library for used of its functions in other applications

```bash
pip install kurra
```

Use the relevant command to add dependencies to your project if you are using a tool like uv, poetry, or conda.

Then import it and use in your code, e.g. for the format functions:

```python
from kurra.file import format_file, make_dataset, export_quads
```

## Development

Install the Poetry project and its dependencies:

```bash
task install
```

Format code:

```bash
task code
```

To build a new release:

1. update the version in pyproject.toml
2. commit & push all changes
3. git tag with the same version number
4. push the tag - `git push --tags`
5. build the release - `uv build`
6. publish the release on PyPI - `uv publish` - username `__token__`, pwd is an actual token
7. make the release on GitHub - https://github.com/Kurrawong/kurra/releases
  * don't forget to add the dist zips & wheels to it
8. update version number in pyproject.toml to next alpha & push

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
