"""Pytest configuration and shared fixtures for all tests.

This module contains pytest fixtures that are shared across multiple test packages.

For shared helper utilities, see tests/test_helpers.py.
"""
from pathlib import Path
from typing import Optional

import mongomock
import pytest
from pydantic import Field, TypeAdapter
from typer.testing import CliRunner

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.core.models.mapping_package import MappingPackage
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
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3MetadataJSONLD
from tests import (
    TEST_DATA_CORRUPTED_MAPPING_PACKAGE_PATH,
    TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_MODEL_PATH,
    TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_FOLDER_PATH,
    TEST_DATA_MAPPING_PACKAGES_REPO_PATH,
    TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_MODEL_PATH,
    TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_FOLDER_PATH,
    TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_PATH,
    TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_PATH,
    TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH,
    TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_PATH,
    TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_MODEL_PATH,
    TEST_DATA_MAPPING_PACKAGES_V3_REPO_PATH
)


# ============================================================================
# Shared Fixtures (used across multiple test packages)
# ============================================================================


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
            ((MappingPackageV3MetadataJSONLD, None),
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
    model.metadata = MappingPackageV3MetadataJSONLD(**model.metadata.model_dump())
    return model


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
def fixture_mapping_package_v3_github_project_path() -> Path:
    """Path to dummy GitHub project for testing."""
    return TEST_DATA_MAPPING_PACKAGES_V3_REPO_PATH

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


# ============================================================================
# Test Models and Fixtures (shared across core package tests)
# ============================================================================


class TestModel(PydanticModel):
    """Test model for repository and general testing purposes."""
    __test__ = False  # Tell pytest this is not a test class

    id: str = Field(default="dummy_id", alias="_id")
    name: str
    description: Optional[str] = None
    count: int = 0


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
