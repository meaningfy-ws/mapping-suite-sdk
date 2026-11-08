"""public-api / optional-integrations, on an install with no extras (run by make test-core-only)."""

import importlib.util
import sys

OPTIONAL_LIBRARIES = ["pymongo", "bson", "git", "opentelemetry", "typer", "click"]


def test_no_optional_library_is_installed():
    assert [name for name in OPTIONAL_LIBRARIES if importlib.util.find_spec(name) is not None] == []


def test_import_the_loader_from_the_root():
    from mapping_suite_sdk import load_mapping_package

    assert callable(load_mapping_package)
    assert "pymongo" not in sys.modules


def test_tests_import_the_installed_wheel_not_the_source_tree():
    import mapping_suite_sdk

    assert "site-packages" in mapping_suite_sdk.__file__
