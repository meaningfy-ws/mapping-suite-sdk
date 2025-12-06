"""
Unit tests for MappingPackageV3LightweightSaver.

Tests focus on adapter responsibilities:
- Archive extraction
- Package loading
- Integration with save_mapping_package service
"""
from pathlib import Path

import mongomock
import pytest

from mapping_suite_sdk.core.adapters.extractor import ArchiveExtractor
from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_saver import MappingPackageV3LightweightSaver
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight


class TestMappingPackageV3LightweightSaver:
    """Tests for MappingPackageV3LightweightSaver."""

    def test_save_from_archive_success(self, dummy_mapping_package_v3L_archive_path):
        """Test successful saving of a v3L mapping package from archive to MongoDB."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        saver = MappingPackageV3LightweightSaver()
        result = saver.save_from_archive(
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

    def test_save_from_archive_file_not_found(self):
        """Test error handling for non-existent archive file."""
        mongo_client = mongomock.MongoClient()
        non_existent_path = Path("/non/existent/package.zip")

        saver = MappingPackageV3LightweightSaver()
        with pytest.raises(FileNotFoundError) as exc_info:
            saver.save_from_archive(
                mapping_package_archive_path=non_existent_path,
                mongo_client=mongo_client,
                database_name="test_db"
            )

        assert "Mapping package archive not found" in str(exc_info.value)

    def test_save_from_archive_not_a_file(self, tmp_path):
        """Test error handling when path is not a file."""
        mongo_client = mongomock.MongoClient()
        directory_path = tmp_path / "not_a_file"
        directory_path.mkdir()

        saver = MappingPackageV3LightweightSaver()
        with pytest.raises(ValueError) as exc_info:
            saver.save_from_archive(
                mapping_package_archive_path=directory_path,
                mongo_client=mongo_client,
                database_name="test_db"
            )

        assert "Specified path is not a file" in str(exc_info.value)

    def test_save_from_archive_custom_collection_name(self, dummy_mapping_package_v3L_archive_path):
        """Test that custom collection name is used."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        custom_collection_name = "custom_packages"

        saver = MappingPackageV3LightweightSaver()
        result = saver.save_from_archive(
            mapping_package_archive_path=dummy_mapping_package_v3L_archive_path,
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

    def test_save_from_archive_custom_extractor(self, dummy_mapping_package_v3L_archive_path):
        """Test that custom archive extractor can be provided."""
        mongo_client = mongomock.MongoClient()
        custom_extractor = ArchiveExtractor()

        saver = MappingPackageV3LightweightSaver(archive_unpacker=custom_extractor)
        result = saver.save_from_archive(
            mapping_package_archive_path=dummy_mapping_package_v3L_archive_path,
            mongo_client=mongo_client,
            database_name="test_db"
        )

        assert isinstance(result, MappingPackageV3Lightweight)
        assert result.id is not None

    def test_save_from_archive_uses_package_id(self, dummy_mapping_package_v3L_archive_path):
        """Test that save uses the package's identifier for MongoDB _id."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        saver = MappingPackageV3LightweightSaver()
        result = saver.save_from_archive(
            mapping_package_archive_path=dummy_mapping_package_v3L_archive_path,
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

