"""Runtime dependencies are only what the code imports, as ranges (package-distribution spec)."""

import ast
import re
from importlib.metadata import requires
from pathlib import Path

import mapping_suite_sdk

DISTRIBUTION_TO_IMPORT = {
    "gitpython": "git",
    "opentelemetry-api": "opentelemetry",
    "opentelemetry-sdk": "opentelemetry",
    "pydantic": "pydantic",
    "pymongo": "pymongo",
    "typer": "typer",
}


def _runtime_requirements() -> dict[str, str]:
    """Distribution name -> version specifier, from the installed package metadata."""
    result = {}
    for requirement in requires("mapping-suite-sdk") or []:
        if "extra ==" in requirement:
            continue
        name, specifier = re.match(r"([A-Za-z0-9_.\-]+)\s*\(?([^;)]*)", requirement).groups()
        result[name.lower()] = specifier.strip()
    return result


def _imported_top_level_modules() -> set[str]:
    modules = set()
    for path in Path(mapping_suite_sdk.__file__).parent.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                modules.add(node.module.split(".")[0])
    return modules


def test_every_runtime_dependency_is_imported():
    requirements = _runtime_requirements()
    assert set(requirements) == set(DISTRIBUTION_TO_IMPORT), "update DISTRIBUTION_TO_IMPORT with the new dependency"
    imported = _imported_top_level_modules()
    unused = {name for name in requirements if DISTRIBUTION_TO_IMPORT[name] not in imported}
    assert not unused


def test_no_runtime_dependency_is_pinned_and_each_has_an_upper_bound():
    for name, specifier in _runtime_requirements().items():
        assert "==" not in specifier, name
        assert "<" in specifier, name
