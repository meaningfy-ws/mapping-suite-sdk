import json
import random
import shutil
import string
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Set, Optional

import mongomock
import pytest
from git import Repo
from pydantic import TypeAdapter, Field
from typer.testing import CliRunner

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.adapters.loader import MappingPackageAssetLoader
from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
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
from mapping_suite_sdk.core.models.pydantic import PydanticModel
from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_validator import MappingPackageV1Validator
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1_metadata import (
    MappingPackageV1Metadata
)
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_validator import MappingPackageV2Validator
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import (
    MappingPackageV2Metadata
)
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3Metadata
from tests import (
    TEST_DATA_CORRUPTED_MAPPING_PACKAGE_PATH,
    TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_MODEL_PATH,
    TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_FOLDER_PATH,
    TEST_DATA_MAPPING_PACKAGES_REPO_PATH,
    TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_MODEL_PATH,
    TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_FOLDER_PATH,
    TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_PATH,
    TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_PATH,
    TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH, TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_PATH,
    TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_MODEL_PATH
)


class TestModel(PydanticModel):
    """Test model for repository and general testing purposes."""
    id: str = Field(default="dummy_id", alias="_id")

    name: str
    description: Optional[str] = None
    count: int = 0


def _get_random_string(length: int = 20) -> str:
    """Generate a random string for testing purposes."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def _test_mapping_package_asset_loader(
        dummy_mapping_package_path: Path,
        loader_class: MappingPackageAssetLoader,
        expected_relative_path: str
) -> None:
    """
    Generic test utility for mapping package asset loaders.

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


def _test_mapping_suites_asset_loader(
        dummy_mapping_package_path: Path,
        loader_class: MappingPackageAssetLoader,
        expected_relative_path: str
) -> None:
    """
    Generic test utility for mapping suites asset loaders.

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
    """
    Validate that a mapping package instance has all required components.

    Args:
        mapping_package: The mapping package to validate

    Raises:
        AssertionError: If validation fails
    """
    assert isinstance(mapping_package, MappingPackage), \
        f"Expected MappingPackage instance, got {type(mapping_package)}"

    # Metadata validation
    assert hasattr(mapping_package, 'metadata'), "Missing required field: metadata"
    assert isinstance(mapping_package.metadata, MappingPackageMetadata), \
        f"metadata must be MappingPackageMetadata, got {type(mapping_package.metadata)}"

    # Conceptual Mapping File validation
    assert hasattr(mapping_package, 'conceptual_mapping_asset'), \
        "Missing required field: conceptual_mapping_asset"
    assert isinstance(mapping_package.conceptual_mapping_asset, ConceptualMappingFileAsset), \
        f"conceptual_mapping_asset must be ConceptualMappingFileAsset, got {type(mapping_package.conceptual_mapping_asset)}"

    # Technical Mapping Suite validation
    assert hasattr(mapping_package, 'technical_mapping_suite'), \
        "Missing required field: technical_mapping_suite"
    assert isinstance(mapping_package.technical_mapping_suite, TechnicalMappingCollectionAsset), \
        f"technical_mapping_suite must be TechnicalMappingCollectionAsset, got {type(mapping_package.technical_mapping_suite)}"

    # Vocabulary Mapping Suite validation
    assert hasattr(mapping_package, 'vocabulary_mapping_suite'), \
        "Missing required field: vocabulary_mapping_suite"
    assert isinstance(mapping_package.vocabulary_mapping_suite, VocabularyMappingCollectionAsset), \
        f"vocabulary_mapping_suite must be VocabularyMappingCollectionAsset, got {type(mapping_package.vocabulary_mapping_suite)}"

    # Test Data Suites validation
    assert hasattr(mapping_package, 'test_data_suites'), \
        "Missing required field: test_data_suites"
    assert isinstance(mapping_package.test_data_suites, list), \
        f"test_data_suites must be a list, got {type(mapping_package.test_data_suites)}"
    assert len(mapping_package.test_data_suites) > 0, \
        "test_data_suites list cannot be empty"
    for suite in mapping_package.test_data_suites:
        assert isinstance(suite, TestDataCollectionAsset), \
            f"All test_data_suites elements must be TestDataCollectionAsset, got {type(suite)}"

    # SPARQL Test Suites validation
    assert hasattr(mapping_package, 'test_suites_sparql'), \
        "Missing required field: test_suites_sparql"
    assert isinstance(mapping_package.test_suites_sparql, list), \
        f"test_suites_sparql must be a list, got {type(mapping_package.test_suites_sparql)}"
    assert len(mapping_package.test_suites_sparql) > 0, \
        "test_suites_sparql list cannot be empty"
    for suite in mapping_package.test_suites_sparql:
        assert isinstance(suite, SAPRQLTestCollectionAsset), \
            f"All test_suites_sparql elements must be SAPRQLTestCollectionAsset, got {type(suite)}"

    # SHACL Test Suites validation
    assert hasattr(mapping_package, 'test_suites_shacl'), \
        "Missing required field: test_suites_shacl"
    assert isinstance(mapping_package.test_suites_shacl, list), \
        f"test_suites_shacl must be a list, got {type(mapping_package.test_suites_shacl)}"
    assert len(mapping_package.test_suites_shacl) > 0, \
        "test_suites_shacl list cannot be empty"
    for suite in mapping_package.test_suites_shacl:
        assert isinstance(suite, SHACLTestCollectionAsset), \
            f"All test_suites_shacl elements must be SHACLTestCollectionAsset, got {type(suite)}"


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

    Args:
        source_dir: the serialized folder (all files must exist in target)
        target_dir: the dummy package folder (can have extra files)

    Returns:
        (is_equal, error_message)
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
            if not source_file.read_text(encoding='utf-8', errors="ignore") == target_file.read_text(encoding='utf-8',
                                                                                                     errors="ignore"):
                return False, f"Content differs in {rel_path}"

    return True, ""


@contextmanager
def _setup_temporary_test_git_repository(
        dummy_github_project_path: Path,
        dummy_github_branch_name: str = None
):
    """Create a temporary git repository for testing purposes."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / dummy_github_project_path.name
        repo_path = shutil.copytree(dummy_github_project_path, repo_path)
        repo = Repo.init(repo_path)
        repo.git.add(all=True)
        repo.index.commit("commit for test")

        if dummy_github_branch_name:
            repo.create_tag(dummy_github_branch_name)

        yield repo_path


