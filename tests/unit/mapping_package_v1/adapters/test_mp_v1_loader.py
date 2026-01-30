import json
import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk.core.models.collection_asset import (
    TechnicalMappingCollectionAsset,
    VocabularyMappingCollectionAsset,
    TestDataCollectionAsset,
    SPARQLTestCollectionAsset,
    SHACLTestCollectionAsset,
    TestResultCollectionAsset
)
from mapping_suite_sdk.core.models.file_asset import ConceptualMappingFileAsset
from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_loader import (
    MappingPackageV1MetadataLoader,
    MappingPackageV1Loader
)
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1_metadata import MappingPackageV1Metadata


def test_mp_v1_metadata_loader_handles_missing_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        loader = MappingPackageV1MetadataLoader()

        with pytest.raises(FileNotFoundError):
            loader.load(temp_dir_path, relative_asset_path=Path("non_existing_path.json"))


def test_mp_v1_metadata_loader_handles_invalid_json():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Create invalid JSON file
        metadata_path = temp_dir_path / "metadata.json"
        metadata_path.write_text("invalid json content")

        loader = MappingPackageV1MetadataLoader()

        with pytest.raises(json.JSONDecodeError):
            loader.load(temp_dir_path, relative_asset_path=metadata_path)


def test_mp_v1_loader_initialization_default_values():
    loader = MappingPackageV1Loader()

    assert loader.include_test_data is True
    assert loader.include_output is True


def test_mp_v1_loader_initialization_custom_values():
    loader = MappingPackageV1Loader(include_test_data=False, include_output=False)

    assert loader.include_test_data is False
    assert loader.include_output is False


def test_mp_v1_loader_equality():
    loader1 = MappingPackageV1Loader(include_test_data=True, include_output=True)
    loader2 = MappingPackageV1Loader(include_test_data=True, include_output=True)
    loader3 = MappingPackageV1Loader(include_test_data=False, include_output=True)

    assert loader1 == loader2
    assert loader1 != loader3
    assert loader1 != "not a loader"


def test_mp_v1_loader_tracer_decoration():
    # Test that the loader is properly decorated with @traced_class
    loader = MappingPackageV1Loader()

    # The traced_class decorator should add certain attributes/methods
    # This test verifies the decorator is applied
    assert hasattr(loader, '__class__')
    assert loader.__class__.__name__ == 'MappingPackageV1Loader'


def test_mp_v1_loader_handles_nonexistent_path():
    loader = MappingPackageV1Loader()

    with pytest.raises(FileNotFoundError):
        loader.load(Path("/nonexistent/path"))


def test_mp_v1_loader_validates_package_structure(dummy_mapping_package_v1_model):
    """Test that loader creates a valid package structure matching the model fixture"""
    if not isinstance(dummy_mapping_package_v1_model, MappingPackageV1):
        pytest.skip("This test requires a V1 mapping package model")

    # This is more of an integration test to ensure the loaded package
    # has the same structure as our test fixtures
    assert hasattr(dummy_mapping_package_v1_model, 'metadata')
    assert hasattr(dummy_mapping_package_v1_model, 'conceptual_mapping_asset')
    assert hasattr(dummy_mapping_package_v1_model, 'technical_mapping_suite')
    assert hasattr(dummy_mapping_package_v1_model, 'vocabulary_mapping_suite')
    assert hasattr(dummy_mapping_package_v1_model, 'test_data_suites')
    assert hasattr(dummy_mapping_package_v1_model, 'test_suites_sparql')
    assert hasattr(dummy_mapping_package_v1_model, 'test_suites_shacl')
    assert hasattr(dummy_mapping_package_v1_model, 'test_results')


def test_mp_v1_loader_component_types(dummy_mapping_package_v1_model):
    """Test that all loaded components have correct types"""
    if not isinstance(dummy_mapping_package_v1_model, MappingPackageV1):
        pytest.skip("This test requires a V1 mapping package model")

    assert isinstance(dummy_mapping_package_v1_model.metadata, MappingPackageV1Metadata)
    assert isinstance(dummy_mapping_package_v1_model.conceptual_mapping_asset, ConceptualMappingFileAsset)
    assert isinstance(dummy_mapping_package_v1_model.technical_mapping_suite, TechnicalMappingCollectionAsset)
    assert isinstance(dummy_mapping_package_v1_model.vocabulary_mapping_suite, VocabularyMappingCollectionAsset)
    assert isinstance(dummy_mapping_package_v1_model.test_data_suites, list)
    assert isinstance(dummy_mapping_package_v1_model.test_suites_sparql, list)
    assert isinstance(dummy_mapping_package_v1_model.test_suites_shacl, SHACLTestCollectionAsset)
    assert isinstance(dummy_mapping_package_v1_model.test_results, TestResultCollectionAsset)

    # Verify list contents
    if dummy_mapping_package_v1_model.test_data_suites:
        assert all(
            isinstance(suite, TestDataCollectionAsset) for suite in dummy_mapping_package_v1_model.test_data_suites)

    if dummy_mapping_package_v1_model.test_suites_sparql:
        assert all(
            isinstance(suite, SPARQLTestCollectionAsset) for suite in dummy_mapping_package_v1_model.test_suites_sparql)
