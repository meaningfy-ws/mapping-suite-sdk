"""Runtime dependencies and extras are only what the code imports, as ranges (package-distribution spec)."""

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


def _requirements() -> list[tuple[str, str, str | None]]:
    """(distribution, version specifier, extra or None) from the installed package metadata."""
    result = []
    for requirement in requires("mapping-suite-sdk") or []:
        name, specifier = re.match(r"([A-Za-z0-9_.\-]+)\s*\(?([^;)]*)", requirement).groups()
        extra = re.search(r'extra == "([^"]+)"', requirement)
        result.append((name.lower(), specifier.strip(), extra.group(1) if extra else None))
    return result


def _extras() -> dict[str, set[str]]:
    extras: dict[str, set[str]] = {}
    for name, _, extra in _requirements():
        if extra:
            extras.setdefault(extra, set()).add(name)
    return extras


def _imported_top_level_modules() -> set[str]:
    modules = set()
    for path in Path(mapping_suite_sdk.__file__).parent.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                modules.add(node.module.split(".")[0])
            elif (  # optional libraries are imported at the point of use through require("<module>", ...)
                isinstance(node, ast.Call)
                and getattr(node.func, "id", None) == "require"
                and node.args
                and isinstance(node.args[0], ast.Constant)
            ):
                modules.add(node.args[0].value.split(".")[0])
    return modules


def test_core_depends_on_pydantic_only():
    assert [name for name, _, extra in _requirements() if extra is None] == ["pydantic"]


def test_extras_map_to_integrations():
    extras = _extras()
    integrations = {
        "mongodb": {"pymongo"},
        "github": {"gitpython"},
        "tracing": {"opentelemetry-api", "opentelemetry-sdk"},
        "cli": {"typer"},
    }
    assert {name: extras.get(name) for name in integrations} == integrations
    assert extras["all"] == set().union(*integrations.values())


def test_every_declared_dependency_is_imported():
    declared = {name for name, _, _ in _requirements()}
    assert declared == set(DISTRIBUTION_TO_IMPORT), "update DISTRIBUTION_TO_IMPORT with the new dependency"
    imported = _imported_top_level_modules()
    assert {name for name in declared if DISTRIBUTION_TO_IMPORT[name] not in imported} == set()


def test_no_dependency_is_pinned_and_each_has_an_upper_bound():
    for name, specifier, _ in _requirements():
        assert "==" not in specifier, name
        assert "<" in specifier, name