@pytest.fixture
def dummy_corrupted_mapping_package_path() -> Path:
    """Path to a corrupted mapping package for testing error handling."""
    return TEST_DATA_CORRUPTED_MAPPING_PACKAGE_PATH


@pytest.fixture(
    params=[
        pytest.param(
            ((MappingPackageV2Metadata, TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_MODEL_PATH),
             TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_FOLDER_PATH,
             TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_PATH,

             mssdk_config.MPV2_METADATA_FILE_ASSET_PATH,
             mssdk_config.MPV2_CONCEPTUAL_MAPPING_FILE_ASSET_PATH,
             mssdk_config.MPV2_VOCABULARY_COLLECTION_ASSET_PATH,
             mssdk_config.MPV2_TECHNICAL_COLLECTION_ASSET_PATH,
             mssdk_config.MPV2_TEST_DATA_COLLECTION_ASSET_PATH,
             mssdk_config.MPV2_SPARQL_TEST_COLLECTION_ASSET_PATH,
             mssdk_config.MPV2_SHACL_TEST_COLLECTION_ASSET_PATH,
             mssdk_config.MPV2_TEST_RESULT_COLLECTION_ASSET_PATH,
             ),
            id="eForms_V2"
        ),
        pytest.param(
            ((MappingPackageV1Metadata, TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_MODEL_PATH),
             TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_FOLDER_PATH,
             TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_PATH,

             mssdk_config.MPV1_METADATA_FILE_ASSET_PATH,
             mssdk_config.MPV1_CONCEPTUAL_MAPPING_FILE_ASSET_PATH,
             mssdk_config.MPV1_VOCABULARY_COLLECTION_ASSET_PATH,
             mssdk_config.MPV1_TECHNICAL_COLLECTION_ASSET_PATH,
             mssdk_config.MPV1_TEST_DATA_COLLECTION_ASSET_PATH,
             mssdk_config.MPV1_SPARQL_TEST_COLLECTION_ASSET_PATH,
             mssdk_config.MPV1_SHACL_TEST_COLLECTION_ASSET_PATH,
             mssdk_config.MPV1_TEST_RESULT_COLLECTION_ASSET_PATH,
             ),
            id="SF_V1"
        ),
        pytest.param(
            ((MappingPackageV3Metadata, None),
             TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH,
             TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_PATH,

             mssdk_config.MPV3_METADATA_FILE_ASSET_PATH,
             mssdk_config.MPV3_CONCEPTUAL_MAPPING_FILE_ASSET_PATH,
             mssdk_config.MPV3_VOCABULARY_COLLECTION_ASSET_PATH,
             mssdk_config.MPV3_TECHNICAL_COLLECTION_ASSET_PATH,
             mssdk_config.MPV3_TEST_DATA_COLLECTION_ASSET_PATH,
             mssdk_config.MPV3_SPARQL_TEST_COLLECTION_ASSET_PATH,
             mssdk_config.MPV3_SHACL_TEST_COLLECTION_ASSET_PATH,
             mssdk_config.MPV3_TEST_RESULT_COLLECTION_ASSET_PATH,
             ),
            id="Unified_V3"
        )
    ]
)
def dummy_mapping_package_params(request):
    """Fixture that returns a tuple of (model_path, folder_path, archive_path)"""
    return request.param


