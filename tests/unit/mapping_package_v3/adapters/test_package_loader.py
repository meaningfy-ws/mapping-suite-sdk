from pathlib import Path

import pytest

from mapping_suite_sdk.mapping_package_v3.adapters.package_loader import MappingPackageV3Loader
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3


def test_mp_v3_loader_loads_with_success(dummy_mapping_package_v3_path: Path) -> None:
    loader = MappingPackageV3Loader()
    mapping_package: MappingPackageV3 = loader.load(dummy_mapping_package_v3_path)

    assert hasattr(mapping_package, 'metadata')
    assert hasattr(mapping_package, 'conceptual_mapping_asset')
    assert hasattr(mapping_package, 'technical_mapping_suite')
    assert hasattr(mapping_package, 'vocabulary_mapping_suite')
    assert hasattr(mapping_package, 'test_data_suites')
    assert hasattr(mapping_package, 'test_suites_sparql')
    assert hasattr(mapping_package, 'test_suites_shacl')
    assert hasattr(mapping_package, 'test_results')


def test_mp_v3_loader_fails_on_wrong_path() -> None:
    loader = MappingPackageV3Loader()

    with pytest.raises(FileNotFoundError):
        loader.load(Path("/nonexistent/path"))


def test_mp_v3_loader_initialization_default_values() -> None:
    loader = MappingPackageV3Loader()

    assert loader.include_test_data is True
    assert loader.include_output is True


def test_mp_v3_loader_initialization_custom_values() -> None:
    loader = MappingPackageV3Loader(include_test_data=False, include_output=False)

    assert loader.include_test_data is False
    assert loader.include_output is False


def test_mp_v3_loader_equality() -> None:
    loader1 = MappingPackageV3Loader(include_test_data=True, include_output=True)
    loader2 = MappingPackageV3Loader(include_test_data=True, include_output=True)
    loader3 = MappingPackageV3Loader(include_test_data=False, include_output=True)

    assert loader1 == loader2
    assert loader1 != loader3
    assert loader1 != "not a loader"
