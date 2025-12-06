"""
Adapter for saving MappingPackageV2 from archives to MongoDB.

This adapter handles extraction and loading of v2 mapping packages,
then saves them to MongoDB using the save_mapping_package service.
"""
import logging
from pathlib import Path
from typing import Optional

from pymongo import MongoClient

from mapping_suite_sdk.core.adapters.extractor import ArchiveExtractor
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_suite.services.save_mapping_package import (
    save_mapping_package_to_mongo_db
)

logger = logging.getLogger(__name__)


@traced_class
class MappingPackageV2Saver:
    """Saver for MappingPackageV2 from zip archives to MongoDB."""

    def __init__(self, archive_unpacker: Optional[ArchiveExtractor] = None):
        """Initialize the saver.

        Args:
            archive_unpacker: Custom archive extractor instance.
                If None, a default ArchiveExtractor will be used.
        """
        self.archive_unpacker = archive_unpacker or ArchiveExtractor()

    def save_from_archive(
            self,
            mapping_package_archive_path: Path,
            mongo_client: MongoClient,
            database_name: str,
            collection_name: str = "mapping_package"
    ) -> MappingPackageV2:
        """Load a v2 mapping package from a zip archive and save it to MongoDB.

        Args:
            mapping_package_archive_path: Path to the zip archive file.
            mongo_client: MongoDB client instance.
            database_name: Name of the MongoDB database.
            collection_name: Name of the MongoDB collection. Defaults to "mapping_package".

        Returns:
            The loaded and saved mapping package.

        Raises:
            FileNotFoundError: If the archive file does not exist.
            ValueError: If the path is not a file, or if the package cannot be loaded.
        """
        if not mapping_package_archive_path.exists():
            raise FileNotFoundError(
                f"Mapping package archive not found: {mapping_package_archive_path}"
            )

        if not mapping_package_archive_path.is_file():
            raise ValueError(f"Specified path is not a file: {mapping_package_archive_path}")

        # Extract archive temporarily
        with self.archive_unpacker.extract_temporary(mapping_package_archive_path) as temp_folder:
            # Resolve package root (handle nested folder structure)
            package_root = temp_folder
            nested_root = temp_folder / temp_folder.name
            if nested_root.exists() and nested_root.is_dir():
                if (nested_root / "metadata.json").exists():
                    package_root = nested_root

            # Load the package using the adapter loader
            loader = MappingPackageV2Loader()
            mapping_package = loader.load(package_root)

            # Save to MongoDB
            return save_mapping_package_to_mongo_db(
                mapping_package=mapping_package,
                mongo_client=mongo_client,
                database_name=database_name,
                collection_name=collection_name
            )

