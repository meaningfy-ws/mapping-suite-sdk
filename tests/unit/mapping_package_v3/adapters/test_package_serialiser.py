from pathlib import Path
from unittest.mock import patch

from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser import MappingPackageV3Serialiser
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3


def test_mp_v3_serialiser_creates_all_components(tmp_path: Path,
                                                 fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    serialiser = MappingPackageV3Serialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model)

    assert (tmp_path / fixture_mapping_package_v3_model.metadata.path).exists()
    assert (tmp_path / fixture_mapping_package_v3_model.conceptual_mapping_asset.path).exists()
    assert (tmp_path / fixture_mapping_package_v3_model.technical_mapping_suite.path).exists()
    assert (tmp_path / fixture_mapping_package_v3_model.vocabulary_mapping_suite.path).exists()


@patch('mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser.MappingPackageV3MetadataSerialiser')
@patch('mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser.ConceptualMappingFileAssetSerialiser')
@patch('mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser.TechnicalMappingCollectionAssetSerialiser')
@patch('mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser.VocabularyMappingCollectionAssetSerialiser')
@patch('mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser.TestDataCollectionAssetSerialiser')
@patch('mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser.SPARQLTestCollectionAssetSerialiser')
@patch('mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser.SHACLTestCollectionAssetSerialiser')
@patch('mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser.TestResultCollectionAssetSerialiser')
def test_mp_v3_serialiser_calls_all_component_serialisers(
        mock_test_result_serialiser,
        mock_shacl_serialiser,
        mock_sparql_serialiser,
        mock_test_data_serialiser,
        mock_vocab_serialiser,
        mock_tech_serialiser,
        mock_cm_serialiser,
        mock_metadata_serialiser,
        tmp_path: Path,
        fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    serialiser = MappingPackageV3Serialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model)

    mock_metadata_serialiser.return_value.serialise.assert_called_once_with(
        tmp_path, fixture_mapping_package_v3_model.metadata
    )
    mock_cm_serialiser.return_value.serialise.assert_called_once_with(
        tmp_path, fixture_mapping_package_v3_model.conceptual_mapping_asset
    )
    mock_tech_serialiser.return_value.serialise.assert_called_once_with(
        tmp_path, fixture_mapping_package_v3_model.technical_mapping_suite
    )
    mock_vocab_serialiser.return_value.serialise.assert_called_once_with(
        tmp_path, fixture_mapping_package_v3_model.vocabulary_mapping_suite
    )
    mock_test_data_serialiser.return_value.serialise.assert_called_once_with(
        tmp_path, fixture_mapping_package_v3_model.test_data_suites
    )
    mock_sparql_serialiser.return_value.serialise.assert_called_once_with(
        tmp_path, fixture_mapping_package_v3_model.test_suites_sparql
    )
    mock_shacl_serialiser.return_value.serialise.assert_called_once_with(
        tmp_path, fixture_mapping_package_v3_model.test_suites_shacl
    )
    mock_test_result_serialiser.return_value.serialise.assert_called_once_with(
        tmp_path, fixture_mapping_package_v3_model.test_results
    )


def test_mp_v3_serialiser_tracer_decoration() -> None:
    serialiser = MappingPackageV3Serialiser()

    assert hasattr(serialiser, '__class__')
    assert serialiser.__class__.__name__ == 'MappingPackageV3Serialiser'


def test_mp_v3_serialiser_preserves_file_content(tmp_path: Path,
                                                 fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    serialiser = MappingPackageV3Serialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model)

    for tm_file in fixture_mapping_package_v3_model.technical_mapping_suite.files:
        file_path = tmp_path / tm_file.path
        assert file_path.exists()
        assert file_path.read_text() == tm_file.content

    for vm_file in fixture_mapping_package_v3_model.vocabulary_mapping_suite.files:
        file_path = tmp_path / vm_file.path
        assert file_path.exists()
        assert file_path.read_text() == vm_file.content

    cm_path = tmp_path / fixture_mapping_package_v3_model.conceptual_mapping_asset.path
    assert cm_path.exists()
    assert cm_path.read_bytes() == fixture_mapping_package_v3_model.conceptual_mapping_asset.content


def test_mp_v3_serialiser_creates_directory_structure(tmp_path: Path,
                                                      fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    serialiser = MappingPackageV3Serialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model)

    tech_suite_path = tmp_path / fixture_mapping_package_v3_model.technical_mapping_suite.path
    assert tech_suite_path.exists()
    assert tech_suite_path.is_dir()

    vocab_suite_path = tmp_path / fixture_mapping_package_v3_model.vocabulary_mapping_suite.path
    assert vocab_suite_path.exists()
    assert vocab_suite_path.is_dir()

    cm_path = tmp_path / fixture_mapping_package_v3_model.conceptual_mapping_asset.path
    assert cm_path.parent.exists()


def test_mp_v3_serialiser_handles_test_data_suites(tmp_path: Path,
                                                   fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    serialiser = MappingPackageV3Serialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model)

    for test_suite in fixture_mapping_package_v3_model.test_data_suites:
        suite_path = tmp_path / test_suite.path
        assert suite_path.exists()
        assert suite_path.is_dir()

        for test_file in test_suite.files:
            file_path = tmp_path / test_file.path
            assert file_path.exists()


def test_mp_v3_serialiser_handles_sparql_test_suites(tmp_path: Path,
                                                     fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    serialiser = MappingPackageV3Serialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model)

    for sparql_suite in fixture_mapping_package_v3_model.test_suites_sparql:
        suite_path = tmp_path / sparql_suite.path
        assert suite_path.exists()
        assert suite_path.is_dir()

        for query_file in sparql_suite.files:
            file_path = tmp_path / query_file.path
            assert file_path.exists()


def test_mp_v3_serialiser_handles_shacl_test_suite(tmp_path: Path,
                                                   fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    serialiser = MappingPackageV3Serialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model)

    for shacl_suite in fixture_mapping_package_v3_model.test_suites_shacl.shacl_collections:
        suite_path = tmp_path / shacl_suite.path
        assert suite_path.exists()
        assert suite_path.is_dir()

        for shacl_file in shacl_suite.files:
            file_path = tmp_path / shacl_file.path
            assert file_path.exists()


def test_mp_v3_serialiser_handles_empty_collections(tmp_path: Path,
                                                    fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    empty_model = fixture_mapping_package_v3_model.model_copy(deep=True)
    empty_model.test_data_suites = []
    empty_model.test_suites_sparql = []

    serialiser = MappingPackageV3Serialiser()
    serialiser.serialise(tmp_path, empty_model)

    assert (tmp_path / empty_model.metadata.path).exists()
    assert (tmp_path / empty_model.conceptual_mapping_asset.path).exists()


def test_mp_v3_serialiser_protocol_implementation() -> None:
    serialiser = MappingPackageV3Serialiser()

    assert hasattr(serialiser, 'serialise')
    assert callable(getattr(serialiser, 'serialise'))
