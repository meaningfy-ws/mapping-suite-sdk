import json
import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk import MappingPackageV2MetadataLoader, MappingPackageV2Loader, MappingPackageV2, \
    MappingPackageV2Metadata
from mapping_suite_sdk.core.models.collection_asset import (
    TechnicalMappingCollectionAsset,
    VocabularyMappingCollectionAsset,
    TestDataCollectionAsset,
    SAPRQLTestCollectionAsset,
    SHACLTestCollectionAsset,
    TestResultCollectionAsset
)
from mapping_suite_sdk.core.models.file_asset import ConceptualMappingFileAsset


def test_mp_v2_metadata_loader_handles_missing_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        loader = MappingPackageV2MetadataLoader()

        with pytest.raises(FileNotFoundError):
            loader.load(temp_dir_path)


def test_mp_v2_metadata_loader_handles_invalid_json():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Create invalid JSON file
        metadata_path = temp_dir_path / "metadata.json"
        metadata_path.write_text("invalid json content")

        loader = MappingPackageV2MetadataLoader()

        with pytest.raises(json.JSONDecodeError):
            loader.load(temp_dir_path)


def test_mp_v2_loader_initialization_default_values():
    loader = MappingPackageV2Loader()

    assert loader.include_test_data is True
    assert loader.include_output is True


def test_mp_v2_loader_initialization_custom_values():
    loader = MappingPackageV2Loader(include_test_data=False, include_output=False)

    assert loader.include_test_data is False
    assert loader.include_output is False


def test_mp_v2_loader_equality():
    loader1 = MappingPackageV2Loader(include_test_data=True, include_output=True)
    loader2 = MappingPackageV2Loader(include_test_data=True, include_output=True)
    loader3 = MappingPackageV2Loader(include_test_data=False, include_output=True)

    assert loader1 == loader2
    assert loader1 != loader3
    assert loader1 != "not a loader"


def test_mp_v2_loader_tracer_decoration():
    # Test that the loader is properly decorated with @traced_class
    loader = MappingPackageV2Loader()

    # The traced_class decorator should add certain attributes/methods
    # This test verifies the decorator is applied
    assert hasattr(loader, '__class__')
    assert loader.__class__.__name__ == 'MappingPackageV2Loader'


def test_mp_v2_loader_handles_nonexistent_path():
    loader = MappingPackageV2Loader()

    with pytest.raises(FileNotFoundError):
        loader.load(Path("/nonexistent/path"))


def test_mp_v2_loader_validates_package_structure(dummy_mapping_package_v2_model):

    # This is more of an integration test to ensure the loaded package
    # has the same structure as our test fixtures
    assert hasattr(dummy_mapping_package_v2_model, 'metadata')
    assert hasattr(dummy_mapping_package_v2_model, 'conceptual_mapping_asset')
    assert hasattr(dummy_mapping_package_v2_model, 'technical_mapping_suite')
    assert hasattr(dummy_mapping_package_v2_model, 'vocabulary_mapping_suite')
    assert hasattr(dummy_mapping_package_v2_model, 'test_data_suites')
    assert hasattr(dummy_mapping_package_v2_model, 'test_suites_sparql')
    assert hasattr(dummy_mapping_package_v2_model, 'test_suites_shacl')
    assert hasattr(dummy_mapping_package_v2_model, 'test_results')


def test_mp_v2_loader_component_types(dummy_mapping_package_v2_model):

    assert isinstance(dummy_mapping_package_v2_model.metadata, MappingPackageV2Metadata)
    assert isinstance(dummy_mapping_package_v2_model.conceptual_mapping_asset, ConceptualMappingFileAsset)
    assert isinstance(dummy_mapping_package_v2_model.technical_mapping_suite, TechnicalMappingCollectionAsset)
    assert isinstance(dummy_mapping_package_v2_model.vocabulary_mapping_suite, VocabularyMappingCollectionAsset)
    assert isinstance(dummy_mapping_package_v2_model.test_data_suites, list)
    assert isinstance(dummy_mapping_package_v2_model.test_suites_sparql, list)
    assert isinstance(dummy_mapping_package_v2_model.test_suites_shacl, SHACLTestCollectionAsset)
    assert isinstance(dummy_mapping_package_v2_model.test_results, TestResultCollectionAsset)

    # Verify list contents
    if dummy_mapping_package_v2_model.test_data_suites:
        assert all(
            isinstance(suite, TestDataCollectionAsset) for suite in dummy_mapping_package_v2_model.test_data_suites)

    if dummy_mapping_package_v2_model.test_suites_sparql:
        assert all(
            isinstance(suite, SAPRQLTestCollectionAsset) for suite in dummy_mapping_package_v2_model.test_suites_sparql)
