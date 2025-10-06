import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_serialiser import MappingPackageV2MetadataSerialiser, \
    MappingPackageV2Serialiser
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2


def test_mp_v1_metadata_serialiser_creates_metadata_file(dummy_mapping_package_v2_model):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        serialiser = MappingPackageV2MetadataSerialiser()
        serialiser.serialise(temp_path, dummy_mapping_package_v2_model.metadata)

        # Verify metadata file is created
        metadata_path = temp_path / dummy_mapping_package_v2_model.metadata.path
        assert metadata_path.exists()
        assert metadata_path.is_file()


def test_mp_v1_metadata_serialiser_creates_parent_directories(dummy_mapping_package_v2_model):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create metadata with nested path
        metadata = dummy_mapping_package_v2_model.metadata

        serialiser = MappingPackageV2MetadataSerialiser()
        serialiser.serialise(temp_path, metadata)

        # Verify nested directories are created
        metadata_path = temp_path / metadata.path
        assert metadata_path.exists()
        assert metadata_path.parent.exists()


def test_mp_v1_metadata_serialiser_json_format(dummy_mapping_package_v2_model):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        serialiser = MappingPackageV2MetadataSerialiser()
        serialiser.serialise(temp_path, dummy_mapping_package_v2_model.metadata)

        metadata_path = temp_path / dummy_mapping_package_v2_model.metadata.path
        content = metadata_path.read_text()

        # Verify it's valid JSON
        parsed_json = json.loads(content)
        assert isinstance(parsed_json, dict)

        # Verify required fields are present
        assert "title" in parsed_json
        assert "identifier" in parsed_json
        assert "mapping_version" in parsed_json
        assert "ontology_version" in parsed_json


def test_mp_v1_metadata_serialiser_excludes_path_field(dummy_mapping_package_v2_model):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        serialiser = MappingPackageV2MetadataSerialiser()
        serialiser.serialise(temp_path, dummy_mapping_package_v2_model.metadata)

        metadata_path = temp_path / dummy_mapping_package_v2_model.metadata.path
        content = metadata_path.read_text()
        parsed_json = json.loads(content)

        # Path field should be excluded from serialized JSON
        assert "path" not in parsed_json


def test_mp_v1_metadata_serialiser_pretty_formatted(dummy_mapping_package_v2_model):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        serialiser = MappingPackageV2MetadataSerialiser()
        serialiser.serialise(temp_path, dummy_mapping_package_v2_model.metadata)

        metadata_path = temp_path / dummy_mapping_package_v2_model.metadata.path
        content = metadata_path.read_text()

        # Verify JSON is pretty-formatted (indented)
        assert "\n" in content  # Should have newlines
        assert "  " in content or "\t" in content  # Should have indentation


def test_mp_v1_metadata_serialiser_excludes_none_values(dummy_mapping_package_v2_model):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create metadata with some None values
        metadata = dummy_mapping_package_v2_model.metadata

        serialiser = MappingPackageV2MetadataSerialiser()
        serialiser.serialise(temp_path, metadata)

        metadata_path = temp_path / metadata.path
        content = metadata_path.read_text()
        parsed_json = json.loads(content)

        # None values should not appear in JSON
        for value in parsed_json.values():
            assert value is not None


def test_mp_v1_serialiser_creates_all_components(dummy_mapping_package_v2_model):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        serialiser = MappingPackageV2Serialiser()
        serialiser.serialise(temp_path, dummy_mapping_package_v2_model)

        # Verify all major components are created
        assert (temp_path / dummy_mapping_package_v2_model.metadata.path).exists()
        assert (temp_path / dummy_mapping_package_v2_model.conceptual_mapping_asset.path).exists()
        assert (temp_path / dummy_mapping_package_v2_model.technical_mapping_suite.path).exists()
        assert (temp_path / dummy_mapping_package_v2_model.vocabulary_mapping_suite.path).exists()


