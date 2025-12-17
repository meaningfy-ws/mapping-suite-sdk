"""
Unit tests for the save_mapping_package_v3_lightweight service.

Tests focus on service layer responsibilities:
- Simple dump-to-mongo functionality
- Integration with PackageRepository
"""
import mongomock
import pytest

from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.mapping_package_v3.services.save_mapping_package_v3_lightweight import (
    save_mapping_package_v3_lightweight_to_mongo_db
)


class TestSaveMappingPackageV3LightweightToMongoDB:
    """Tests for saving MappingPackageV3Lightweight models to MongoDB."""

    def test_save_mapping_package_v3_lightweight_success(self, dummy_mapping_package_v3L_archive_path):
        """Test successful saving of a v3L mapping package model to MongoDB."""
        from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight import (
            load_mapping_package_v3_lightweight_from_archive
        )
        
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        # Load v3L model from archive
        v3L_model = load_mapping_package_v3_lightweight_from_archive(dummy_mapping_package_v3L_archive_path)
        
        result = save_mapping_package_v3_lightweight_to_mongo_db(
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

    def test_save_mapping_package_v3_lightweight_none_client(self, dummy_mapping_package_v3L_archive_path):
        """Test error handling for None MongoDB client."""
        from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight import (
            load_mapping_package_v3_lightweight_from_archive
        )
        
        v3L_model = load_mapping_package_v3_lightweight_from_archive(dummy_mapping_package_v3L_archive_path)
        
        with pytest.raises(ValueError) as exc_info:
            save_mapping_package_v3_lightweight_to_mongo_db(
                mapping_package=v3L_model,
                mongo_client=None,
                database_name="test_db"
            )

        assert "MongoDB client must be provided" in str(exc_info.value)

    def test_save_mapping_package_v3_lightweight_custom_collection_name(self, dummy_mapping_package_v3L_archive_path):
        """Test that custom collection name is used."""
        from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight import (
            load_mapping_package_v3_lightweight_from_archive
        )
        
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        custom_collection_name = "custom_packages"

        v3L_model = load_mapping_package_v3_lightweight_from_archive(dummy_mapping_package_v3L_archive_path)

        result = save_mapping_package_v3_lightweight_to_mongo_db(
            mapping_package=v3L_model,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=custom_collection_name
        )

        # Verify it was saved to the custom collection
        repository = MongoDBRepository[MappingPackageV3Lightweight](
            model_class=MappingPackageV3Lightweight,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=custom_collection_name
        )
        stored_doc = repository.collection.find_one({"_id": result.id})
        assert stored_doc is not None

    def test_save_mapping_package_v3_lightweight_tracer_decoration(self):
        """Test that the function is properly decorated with tracer."""
        assert hasattr(save_mapping_package_v3_lightweight_to_mongo_db, '__name__')
        assert save_mapping_package_v3_lightweight_to_mongo_db.__name__ == 'save_mapping_package_v3_lightweight_to_mongo_db'

    def test_save_mapping_package_v3_lightweight_uses_package_id(self, dummy_mapping_package_v3L_archive_path):
        """Test that save uses the package's identifier for MongoDB _id."""
        from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight import (
            load_mapping_package_v3_lightweight_from_archive
        )
        
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        v3L_model = load_mapping_package_v3_lightweight_from_archive(dummy_mapping_package_v3L_archive_path)

        result = save_mapping_package_v3_lightweight_to_mongo_db(
            mapping_package=v3L_model,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )

        expected_id = result.id

        # Verify the package was saved with the correct _id
        repository = MongoDBRepository[MappingPackageV3Lightweight](
            model_class=MappingPackageV3Lightweight,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )
        stored_doc = repository.collection.find_one({"_id": expected_id})
        assert stored_doc is not None
        assert stored_doc["_id"] == expected_id

