import shutil
import tempfile
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from mssdk.adapters.loader import MappingPackageAssetLoader
from mssdk.models.files import ConceptualMappingFile, TechnicalMappingSuite, VocabularyMappingSuite, TestDataSuite, \
    SAPRQLTestSuite, SHACLTestSuite
from mssdk.models.mapping_package import MappingPackage, MappingPackageMetadata
from tests import TEST_DATA_EXAMPLE_MAPPING_PACKAGE_PATH, TEST_DATA_CORRUPTED_MAPPING_PACKAGE_PATH, \
    TEST_DATA_EXAMPLE_MAPPING_PACKAGE_MODEL_PATH


def _test_mapping_package_asset_loader(dummy_mapping_package_path: Path,
                                       loader_class: MappingPackageAssetLoader,
                                       expected_relative_path: str) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        mapping_suite = loader_class.load(temp_mp_path)

        assert mapping_suite is not None
        assert mapping_suite.path is not None
        assert mapping_suite.path == expected_relative_path
        assert (temp_mp_path / mapping_suite.path).exists()
        assert len(mapping_suite.files) > 0
        for file in mapping_suite.files:
            assert file is not None
            assert (temp_mp_path / file.path).exists()
            assert file.content is not None


def _test_mapping_suites_asset_loader(dummy_mapping_package_path: Path,
                                      loader_class: MappingPackageAssetLoader,
                                      expected_relative_path: str) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        mapping_suites = loader_class.load(temp_mp_path)

        for mapping_suite in mapping_suites:
            assert mapping_suite is not None
            assert mapping_suite.path is not None
            assert mapping_suite.path.is_relative_to(expected_relative_path)
            assert (temp_mp_path / mapping_suite.path).exists()
            assert len(mapping_suite.files) > 0
            for file in mapping_suite.files:
                assert file is not None
                assert (temp_mp_path / file.path).exists()
                assert file.content is not None


def assert_valid_mapping_package(mapping_package: MappingPackage) -> None:
    assert isinstance(mapping_package, MappingPackage), \
        f"Expected MappingPackage instance, got {type(mapping_package)}"

    # Metadata validation
    assert hasattr(mapping_package, 'metadata'), "Missing required field: metadata"
    assert isinstance(mapping_package.metadata, MappingPackageMetadata), \
        f"metadata must be MappingPackageMetadata, got {type(mapping_package.metadata)}"

    # Conceptual Mapping File validation
    assert hasattr(mapping_package, 'conceptual_mapping_file'), \
        "Missing required field: conceptual_mapping_file"
    assert isinstance(mapping_package.conceptual_mapping_file, ConceptualMappingFile), \
        f"conceptual_mapping_file must be ConceptualMappingFile, got {type(mapping_package.conceptual_mapping_file)}"

    # Technical Mapping Suite validation
    assert hasattr(mapping_package, 'technical_mapping_suite'), \
        "Missing required field: technical_mapping_suite"
    assert isinstance(mapping_package.technical_mapping_suite, TechnicalMappingSuite), \
        f"technical_mapping_suite must be TechnicalMappingSuite, got {type(mapping_package.technical_mapping_suite)}"

    # Vocabulary Mapping Suite validation
    assert hasattr(mapping_package, 'vocabulary_mapping_suite'), \
        "Missing required field: vocabulary_mapping_suite"
    assert isinstance(mapping_package.vocabulary_mapping_suite, VocabularyMappingSuite), \
        f"vocabulary_mapping_suite must be VocabularyMappingSuite, got {type(mapping_package.vocabulary_mapping_suite)}"

    # Test Data Suites validation
    assert hasattr(mapping_package, 'test_data_suites'), \
        "Missing required field: test_data_suites"
    assert isinstance(mapping_package.test_data_suites, list), \
        f"test_data_suites must be a list, got {type(mapping_package.test_data_suites)}"
    assert len(mapping_package.test_data_suites) > 0, \
        "test_data_suites list cannot be empty"
    for suite in mapping_package.test_data_suites:
        assert isinstance(suite, TestDataSuite), \
            f"All test_data_suites elements must be TestDataSuite, got {type(suite)}"

    # SPARQL Test Suites validation
    assert hasattr(mapping_package, 'test_suites_sparql'), \
        "Missing required field: test_suites_sparql"
    assert isinstance(mapping_package.test_suites_sparql, list), \
        f"test_suites_sparql must be a list, got {type(mapping_package.test_suites_sparql)}"
    assert len(mapping_package.test_suites_sparql) > 0, \
        "test_suites_sparql list cannot be empty"
    for suite in mapping_package.test_suites_sparql:
        assert isinstance(suite, SAPRQLTestSuite), \
            f"All test_suites_sparql elements must be SAPRQLTestSuite, got {type(suite)}"

    # SHACL Test Suites validation
    assert hasattr(mapping_package, 'test_suites_shacl'), \
        "Missing required field: test_suites_shacl"
    assert isinstance(mapping_package.test_suites_shacl, list), \
        f"test_suites_shacl must be a list, got {type(mapping_package.test_suites_shacl)}"
    assert len(mapping_package.test_suites_shacl) > 0, \
        "test_suites_shacl list cannot be empty"
    for suite in mapping_package.test_suites_shacl:
        assert isinstance(suite, SHACLTestSuite), \
            f"All test_suites_shacl elements must be SHACLTestSuite, got {type(suite)}"


@pytest.fixture
def dummy_mapping_package_path() -> Path:
    return TEST_DATA_EXAMPLE_MAPPING_PACKAGE_PATH


@pytest.fixture
def dummy_corrupted_mapping_package_path() -> Path:
    return TEST_DATA_CORRUPTED_MAPPING_PACKAGE_PATH


@pytest.fixture
def dummy_mapping_package_model() -> MappingPackage:
    return TypeAdapter(MappingPackage).validate_json(TEST_DATA_EXAMPLE_MAPPING_PACKAGE_MODEL_PATH.read_text())