@pytest.fixture
def dummy_mapping_package_metadata_path(dummy_mapping_package_params):
    return dummy_mapping_package_params[3]


@pytest.fixture
def dummy_mapping_package_conceptual_mapping_path(dummy_mapping_package_params):
    return dummy_mapping_package_params[4]


@pytest.fixture
def dummy_mapping_package_vocabulary_collection_path(dummy_mapping_package_params):
    return dummy_mapping_package_params[5]


@pytest.fixture
def dummy_mapping_package_technical_collection_path(dummy_mapping_package_params):
    return dummy_mapping_package_params[6]


@pytest.fixture
def dummy_mapping_package_test_data_collection_path(dummy_mapping_package_params):
    return dummy_mapping_package_params[7]


@pytest.fixture
def dummy_mapping_package_shacl_collection_path(dummy_mapping_package_params):
    return dummy_mapping_package_params[8]


@pytest.fixture
def dummy_mapping_package_sparql_collection_path(dummy_mapping_package_params):
    return dummy_mapping_package_params[9]


@pytest.fixture
def dummy_mapping_test_result_collection_path(dummy_mapping_package_params):
    return dummy_mapping_package_params[10]


@pytest.fixture
def dummy_mapping_package_model(dummy_mapping_package_params):
    """Returns the model from the parameter tuple."""
    model_info = dummy_mapping_package_params[0]
    metadata_type, model_path = model_info

    # Load as generic MappingPackage first, then update metadata
    model = TypeAdapter(MappingPackage).validate_json(model_path.read_text())
    model.metadata = metadata_type(**model.metadata.model_dump())
    return model


@pytest.fixture
def dummy_mapping_package_v1_model():
    # Load as generic MappingPackage first, then update metadata
    model = TypeAdapter(MappingPackageV1).validate_json(TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_MODEL_PATH.read_text())
    model.metadata = MappingPackageV1Metadata(**model.metadata.model_dump())
    return model


@pytest.fixture
def dummy_mapping_package_v2_model():
    # Load as generic MappingPackage first, then update metadata
    model = TypeAdapter(MappingPackageV2).validate_json(TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_MODEL_PATH.read_text())
    model.metadata = MappingPackageV2Metadata(**model.metadata.model_dump())
    return model


@pytest.fixture
def fixture_mapping_package_v3_model() -> MappingPackageV3:
    model = MappingPackageV3.model_validate_json(TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_MODEL_PATH.read_text())
    model.metadata = MappingPackageV3Metadata(**model.metadata.model_dump())
    return model


# @pytest.fixture
# def dummy_mapping_package_v3_model():
#     # Load as generic MappingPackage first, then update metadata
#     model = TypeAdapter(MappingPackageV3).validate_json(TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_MODEL_PATH.read_text())
#     model.metadata = MappingPackageV3Metadata(**model.metadata.model_dump())
#     return model


