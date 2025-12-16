"""
Unit tests for MappingPackageV3Saver.

Tests focus on adapter responsibilities:
- Saving package models to MongoDB
"""
import mongomock

from mapping_suite_sdk.core.adapters.extractor import ArchiveExtractor
from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_loader import MappingPackageV3Loader
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_saver import MappingPackageV3Saver
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3


class TestMappingPackageV3Saver:
    """Tests for MappingPackageV3Saver."""

    def test_save_success(self, dummy_mapping_package_v3_archive_path):
        """Test successful saving of a v3 mapping package model to MongoDB."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        # Load package from archive first
        extractor = ArchiveExtractor()
        with extractor.extract_temporary(dummy_mapping_package_v3_archive_path) as temp_folder:
            package_root = temp_folder
            nested_root = temp_folder / temp_folder.name
            if nested_root.exists() and nested_root.is_dir():
                if (nested_root / "metadata.jsonld").exists():
                    package_root = nested_root

            loader = MappingPackageV3Loader()
            mapping_package = loader.load(package_root)

        # Save to MongoDB
        saver = MappingPackageV3Saver()
        result = saver.save(
            mapping_package=mapping_package,
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

    def test_save_custom_collection_name(self, dummy_mapping_package_v3_archive_path):
        """Test that custom collection name is used."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        custom_collection_name = "custom_packages"

        # Load package from archive first
        extractor = ArchiveExtractor()
        with extractor.extract_temporary(dummy_mapping_package_v3_archive_path) as temp_folder:
            package_root = temp_folder
            nested_root = temp_folder / temp_folder.name
            if nested_root.exists() and nested_root.is_dir():
                if (nested_root / "metadata.jsonld").exists():
                    package_root = nested_root

            loader = MappingPackageV3Loader()
            mapping_package = loader.load(package_root)

        # Save to MongoDB
        saver = MappingPackageV3Saver()
        result = saver.save(
            mapping_package=mapping_package,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=custom_collection_name
        )

        # Verify it was saved to the custom collection
        repository = MongoDBRepository[MappingPackageV3](
            model_class=MappingPackageV3,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=custom_collection_name
        )
        stored_doc = repository.collection.find_one({"_id": result.id})
        assert stored_doc is not None

    def test_save_uses_package_id(self, dummy_mapping_package_v3_archive_path):
        """Test that save uses the package's identifier for MongoDB _id."""
        mongo_client = mongomock.MongoClient()
        database_name = "test_db"
        collection_name = "mapping_package"

        # Load package from archive first
        extractor = ArchiveExtractor()
        with extractor.extract_temporary(dummy_mapping_package_v3_archive_path) as temp_folder:
            package_root = temp_folder
            nested_root = temp_folder / temp_folder.name
            if nested_root.exists() and nested_root.is_dir():
                if (nested_root / "metadata.jsonld").exists():
                    package_root = nested_root

            loader = MappingPackageV3Loader()
            mapping_package = loader.load(package_root)

        expected_id = mapping_package.id

        # Save to MongoDB
        saver = MappingPackageV3Saver()
        result = saver.save(
            mapping_package=mapping_package,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )

        # Verify the package was saved with the correct _id
        repository = MongoDBRepository[MappingPackageV3](
            model_class=MappingPackageV3,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )
        stored_doc = repository.collection.find_one({"_id": expected_id})
        assert stored_doc is not None
        assert stored_doc["_id"] == expected_id
        assert result.id == expected_id
