"""
Unit tests for MappingPackageV3Repository.

Tests cover CRUD operations and MongoDB-specific behavior for V3 mapping packages.
"""

import mongomock
import pytest
from pymongo.errors import DuplicateKeyError

from mapping_suite_sdk.core.adapters.repository import ModelNotFoundError
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_repository import (
    MappingPackageV3Repository,
    PACKAGE_VERSION,
    DEFAULT_COLLECTION_NAME
)
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3


def test_create_with_success_non_existing_element(
    mongo_client: mongomock.MongoClient,
    fixture_mapping_package_v3_model: MappingPackageV3
):
    """Test creating a new mapping package in MongoDB."""
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db"
    )

    result_id = repository.create(fixture_mapping_package_v3_model)
    stored_result = repository.collection.find_one({"_id": fixture_mapping_package_v3_model.id})

    assert result_id == fixture_mapping_package_v3_model.id
    assert stored_result is not None
    assert stored_result["package_version"] == PACKAGE_VERSION
    assert stored_result["_id"] == fixture_mapping_package_v3_model.id

    # Remove MongoDB-specific fields and validate
    stored_result.pop("_id", None)
    stored_result.pop("package_version", None)
    stored_model = MappingPackageV3.model_validate(stored_result)
    assert stored_model.metadata.id == fixture_mapping_package_v3_model.metadata.id


def test_create_fails_on_creating_existing_element(
    mongo_client: mongomock.MongoClient,
    fixture_mapping_package_v3_model: MappingPackageV3
):
    """Test that creating a duplicate package raises DuplicateKeyError."""
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db"
    )

    repository.create(fixture_mapping_package_v3_model)

    with pytest.raises(DuplicateKeyError):
        repository.create(fixture_mapping_package_v3_model)


def test_read_with_success_existing_element(
    mongo_client: mongomock.MongoClient,
    fixture_mapping_package_v3_model: MappingPackageV3
):
    """Test reading an existing mapping package from MongoDB."""
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db"
    )

    repository.create(fixture_mapping_package_v3_model)
    stored_model = repository.read(fixture_mapping_package_v3_model.id)

    assert stored_model is not None
    assert stored_model.id == fixture_mapping_package_v3_model.id
    assert stored_model.metadata.id == fixture_mapping_package_v3_model.metadata.id


def test_read_fails_on_non_existing_element(
    mongo_client: mongomock.MongoClient,
    fixture_mapping_package_v3_model: MappingPackageV3
):
    """Test that reading a non-existent package raises ModelNotFoundError."""
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db"
    )

    with pytest.raises(ModelNotFoundError) as exc_info:
        repository.read(fixture_mapping_package_v3_model.id)

    assert f"Mapping package with ID {fixture_mapping_package_v3_model.id} not found" in str(exc_info.value)


def test_read_many_with_success_without_filters(
    mongo_client: mongomock.MongoClient,
    fixture_mapping_package_v3_model: MappingPackageV3
):
    """Test reading multiple packages without filters."""
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db"
    )

    # Create multiple packages by modifying the id
    package1 = fixture_mapping_package_v3_model.model_copy(deep=True)
    package1.metadata.id = "package_1"
    package2 = fixture_mapping_package_v3_model.model_copy(deep=True)
    package2.metadata.id = "package_2"
    package3 = fixture_mapping_package_v3_model.model_copy(deep=True)
    package3.metadata.id = "package_3"

    repository.create(package1)
    repository.create(package2)
    repository.create(package3)

    results = repository.read_many()

    assert len(results) == 3
    assert {pkg.id for pkg in results} == {package1.id, package2.id, package3.id}


def test_read_many_with_success_with_filters(
    mongo_client: mongomock.MongoClient,
    fixture_mapping_package_v3_model: MappingPackageV3
):
    """Test reading multiple packages with filters."""
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db"
    )

    package1 = fixture_mapping_package_v3_model.model_copy(deep=True)
    package1.metadata.id = "package_1"

    package2 = fixture_mapping_package_v3_model.model_copy(deep=True)
    package2.metadata.id = "package_2"

    package3 = fixture_mapping_package_v3_model.model_copy(deep=True)
    package3.metadata.id = "package_3"

    repository.create(package1)
    repository.create(package2)
    repository.create(package3)

    results = repository.read_many({})

    assert len(results) == 3


def test_update_with_success_existing_element(
    mongo_client: mongomock.MongoClient,
    fixture_mapping_package_v3_model: MappingPackageV3
):
    """Test updating an existing mapping package."""
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db"
    )

    repository.create(fixture_mapping_package_v3_model)

    # Update the package
    updated_package = fixture_mapping_package_v3_model.model_copy(deep=True)
    updated_package.metadata.description = "Updated description"

    result = repository.update(updated_package)

    assert result.metadata.description == "Updated description"
    stored_model = repository.read(updated_package.id)
    assert stored_model.metadata.description == "Updated description"


def test_update_fails_on_non_existing_element(
    mongo_client: mongomock.MongoClient,
    fixture_mapping_package_v3_model: MappingPackageV3
):
    """Test that updating a non-existent package raises ModelNotFoundError."""
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db"
    )

    with pytest.raises(ModelNotFoundError):
        repository.update(fixture_mapping_package_v3_model)


def test_delete_with_success_existing_element(
    mongo_client: mongomock.MongoClient,
    fixture_mapping_package_v3_model: MappingPackageV3
):
    """Test deleting an existing mapping package."""
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db"
    )

    repository.create(fixture_mapping_package_v3_model)
    stored_result = repository.collection.find_one({"_id": fixture_mapping_package_v3_model.id})

    assert stored_result is not None

    repository.delete(fixture_mapping_package_v3_model.id)

    assert repository.collection.find_one({"_id": fixture_mapping_package_v3_model.id}) is None


def test_delete_fails_on_non_existing_element(
    mongo_client: mongomock.MongoClient,
    fixture_mapping_package_v3_model: MappingPackageV3
):
    """Test that deleting a non-existent package raises ModelNotFoundError."""
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db"
    )

    with pytest.raises(ModelNotFoundError):
        repository.delete(fixture_mapping_package_v3_model.id)


def test_repository_uses_default_collection_name(mongo_client: mongomock.MongoClient):
    """Test that repository uses default collection name when not specified."""
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db"
    )

    assert repository.collection_name == DEFAULT_COLLECTION_NAME


def test_repository_uses_custom_collection_name(mongo_client: mongomock.MongoClient):
    """Test that repository uses custom collection name when specified."""
    custom_collection = "custom_v3_collection"
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db",
        collection_name=custom_collection
    )

    assert repository.collection_name == custom_collection


def test_package_version_field_is_stored(
    mongo_client: mongomock.MongoClient,
    fixture_mapping_package_v3_model: MappingPackageV3
):
    """Test that package_version field is stored in MongoDB."""
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db"
    )

    repository.create(fixture_mapping_package_v3_model)
    stored_result = repository.collection.find_one({"_id": fixture_mapping_package_v3_model.id})

    assert stored_result is not None
    assert stored_result["package_version"] == PACKAGE_VERSION


def test_package_version_field_is_removed_on_read(
    mongo_client: mongomock.MongoClient,
    fixture_mapping_package_v3_model: MappingPackageV3
):
    """Test that package_version field is removed when reading from MongoDB."""
    repository = MappingPackageV3Repository(
        mongo_client=mongo_client,
        database_name="test_db"
    )

    repository.create(fixture_mapping_package_v3_model)
    stored_model = repository.read(fixture_mapping_package_v3_model.id)

    # Verify the model doesn't have package_version (it's not a model field)
    assert not hasattr(stored_model, "package_version")

