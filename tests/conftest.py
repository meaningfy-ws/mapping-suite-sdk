import filecmp
import json
import shutil
import tempfile
from pathlib import Path
from typing import Set

import pytest
from pydantic import TypeAdapter

from mssdk.adapters.loader import MappingPackageAssetLoader
from mssdk.models.asset import ConceptualMappingPackageAsset, TechnicalMappingSuite, VocabularyMappingSuite, TestDataSuite, \
    SAPRQLTestSuite, SHACLTestSuite
from mssdk.models.mapping_package import MappingPackage, MappingPackageMetadata
from tests import TEST_DATA_EXAMPLE_MAPPING_PACKAGE_PATH, TEST_DATA_CORRUPTED_MAPPING_PACKAGE_PATH, \
    TEST_DATA_EXAMPLE_MAPPING_PACKAGE_MODEL_PATH, TEST_DATA_EXAMPLE_MAPPING_PACKAGE_FOLDER_PATH


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
    assert isinstance(mapping_package.conceptual_mapping_file, ConceptualMappingPackageAsset), \
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


def _get_all_files(directory: Path) -> Set[str]:
    """Get all files in directory recursively, returning relative paths."""
    return {str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file()}


def _compare_json_files(file1: Path, file2: Path) -> bool:
    """Compare two JSON files for semantic equality."""
    with file1.open() as f1, file2.open() as f2:
        return json.load(f1) == json.load(f2)


def _compare_directories(source_dir: Path, target_dir: Path) -> tuple[bool, str]:
    """
    Compare directories recursively, allowing target_dir to have extra files.
    source_dir: the serialized folder (all files must exist in target)
    target_dir: the dummy package folder (can have extra files)
    Returns (is_equal, error_message)
    """

    source_files = _get_all_files(source_dir)
    target_files = _get_all_files(target_dir)

    missing_files = source_files - target_files
    if missing_files:
        return False, f"Files missing in {target_dir}:\n" + "\n".join(sorted(missing_files))

    for rel_path in source_files:
        source_file = source_dir / rel_path
        target_file = target_dir / rel_path

        if source_file.suffix.lower() == '.json':
            try:
                if not _compare_json_files(source_file, target_file):
                    return False, f"JSON content differs in {rel_path}"
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON in {rel_path}: {str(e)}"
        else:
            # Binary comparison for other files
            # Alternative: #filecmp.cmp(str(source_file), str(target_file), shallow=False) # Also compares timestamp
            if not source_file.read_text(encoding='utf-8', errors="ignore") == target_file.read_text(encoding='utf-8', errors="ignore"):
                return False, f"Content differs in {rel_path}"

    return True, ""


@pytest.fixture
def dummy_mapping_package_path() -> Path:
    return TEST_DATA_EXAMPLE_MAPPING_PACKAGE_PATH


@pytest.fixture
def dummy_corrupted_mapping_package_path() -> Path:
    return TEST_DATA_CORRUPTED_MAPPING_PACKAGE_PATH


@pytest.fixture
def dummy_mapping_package_model() -> MappingPackage:
    return TypeAdapter(MappingPackage).validate_json(TEST_DATA_EXAMPLE_MAPPING_PACKAGE_MODEL_PATH.read_text())


@pytest.fixture
def dummy_mapping_package_extracted_path() -> Path:
    return TEST_DATA_EXAMPLE_MAPPING_PACKAGE_FOLDER_PATH
