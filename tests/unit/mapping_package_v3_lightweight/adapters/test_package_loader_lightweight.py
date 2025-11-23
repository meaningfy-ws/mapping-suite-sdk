from pathlib import Path

import pytest

from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_loader import MappingPackageV3LightweightLoader
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight


def test_mp_v3_loader_loads_with_success(dummy_mapping_package_v3_path: Path) -> None:
    loader = MappingPackageV3LightweightLoader()
    mapping_package: MappingPackageV3Lightweight = loader.load(dummy_mapping_package_v3_path)

    assert hasattr(mapping_package, 'metadata')
    assert hasattr(mapping_package, 'technical_mapping_suite')
    assert hasattr(mapping_package, 'vocabulary_mapping_suite')


def test_mp_v3_loader_fails_on_wrong_path() -> None:
    loader = MappingPackageV3LightweightLoader()

    with pytest.raises(FileNotFoundError):
        loader.load(Path("/nonexistent/path"))


def test_mp_v3_loader_initialization_default_values() -> None:
    loader = MappingPackageV3LightweightLoader()

    assert loader.include_test_data is True
    assert loader.include_output is True


def test_mp_v3_loader_initialization_custom_values() -> None:
    loader = MappingPackageV3LightweightLoader(include_test_data=False, include_output=False)

    assert loader.include_test_data is False
    assert loader.include_output is False


def test_mp_v3_loader_equality() -> None:
    loader1 = MappingPackageV3LightweightLoader(include_test_data=True, include_output=True)
    loader2 = MappingPackageV3LightweightLoader(include_test_data=True, include_output=True)
    loader3 = MappingPackageV3LightweightLoader(include_test_data=False, include_output=True)

    assert loader1 == loader2
    assert loader1 != loader3
    assert loader1 != "not a loader"
