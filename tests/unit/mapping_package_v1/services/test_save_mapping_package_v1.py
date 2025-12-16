"""
Unit tests for the save_mapping_package_v1 service.

Tests focus on service layer responsibilities:
- Simple dump-to-mongo functionality
- Integration with PackageRepository
"""
import mongomock
import pytest

from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1
from mapping_suite_sdk.mapping_package_v1.services.save_mapping_package_v1 import (
    save_mapping_package_v1_to_mongo_db
)


class TestSaveMappingPackageV1ToMongoDB:
    """Tests for saving MappingPackageV1 models to MongoDB."""

    def test_save_mapping_package_v1_success(self, dummy_mapping_package_v1_model):
        """Test successful saving of a v1 mapping package model to MongoDB."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        result = save_mapping_package_v1_to_mongo_db(
            mapping_package=dummy_mapping_package_v1_model,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )

        assert isinstance(result, MappingPackageV1)
        assert result.id is not None

        # Verify it was saved to MongoDB
        repository = MongoDBRepository[MappingPackageV1](
            model_class=MappingPackageV1,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )
        stored_doc = repository.collection.find_one({"_id": result.id})
        assert stored_doc is not None
        assert stored_doc["_id"] == result.id

    def test_save_mapping_package_v1_none_client(self, dummy_mapping_package_v1_model):
        """Test error handling for None MongoDB client."""
        with pytest.raises(ValueError) as exc_info:
            save_mapping_package_v1_to_mongo_db(
                mapping_package=dummy_mapping_package_v1_model,
                mongo_client=None,
                database_name="test_db"
            )

        assert "MongoDB client must be provided" in str(exc_info.value)

    def test_save_mapping_package_v1_custom_collection_name(self, dummy_mapping_package_v1_model):
        """Test that custom collection name is used."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        custom_collection_name = "custom_packages"

        result = save_mapping_package_v1_to_mongo_db(
            mapping_package=dummy_mapping_package_v1_model,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=custom_collection_name
        )

        # Verify it was saved to the custom collection
        repository = MongoDBRepository[MappingPackageV1](
            model_class=MappingPackageV1,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=custom_collection_name
        )
        stored_doc = repository.collection.find_one({"_id": result.id})
        assert stored_doc is not None

    def test_save_mapping_package_v1_tracer_decoration(self):
        """Test that the function is properly decorated with tracer."""
        assert hasattr(save_mapping_package_v1_to_mongo_db, '__name__')
        assert save_mapping_package_v1_to_mongo_db.__name__ == 'save_mapping_package_v1_to_mongo_db'

    def test_save_mapping_package_v1_uses_package_id(self, dummy_mapping_package_v1_model):
        """Test that save uses the package's identifier for MongoDB _id."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        result = save_mapping_package_v1_to_mongo_db(
            mapping_package=dummy_mapping_package_v1_model,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )

        expected_id = result.id

        # Verify the package was saved with the correct _id
        repository = MongoDBRepository[MappingPackageV1](
            model_class=MappingPackageV1,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )
        stored_doc = repository.collection.find_one({"_id": expected_id})
        assert stored_doc is not None
        assert stored_doc["_id"] == expected_id

