"""Shared test helper utilities and validation functions.

This module contains utility functions used across multiple test packages
for validating mapping packages, comparing files, and setting up test environments.
"""
import json
import random
import shutil
import string
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Set

from git import Repo

from mapping_suite_sdk.core.adapters.loader import AssetLoader
from mapping_suite_sdk.core.models.collection_asset import (
    TechnicalMappingCollectionAsset,
    VocabularyMappingCollectionAsset,
    TestDataCollectionAsset,
    SAPRQLTestCollectionAsset,
    SHACLTestCollectionAsset
)
from mapping_suite_sdk.core.models.file_asset import ConceptualMappingFileAsset
from mapping_suite_sdk.core.models.mapping_package import MappingPackage
from mapping_suite_sdk.core.models.mapping_package_metadata import MappingPackageMetadata


def get_random_string(length: int = 20) -> str:
    """Generate a random string for testing purposes.

    Args:
        length: Length of the random string to generate

    Returns:
        Random string of specified length
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def validate_mapping_package_asset_loader(
        dummy_mapping_package_path: Path,
        loader_class: AssetLoader,
        expected_relative_path: str
) -> None:
    """Generic test utility for mapping package asset loaders.

    Args:
        dummy_mapping_package_path: Path to test mapping package
        loader_class: Loader class to test
        expected_relative_path: Expected relative path within package
    """
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
        assert any([
            mapping_suite.path == expected_relative_path,
            mapping_suite.path == Path(temp_mp_path.name) / expected_relative_path
        ])
        assert (temp_mp_path / mapping_suite.path).exists()
        assert len(mapping_suite.files) > 0
        for file in mapping_suite.files:
            assert file is not None
            assert (temp_mp_path / file.path).exists()
            assert file.content is not None


def validate_mapping_suites_asset_loader(
        dummy_mapping_package_path: Path,
        loader_class: AssetLoader,
        expected_relative_path: str
) -> None:
    """Generic test utility for mapping suites asset loaders.

    Args:
        dummy_mapping_package_path: Path to test mapping package
        loader_class: Loader class to test
        expected_relative_path: Expected relative path within package
    """
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
            assert any([
                mapping_suite.path.is_relative_to(expected_relative_path),
                mapping_suite.path.is_relative_to(Path(temp_mp_path.name) / expected_relative_path)
            ])
            assert (temp_mp_path / mapping_suite.path).exists()
            assert len(mapping_suite.files) > 0
            for file in mapping_suite.files:
                assert file is not None
                assert (temp_mp_path / file.path).exists()
                assert file.content is not None


def assert_valid_mapping_package(mapping_package: MappingPackage) -> None:
    """Validate that a mapping package instance has all required components.

    Args:
        mapping_package: The mapping package to validate

    Raises:
        AssertionError: If validation fails
    """
    assert isinstance(mapping_package, MappingPackage), \
        f"Expected MappingPackage instance, got {type(mapping_package)}"

    # Metadata validation
    assert isinstance(mapping_package.metadata, MappingPackageMetadata), \
        f"metadata must be MappingPackageMetadata, got {type(mapping_package.metadata)}"

    # Conceptual Mapping File validation
    assert isinstance(mapping_package.conceptual_mapping_asset, ConceptualMappingFileAsset), \
        f"conceptual_mapping_asset must be ConceptualMappingFileAsset, got {type(mapping_package.conceptual_mapping_asset)}"

    # Technical Mapping Suite validation
    assert isinstance(mapping_package.technical_mapping_suite, TechnicalMappingCollectionAsset), \
        f"technical_mapping_suite must be TechnicalMappingCollectionAsset, got {type(mapping_package.technical_mapping_suite)}"

    # Vocabulary Mapping Suite validation
    assert isinstance(mapping_package.vocabulary_mapping_suite, VocabularyMappingCollectionAsset), \
        f"vocabulary_mapping_suite must be VocabularyMappingCollectionAsset, got {type(mapping_package.vocabulary_mapping_suite)}"

    # Test Data Suites validation
    assert isinstance(mapping_package.test_data_suites, list), \
        f"test_data_suites must be a list, got {type(mapping_package.test_data_suites)}"
    assert len(mapping_package.test_data_suites) > 0, \
        "test_data_suites list cannot be empty"
    for suite in mapping_package.test_data_suites:
        assert isinstance(suite, TestDataCollectionAsset), \
            f"All test_data_suites elements must be TestDataCollectionAsset, got {type(suite)}"

    # SPARQL Test Suites validation
    assert isinstance(mapping_package.test_suites_sparql, list), \
        f"test_suites_sparql must be a list, got {type(mapping_package.test_suites_sparql)}"
    assert len(mapping_package.test_suites_sparql) > 0, \
        "test_suites_sparql list cannot be empty"
    for suite in mapping_package.test_suites_sparql:
        assert isinstance(suite, SAPRQLTestCollectionAsset), \
            f"All test_suites_sparql elements must be SAPRQLTestCollectionAsset, got {type(suite)}"

    # SHACL Test Suites validation
    assert isinstance(mapping_package.test_suites_shacl, list), \
        f"test_suites_shacl must be a list, got {type(mapping_package.test_suites_shacl)}"
    assert len(mapping_package.test_suites_shacl) > 0, \
        "test_suites_shacl list cannot be empty"
    for suite in mapping_package.test_suites_shacl:
        assert isinstance(suite, SHACLTestCollectionAsset), \
            f"All test_suites_shacl elements must be SHACLTestCollectionAsset, got {type(suite)}"


def get_all_files(directory: Path) -> Set[str]:
    """Get all files in directory recursively, returning relative paths.

    Args:
        directory: Directory to scan

    Returns:
        Set of relative file paths
    """
    return {str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file()}


def compare_json_files(file1: Path, file2: Path) -> bool:
    """Compare two JSON files for semantic equality.

    Args:
        file1: First JSON file path
        file2: Second JSON file path

    Returns:
        True if files are semantically equal, False otherwise
    """
    with file1.open() as f1, file2.open() as f2:
        return json.load(f1) == json.load(f2)


def compare_directories(source_dir: Path, target_dir: Path) -> tuple[bool, str]:
    """Compare directories recursively, allowing target_dir to have extra files.

    Args:
        source_dir: the serialized folder (all files must exist in target)
        target_dir: the dummy package folder (can have extra files)

    Returns:
        (is_equal, error_message)
    """
    source_files = get_all_files(source_dir)
    target_files = get_all_files(target_dir)

    missing_files = source_files - target_files
    if missing_files:
        return False, f"Files missing in {target_dir}:\n" + "\n".join(sorted(missing_files))

    for rel_path in source_files:
        source_file = source_dir / rel_path
        target_file = target_dir / rel_path

        if source_file.suffix.lower() == '.json':
            try:
                if not compare_json_files(source_file, target_file):
                    return False, f"JSON content differs in {rel_path}"
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON in {rel_path}: {str(e)}"
        else:
            # Binary comparison for other files
            if not source_file.read_text(encoding='utf-8', errors="ignore") == target_file.read_text(encoding='utf-8',
                                                                                                     errors="ignore"):
                return False, f"Content differs in {rel_path}"

    return True, ""


@contextmanager
def setup_temporary_test_git_repository(
        dummy_github_project_path: Path,
        dummy_github_branch_name: str = None
):
    """Create a temporary git repository for testing purposes.

    Args:
        dummy_github_project_path: Path to source project to copy
        dummy_github_branch_name: Optional branch/tag name to create

    Yields:
        Path to temporary git repository
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / dummy_github_project_path.name
        repo_path = shutil.copytree(dummy_github_project_path, repo_path)
        repo = Repo.init(repo_path)
        repo.git.add(all=True)
        repo.index.commit("commit for test")

        if dummy_github_branch_name:
            repo.create_tag(dummy_github_branch_name)

        yield repo_path