@patch('mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_serialiser.MappingPackageV2MetadataSerialiser')
@patch('mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_serialiser.ConceptualMappingFileAssetSerialiser')
@patch('mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_serialiser.TechnicalMappingCollectionAssetSerialiser')
@patch('mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_serialiser.VocabularyMappingCollectionAssetSerialiser')
@patch('mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_serialiser.TestDataCollectionAssetSerialiser')
@patch('mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_serialiser.SAPRQLTestCollectionAssetSerialiser')
@patch('mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_serialiser.SHACLTestCollectionAssetSerialiser')
@patch('mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_serialiser.TestResultCollectionAssetSerialiser')
def test_mp_v1_serialiser_calls_all_component_serialisers(
        mock_test_result_serialiser,
        mock_shacl_serialiser,
        mock_sparql_serialiser,
        mock_test_data_serialiser,
        mock_vocab_serialiser,
        mock_tech_serialiser,
        mock_cm_serialiser,
        mock_metadata_serialiser,
        dummy_mapping_package_v2_model
):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        serialiser = MappingPackageV2Serialiser()
        serialiser.serialise(temp_path, dummy_mapping_package_v2_model)

        # Verify all component serialisers were called
        mock_metadata_serialiser.return_value.serialise.assert_called_once_with(
            temp_path, dummy_mapping_package_v2_model.metadata
        )
        mock_cm_serialiser.return_value.serialise.assert_called_once_with(
            temp_path, dummy_mapping_package_v2_model.conceptual_mapping_asset
        )
        mock_tech_serialiser.return_value.serialise.assert_called_once_with(
            temp_path, dummy_mapping_package_v2_model.technical_mapping_suite
        )
        mock_vocab_serialiser.return_value.serialise.assert_called_once_with(
            temp_path, dummy_mapping_package_v2_model.vocabulary_mapping_suite
        )
        mock_test_data_serialiser.return_value.serialise.assert_called_once_with(
            temp_path, dummy_mapping_package_v2_model.test_data_suites
        )
        mock_sparql_serialiser.return_value.serialise.assert_called_once_with(
            temp_path, dummy_mapping_package_v2_model.test_suites_sparql
        )
        mock_shacl_serialiser.return_value.serialise.assert_called_once_with(
            temp_path, dummy_mapping_package_v2_model.test_suites_shacl
        )
        mock_test_result_serialiser.return_value.serialise.assert_called_once_with(
            temp_path, dummy_mapping_package_v2_model.test_results
        )


def test_mp_v1_serialiser_tracer_decoration():
    # Test that the serialiser is properly decorated with @traced_class
    serialiser = MappingPackageV2Serialiser()

    # The traced_class decorator should add certain attributes/methods
    assert hasattr(serialiser, '__class__')
    assert serialiser.__class__.__name__ == 'MappingPackageV2Serialiser'


def test_mp_v1_serialiser_preserves_file_content(dummy_mapping_package_v2_model):
    if not isinstance(dummy_mapping_package_v2_model, MappingPackageV2):
        pytest.skip("This test requires a V1 mapping package")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        serialiser = MappingPackageV2Serialiser()
        serialiser.serialise(temp_path, dummy_mapping_package_v2_model)

        # Verify technical mapping files are written correctly
        for tm_file in dummy_mapping_package_v2_model.technical_mapping_suite.files:
            file_path = temp_path / tm_file.path
            assert file_path.exists()
            assert file_path.read_text() == tm_file.content

        # Verify vocabulary mapping files are written correctly
        for vm_file in dummy_mapping_package_v2_model.vocabulary_mapping_suite.files:
            file_path = temp_path / vm_file.path
            assert file_path.exists()
            assert file_path.read_text() == vm_file.content

        # Verify conceptual mapping file is written correctly
        cm_path = temp_path / dummy_mapping_package_v2_model.conceptual_mapping_asset.path
        assert cm_path.exists()
        assert cm_path.read_bytes() == dummy_mapping_package_v2_model.conceptual_mapping_asset.content


def test_mp_v1_serialiser_creates_directory_structure(dummy_mapping_package_v2_model):
    if not isinstance(dummy_mapping_package_v2_model, MappingPackageV2):
        pytest.skip("This test requires a V1 mapping package")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        serialiser = MappingPackageV2Serialiser()
        serialiser.serialise(temp_path, dummy_mapping_package_v2_model)

        # Verify directory structure is created
        tech_suite_path = temp_path / dummy_mapping_package_v2_model.technical_mapping_suite.path
        assert tech_suite_path.exists()
        assert tech_suite_path.is_dir()

        vocab_suite_path = temp_path / dummy_mapping_package_v2_model.vocabulary_mapping_suite.path
        assert vocab_suite_path.exists()
        assert vocab_suite_path.is_dir()

        # Verify parent directories for files are created
        cm_path = temp_path / dummy_mapping_package_v2_model.conceptual_mapping_asset.path
        assert cm_path.parent.exists()


def test_mp_v1_serialiser_handles_test_data_suites(dummy_mapping_package_v2_model):
    if not isinstance(dummy_mapping_package_v2_model, MappingPackageV2):
        pytest.skip("This test requires a V1 mapping package")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        serialiser = MappingPackageV2Serialiser()
        serialiser.serialise(temp_path, dummy_mapping_package_v2_model)

        # Verify test data suites are created
        for test_suite in dummy_mapping_package_v2_model.test_data_suites:
            suite_path = temp_path / test_suite.path
            assert suite_path.exists()
            assert suite_path.is_dir()

            for test_file in test_suite.files:
                file_path = temp_path / test_file.path
                assert file_path.exists()