@pytest.fixture
def dummy_mapping_package_extracted_path(dummy_mapping_package_params):
    """Returns the folder path from the parameter tuple."""
    folder_path = dummy_mapping_package_params[1]
    return folder_path


@pytest.fixture
def dummy_mapping_package_path(dummy_mapping_package_params):
    """Returns the archive path from the parameter tuple."""
    archive_path = dummy_mapping_package_params[2]
    return archive_path


@pytest.fixture
def dummy_mapping_package_v1_path():
    """Returns the path from the parameter tuple."""
    return TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_FOLDER_PATH


@pytest.fixture
def dummy_mapping_package_v2_path():
    """Returns the path from the parameter tuple."""
    return TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_FOLDER_PATH


@pytest.fixture
def dummy_mapping_package_v3_path():
    """Returns the path from the parameter tuple."""
    return TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH


@pytest.fixture
def dummy_mapping_package_v1_archive_path():
    """Returns the archive path from the parameter tuple."""
    return TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_PATH


@pytest.fixture
def dummy_mapping_package_v2_archive_path():
    """Returns the archive path from the parameter tuple."""
    return TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_PATH


@pytest.fixture
def dummy_mapping_package_v3_archive_path():
    """Returns the archive path from the parameter tuple."""
    return TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_PATH


@pytest.fixture
def dummy_github_project_path() -> Path:
    """Path to dummy GitHub project for testing."""
    return TEST_DATA_MAPPING_PACKAGES_REPO_PATH


@pytest.fixture
def dummy_github_branch_name() -> str:
    """Branch name for GitHub testing."""
    return "test_tag"


@pytest.fixture
def dummy_repo_package_path() -> Path:
    """Path to package within repository."""
    return Path("mappings/package_can_v1.9")


@pytest.fixture
def dummy_packages_path_pattern() -> str:
    """Pattern for finding packages in repository."""
    return "mappings/*_can_*"


@pytest.fixture
def dummy_invalid_github_repo_url() -> str:
    """Invalid GitHub repository URL for testing error cases."""
    return "https://github.com/OP-TED/"


@pytest.fixture
def dummy_non_existing_github_branch_name() -> str:
    """Non-existing branch name for testing error cases."""
    return "non_existing_tag_name"


@pytest.fixture
def dummy_get_all_packages_pattern() -> str:
    """Pattern to get all packages."""
    return "mappings/*"


@pytest.fixture
def dummy_non_existing_pattern() -> str:
    """Non-existing pattern for testing error cases."""
    return "non_existing_pattern*___*_"


@pytest.fixture
def mongo_client() -> mongomock.MongoClient:
    """MongoDB mock client for testing."""
    return mongomock.MongoClient()


@pytest.fixture
def dummy_mongo_repository(mongo_client: mongomock.MongoClient) -> MongoDBRepository:
    """MongoDB repository fixture for testing."""
    return MongoDBRepository(
        model_class=TestModel,
        mongo_client=mongo_client,
        database_name="test_db"
    )


@pytest.fixture
def sample_model() -> TestModel:
    """Sample test model instance."""
    return TestModel(name="Test Model", description="Test Description", count=5)


@pytest.fixture
def updated_sample_model(sample_model: TestModel) -> TestModel:
    """Updated version of sample test model."""
    updated_model = sample_model.model_copy()
    updated_model.name = "Updated Model"
    updated_model.description = "Updated Description"
    updated_model.count = 10
    return updated_model


@pytest.fixture
def dummy_database_name() -> str:
    """Database name for testing."""
    return "test_db_name"


@pytest.fixture
def dummy_collection_name() -> str:
    """Collection name for testing."""
    return "test_collection_Name"


@pytest.fixture
def dummy_mapping_package_v1_validator() -> MappingPackageV1Validator:
    """V1 mapping package validator for testing."""
    return MappingPackageV1Validator()


@pytest.fixture
def dummy_mapping_package_v2_validator() -> MappingPackageV2Validator:
    """V2 mapping package validator for testing."""
    return MappingPackageV2Validator()


@pytest.fixture
def typer_cli_runner() -> CliRunner:
    """CLI runner for testing command-line interfaces."""
    return CliRunner()
