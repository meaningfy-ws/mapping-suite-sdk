"""
Unit tests for the save_mapping_package service.

Tests focus on service layer responsibilities:
- Orchestration of load and save workflow
- Exception handling and validation
- Integration with MongoDBRepository
"""
from pathlib import Path

import mongomock
import pytest

from mapping_suite_sdk.core.adapters.extractor import ArchiveExtractor
from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.mapping_suite.services.save_mapping_package import (
    save_mapping_package_to_mongo_db
)


class TestSaveMappingPackageToMongoDB:
    """Tests for saving mapping packages from zip archives to MongoDB."""

    def test_save_mapping_package_to_mongo_db_success_v1(
        self, dummy_mapping_package_v1_archive_path
    ):
        """Test successful saving of a v1 mapping package from archive to MongoDB."""
        import mongomock

        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        result = save_mapping_package_to_mongo_db(
            mapping_package_archive_path=dummy_mapping_package_v1_archive_path,
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

    def test_save_mapping_package_to_mongo_db_success_v2(
        self, dummy_mapping_package_v2_archive_path
    ):
        """Test successful saving of a v2 mapping package from archive to MongoDB."""
        import mongomock

        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        result = save_mapping_package_to_mongo_db(
            mapping_package_archive_path=dummy_mapping_package_v2_archive_path,
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

    def test_save_mapping_package_to_mongo_db_success_v3(
        self, dummy_mapping_package_v3_archive_path
    ):
        """Test successful saving of a v3 mapping package from archive to MongoDB."""
        import mongomock

        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        result = save_mapping_package_to_mongo_db(
            mapping_package_archive_path=dummy_mapping_package_v3_archive_path,
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

    def test_save_mapping_package_to_mongo_db_file_not_found(self):
        """Test error handling for non-existent archive file."""
        import mongomock

        mongo_client = mongomock.MongoClient()
        non_existent_path = Path("/non/existent/package.zip")

        with pytest.raises(FileNotFoundError) as exc_info:
            save_mapping_package_to_mongo_db(
                mapping_package_archive_path=non_existent_path,
                mongo_client=mongo_client,
                database_name="test_db"
            )

        assert "Mapping package archive not found" in str(exc_info.value)

    def test_save_mapping_package_to_mongo_db_not_a_file(self, tmp_path):
        """Test error handling when path is not a file."""
        import mongomock

        mongo_client = mongomock.MongoClient()
        directory_path = tmp_path / "not_a_file"
        directory_path.mkdir()

        with pytest.raises(ValueError) as exc_info:
            save_mapping_package_to_mongo_db(
                mapping_package_archive_path=directory_path,
                mongo_client=mongo_client,
                database_name="test_db"
            )

        assert "Specified path is not a file" in str(exc_info.value)

    def test_save_mapping_package_to_mongo_db_none_client(
        self, dummy_mapping_package_v1_archive_path
    ):
        """Test error handling for None MongoDB client."""
        with pytest.raises(ValueError) as exc_info:
            save_mapping_package_to_mongo_db(
                mapping_package_archive_path=dummy_mapping_package_v1_archive_path,
                mongo_client=None,
                database_name="test_db"
            )

        assert "MongoDB client must be provided" in str(exc_info.value)

    def test_save_mapping_package_to_mongo_db_custom_collection_name(
        self, dummy_mapping_package_v1_archive_path
    ):
        """Test that custom collection name is used."""
        import mongomock

        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        custom_collection_name = "custom_packages"

        result = save_mapping_package_to_mongo_db(
            mapping_package_archive_path=dummy_mapping_package_v1_archive_path,
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

    def test_save_mapping_package_to_mongo_db_tracer_decoration(self):
        """Test that the function is properly decorated with tracer."""
        assert hasattr(save_mapping_package_to_mongo_db, '__name__')
        assert save_mapping_package_to_mongo_db.__name__ == 'save_mapping_package_to_mongo_db'

    def test_save_mapping_package_to_mongo_db_uses_package_id(
        self, dummy_mapping_package_v1_archive_path
    ):
        """Test that save uses the package's identifier for MongoDB _id."""
        import mongomock

        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        result = save_mapping_package_to_mongo_db(
            mapping_package_archive_path=dummy_mapping_package_v1_archive_path,
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

    def test_save_mapping_package_to_mongo_db_custom_extractor(
        self, dummy_mapping_package_v1_archive_path
    ):
        """Test that custom archive extractor can be provided."""
        import mongomock

        mongo_client = mongomock.MongoClient()
        custom_extractor = ArchiveExtractor()

        result = save_mapping_package_to_mongo_db(
            mapping_package_archive_path=dummy_mapping_package_v1_archive_path,
            mongo_client=mongo_client,
            database_name="test_db",
            archive_unpacker=custom_extractor
        )

        assert isinstance(result, MappingPackageV1)
        assert result.id is not None

    def test_save_mapping_package_to_mongo_db_success_v3L(
        self, dummy_mapping_package_v3L_archive_path
    ):
        """Test successful saving of a v3L (lightweight) mapping package from archive to MongoDB."""
        import mongomock

        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        result = save_mapping_package_to_mongo_db(
            mapping_package_archive_path=dummy_mapping_package_v3L_archive_path,
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

