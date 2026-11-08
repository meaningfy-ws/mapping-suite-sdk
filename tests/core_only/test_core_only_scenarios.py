"""optional-integrations and public-api scenarios on an install with no extras (make test-core-only)."""

import logging
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

from mapping_suite_sdk import (
    MappingPackageV3,
    convert_mapping_package,
    load_mapping_package,
    load_mapping_package_from_bytes,
    mapping_package_to_zip_bytes,
    save_mapping_package_to_mongodb,
    validate_mapping_package,
)

V2_PACKAGE = Path(__file__).parents[1] / "test_data" / "mapping_package_v2" / "package_eforms_29_v1.9_changed"


def test_core_only_round_trip():
    package = convert_mapping_package(load_mapping_package(V2_PACKAGE, include_test_data=True))

    assert isinstance(package, MappingPackageV3)
    assert validate_mapping_package(package) is True


def test_mongodb_without_its_extra():
    package = load_mapping_package(V2_PACKAGE)

    with pytest.raises(ImportError, match=r"pip install mapping-suite-sdk\[mongodb\]"):
        save_mapping_package_to_mongodb(package, None, "db")


def test_github_without_its_extra():
    from mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2 import (
        load_mapping_packages_v2_from_github,
    )

    with pytest.raises(ImportError, match=r"pip install mapping-suite-sdk\[github\]"):
        load_mapping_packages_v2_from_github("https://github.com/org/repo", "mappings/*")


def test_mapping_suite_save_without_its_extra():
    from mapping_suite_sdk.mapping_suite.services.save_mapping_suite import save_mapping_suite_to_mongo_db

    with pytest.raises(ImportError, match=r"pip install mapping-suite-sdk\[mongodb\]"):
        save_mapping_suite_to_mongo_db(None, None)


def test_explicit_tracing_setup_without_its_extra():
    from mapping_suite_sdk.core.adapters.tracer import add_span_processor_to_mssdk_tracer_provider

    with pytest.raises(ImportError, match=r"pip install mapping-suite-sdk\[tracing\]"):
        add_span_processor_to_mssdk_tracer_provider(None)


def test_cli_without_its_extra():
    result = subprocess.run([Path(sys.executable).parent / "mssdk", "--help"], capture_output=True, text=True)

    assert result.returncode != 0
    assert "pip install mapping-suite-sdk[cli]" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("trace", ["false", "true"])
def test_load_without_opentelemetry_emits_no_warning(trace, monkeypatch, caplog):
    monkeypatch.setenv("MSSDK_TRACE", trace)
    caplog.set_level(logging.DEBUG)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        package = load_mapping_package(V2_PACKAGE)

    assert package is not None
    assert caught == []
    assert [record for record in caplog.records if record.levelno >= logging.WARNING] == []


def test_model_modules_stay_importable_by_path():
    from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import VersionRange

    assert VersionRange.__name__ == "VersionRange"


def test_in_memory_round_trip_without_extras():
    package = convert_mapping_package(load_mapping_package(V2_PACKAGE, include_test_data=True))

    loaded = load_mapping_package_from_bytes(mapping_package_to_zip_bytes(package))

    assert validate_mapping_package(loaded) is True
