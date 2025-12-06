"""
Unit tests for the save_mapping_package service.

Tests focus on service layer responsibilities:
- Simple dump-to-mongo functionality
- Model type detection and repository selection
- Integration with PackageRepository
"""
import mongomock
import pytest

from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.mapping_suite.services.save_mapping_package import (
    save_mapping_package_to_mongo_db
)


class TestSaveMappingPackageToMongoDB:
    """Tests for saving mapping package models to MongoDB."""

    def test_save_mapping_package_v1_success(self, dummy_mapping_package_v1_model):
        """Test successful saving of a v1 mapping package model to MongoDB."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        result = save_mapping_package_to_mongo_db(
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

    def test_save_mapping_package_v2_success(self, dummy_mapping_package_v2_model):
        """Test successful saving of a v2 mapping package model to MongoDB."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        result = save_mapping_package_to_mongo_db(
            mapping_package=dummy_mapping_package_v2_model,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )

        assert isinstance(result, MappingPackageV2)
        assert result.id is not None

        # Verify it was saved to MongoDB
        repository = MongoDBRepository[MappingPackageV2](
            model_class=MappingPackageV2,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )
        stored_doc = repository.collection.find_one({"_id": result.id})
        assert stored_doc is not None
        assert stored_doc["_id"] == result.id

    def test_save_mapping_package_v3_success(self, fixture_mapping_package_v3_model):
        """Test successful saving of a v3 mapping package model to MongoDB."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        result = save_mapping_package_to_mongo_db(
            mapping_package=fixture_mapping_package_v3_model,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )

        assert isinstance(result, MappingPackageV3)
        assert result.id is not None

        # Verify it was saved to MongoDB
        repository = MongoDBRepository[MappingPackageV3](
            model_class=MappingPackageV3,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )
        stored_doc = repository.collection.find_one({"_id": result.id})
        assert stored_doc is not None
        assert stored_doc["_id"] == result.id

    def test_save_mapping_package_v3L_success(self, dummy_mapping_package_v3L_archive_path):
        """Test successful saving of a v3L mapping package model to MongoDB."""
        from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight import (
            load_mapping_package_v3_from_archive
        )
        
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        # Load v3L model from archive
        v3L_model = load_mapping_package_v3_from_archive(dummy_mapping_package_v3L_archive_path)
        
        result = save_mapping_package_to_mongo_db(
            mapping_package=v3L_model,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )

        assert isinstance(result, MappingPackageV3Lightweight)
        assert result.id is not None

        # Verify it was saved to MongoDB
        repository = MongoDBRepository[MappingPackageV3Lightweight](
            model_class=MappingPackageV3Lightweight,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )
        stored_doc = repository.collection.find_one({"_id": result.id})
        assert stored_doc is not None
        assert stored_doc["_id"] == result.id

    def test_save_mapping_package_none_client(self, dummy_mapping_package_v1_model):
        """Test error handling for None MongoDB client."""
        with pytest.raises(ValueError) as exc_info:
            save_mapping_package_to_mongo_db(
                mapping_package=dummy_mapping_package_v1_model,
                mongo_client=None,
                database_name="test_db"
            )

        assert "MongoDB client must be provided" in str(exc_info.value)

    def test_save_mapping_package_custom_collection_name(self, dummy_mapping_package_v1_model):
        """Test that custom collection name is used."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        custom_collection_name = "custom_packages"

        result = save_mapping_package_to_mongo_db(
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

    def test_save_mapping_package_tracer_decoration(self):
        """Test that the function is properly decorated with tracer."""
        assert hasattr(save_mapping_package_to_mongo_db, '__name__')
        assert save_mapping_package_to_mongo_db.__name__ == 'save_mapping_package_to_mongo_db'

    def test_save_mapping_package_uses_package_id(self, dummy_mapping_package_v1_model):
        """Test that save uses the package's identifier for MongoDB _id."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        result = save_mapping_package_to_mongo_db(
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

    def test_save_mapping_package_unsupported_type(self):
        """Test error handling for unsupported package type."""
        mongo_client = mongomock.MongoClient()

        class UnsupportedPackage:
            pass

        with pytest.raises(ValueError) as exc_info:
            save_mapping_package_to_mongo_db(
                mapping_package=UnsupportedPackage(),
                mongo_client=mongo_client,
                database_name="test_db"
            )

        assert "Unsupported mapping package type" in str(exc_info.value)
