![](/docs/assets/kurra-logo.svg)

# kurra

A Python package of RDF data manipulation and data management functions that can be called from the command line or
other software.

## Documentation

For Installation, Use and all of kurra's capabilities, see the documentation: <https://kurrawong.github.io/kurra/>.

## Developing

This project uses [`uv`](https://docs.astral.sh/uv/) as it's package manager and many comon development tasks can be 
run from the [Taskfile.yml](https://taskfile.dev/) task runner.

The documentation is [Zensical](https://zensical.org/), the updated version of [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

### SHACL speed regression test

On the benchmark machine, with the VocPub validator already cached (run `kurra shacl syncv` if needed), run:

```sh
uv sync --extra rudof
KURRA_MINERALS_TTL=/path/to/minerals.ttl uv run --extra rudof pytest -q -s tests/shacl/test_shacl_speed.py
```

The test checks the median of three default-report validations against the measured baselines: 8.42 s for pySHACL
and 1.30 s for Rudof. It allows 5% for run-to-run timing variation. Timing depends on the machine and the cached
validator. The test is skipped unless
`KURRA_MINERALS_TTL` is set.

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
  * be sure to add some release notes
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
