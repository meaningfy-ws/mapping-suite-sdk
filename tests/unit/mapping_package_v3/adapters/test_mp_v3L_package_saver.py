"""
Unit tests for MappingPackageV3LightweightSaver.

Tests focus on adapter responsibilities:
- Saving package models to MongoDB
"""
import mongomock

from mapping_suite_sdk.core.adapters.extractor import ArchiveExtractor
from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_loader import (
    MappingPackageV3LightweightLoader
)
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_saver import MappingPackageV3LightweightSaver
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight


class TestMappingPackageV3LightweightSaver:
    """Tests for MappingPackageV3LightweightSaver."""

    def test_save_success(self, dummy_mapping_package_v3L_archive_path):
        """Test successful saving of a v3L mapping package model to MongoDB."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        # Load package from archive first
        extractor = ArchiveExtractor()
        with extractor.extract_temporary(dummy_mapping_package_v3L_archive_path) as temp_folder:
            package_root = temp_folder
            nested_root = temp_folder / temp_folder.name
            if nested_root.exists() and nested_root.is_dir():
                if (nested_root / "metadata.jsonld").exists():
                    package_root = nested_root

            loader = MappingPackageV3LightweightLoader()
            mapping_package = loader.load(package_root)

        # Save to MongoDB
        saver = MappingPackageV3LightweightSaver()
        result = saver.save(
            mapping_package=mapping_package,
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

    def test_save_custom_collection_name(self, dummy_mapping_package_v3L_archive_path):
        """Test that custom collection name is used."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        custom_collection_name = "custom_packages"

        # Load package from archive first
        extractor = ArchiveExtractor()
        with extractor.extract_temporary(dummy_mapping_package_v3L_archive_path) as temp_folder:
            package_root = temp_folder
            nested_root = temp_folder / temp_folder.name
            if nested_root.exists() and nested_root.is_dir():
                if (nested_root / "metadata.jsonld").exists():
                    package_root = nested_root

            loader = MappingPackageV3LightweightLoader()
            mapping_package = loader.load(package_root)

        # Save to MongoDB
        saver = MappingPackageV3LightweightSaver()
        result = saver.save(
            mapping_package=mapping_package,
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

    def test_save_uses_package_id(self, dummy_mapping_package_v3L_archive_path):
        """Test that save uses the package's identifier for MongoDB _id."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        # Load package from archive first
        extractor = ArchiveExtractor()
        with extractor.extract_temporary(dummy_mapping_package_v3L_archive_path) as temp_folder:
            package_root = temp_folder
            nested_root = temp_folder / temp_folder.name
            if nested_root.exists() and nested_root.is_dir():
                if (nested_root / "metadata.jsonld").exists():
                    package_root = nested_root

            loader = MappingPackageV3LightweightLoader()
            mapping_package = loader.load(package_root)

        expected_id = mapping_package.id

        # Save to MongoDB
        saver = MappingPackageV3LightweightSaver()
        result = saver.save(
            mapping_package=mapping_package,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )

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
        assert result.id == expected_id
