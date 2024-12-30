from pathlib import Path

__version__ = [v for v in open(Path(__file__).parent.parent.resolve() / "pyproject.toml").readlines() if v.startswith("version")][0].split('"')[1]