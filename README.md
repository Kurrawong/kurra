![](/docs/assets/kurra-logo.svg)

# Kurra

A Python package of RDF data manipulation and data management functions that can be called from the command line or
other software.

## Documentation

For Installation, Use and all of kurra's capabilities, see the documentation: <https://kurrawong.github.io/kurra/>.

## Developing

This project uses [`uv`](https://docs.astral.sh/uv/) as it's package manager and many comon development tasks can be 
run from the [Taskfile.yml](https://taskfile.dev/) task runner.

The documentation is [Zensical](https://zensical.org/), the updated version of [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

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