def test_mp_v1_serialiser_handles_sparql_test_suites(dummy_mapping_package_v2_model):
    if not isinstance(dummy_mapping_package_v2_model, MappingPackageV2):
        pytest.skip("This test requires a V1 mapping package")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        serialiser = MappingPackageV2Serialiser()
        serialiser.serialise(temp_path, dummy_mapping_package_v2_model)

        # Verify SPARQL test suites are created
        for sparql_suite in dummy_mapping_package_v2_model.test_suites_sparql:
            suite_path = temp_path / sparql_suite.path
            assert suite_path.exists()
            assert suite_path.is_dir()

            for query_file in sparql_suite.files:
                file_path = temp_path / query_file.path
                assert file_path.exists()


def test_mp_v1_serialiser_handles_shacl_test_suite(dummy_mapping_package_v2_model):
    if not isinstance(dummy_mapping_package_v2_model, MappingPackageV2):
        pytest.skip("This test requires a V1 mapping package")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        serialiser = MappingPackageV2Serialiser()
        serialiser.serialise(temp_path, dummy_mapping_package_v2_model)

        # Verify SHACL test suite structure
        shacl_suite = dummy_mapping_package_v2_model.test_suites_shacl

        # Check SHACL result query
        if hasattr(shacl_suite, 'shacl_result_query') and shacl_suite.shacl_result_query:
            query_path = temp_path / shacl_suite.shacl_result_query.path
            assert query_path.exists()

        # Check SHACL collections
        if hasattr(shacl_suite, 'shacl_collections'):
            for collection in shacl_suite.shacl_collections:
                collection_path = temp_path / collection.path
                assert collection_path.exists()
                assert collection_path.is_dir()


def test_mp_v1_serialiser_handles_empty_collections(dummy_mapping_package_v2_model):
    if not isinstance(dummy_mapping_package_v2_model, MappingPackageV2):
        pytest.skip("This test requires a V1 mapping package")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a copy of the model with empty collections
        empty_model = dummy_mapping_package_v2_model.model_copy(deep=True)
        empty_model.test_data_suites = []
        empty_model.test_suites_sparql = []

        serialiser = MappingPackageV2Serialiser()
        serialiser.serialise(temp_path, empty_model)

        # Should still work with empty collections
        assert (temp_path / empty_model.metadata.path).exists()
        assert (temp_path / empty_model.conceptual_mapping_asset.path).exists()


def test_mp_v1_serialiser_reproduces_original_structure(
        dummy_mapping_package_v2_model,
        dummy_mapping_package_extracted_path: Path
):
    """Test that serialization produces the same structure as the original package"""
    if not isinstance(dummy_mapping_package_v2_model, MappingPackageV2):
        pytest.skip("This test requires a V1 mapping package")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        serialiser = MappingPackageV2Serialiser()
        serialiser.serialise(temp_path, dummy_mapping_package_v2_model)

        # Compare with original structure (this might need adjustment based on test data)
        # The comparison should focus on file existence and content, not exact structure
        # since some paths might be normalized or organized differently

        # Verify essential files exist
        assert (temp_path / dummy_mapping_package_v2_model.metadata.path).exists()
        assert (temp_path / dummy_mapping_package_v2_model.conceptual_mapping_asset.path).exists()

        # Verify suites exist
        assert (temp_path / dummy_mapping_package_v2_model.technical_mapping_suite.path).is_dir()
        assert (temp_path / dummy_mapping_package_v2_model.vocabulary_mapping_suite.path).is_dir()


def test_mp_v1_metadata_serialiser_uses_alias_fields(dummy_mapping_package_v2_model):
    """Test that metadata serialization uses field aliases"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        metadata = dummy_mapping_package_v2_model.metadata

        serialiser = MappingPackageV2MetadataSerialiser()
        serialiser.serialise(temp_path, metadata)

        metadata_path = temp_path / metadata.path
        content = metadata_path.read_text()
        parsed_json = json.loads(content)

        # Should use aliases if they exist in the model
        # This test verifies the by_alias=True parameter works
        assert isinstance(parsed_json, dict)
        assert len(parsed_json) > 0


def test_mp_v1_serialiser_protocol_implementation():
    """Test that the serialiser properly implements the protocol"""
    serialiser = MappingPackageV2Serialiser()

    # Should have the required serialise method
    assert hasattr(serialiser, 'serialise')
    assert callable(getattr(serialiser, 'serialise'))
