"""
Service for saving mapping packages from zip archives to MongoDB.

This module provides functionality to load mapping packages from zip files,
detect their version, and persist them to a MongoDB database using the
MongoDBRepository pattern.
"""
import logging
from pathlib import Path
from typing import Optional, Union

from pymongo import MongoClient

from mapping_suite_sdk.core.adapters.extractor import ArchiveExtractor
from mapping_suite_sdk.core.adapters.package_repository import PackageRepository
from mapping_suite_sdk.core.adapters.tracer import traced_routine
# Import from __init__ to ensure id property is patched
from mapping_suite_sdk.mapping_package_v1.models import MappingPackageV1
from mapping_suite_sdk.mapping_package_v2.models import MappingPackageV2
from mapping_suite_sdk.mapping_package_v3.models import MappingPackageV3, MappingPackageV3Lightweight

logger = logging.getLogger(__name__)


@traced_routine
def save_mapping_package_to_mongo_db(
        mapping_package_archive_path: Path,
        mongo_client: MongoClient,
        database_name: str,
        collection_name: str = "mapping_package",
        archive_unpacker: Optional[ArchiveExtractor] = None
) -> Union[MappingPackageV1, MappingPackageV2, MappingPackageV3, MappingPackageV3Lightweight]:
    """Load a mapping package from a zip archive and save it to MongoDB.

    This function:
    1. Extracts the archive to a temporary location
    2. Tries to load the package using each version's loader until one succeeds
    3. Saves it to MongoDB in the specified collection

    Args:
        mapping_package_archive_path (Path): Path to the zip archive file containing
            the mapping package.
        mongo_client (MongoClient): MongoDB client instance for database access.
        database_name (str): Name of the MongoDB database.
        collection_name (str): Name of the MongoDB collection. Defaults to "mapping_package".
        archive_unpacker (Optional[ArchiveExtractor]): Custom archive extractor instance.
            If None, a default ArchiveExtractor will be used.

    Returns:
        Union[MappingPackageV1, MappingPackageV2, MappingPackageV3, MappingPackageV3Lightweight]:
            The loaded and saved mapping package.

    Raises:
        FileNotFoundError: If the archive file does not exist.
        ValueError: If the path is not a file, or if the package cannot be loaded with any version's loader.
        Exception: If database access fails (propagated from repository).
    """
    if not mapping_package_archive_path.exists():
        raise FileNotFoundError(
            f"Mapping package archive not found: {mapping_package_archive_path}"
        )

    if not mapping_package_archive_path.is_file():
        raise ValueError(f"Specified path is not a file: {mapping_package_archive_path}")

    if not mongo_client:
        raise ValueError("MongoDB client must be provided")

    archive_unpacker = archive_unpacker or ArchiveExtractor()

    # Extract archive temporarily
    with archive_unpacker.extract_temporary(mapping_package_archive_path) as temp_folder:
        # Resolve package root (handle nested folder structure)
        package_root = temp_folder
        nested_root = temp_folder / temp_folder.name
        if nested_root.exists() and nested_root.is_dir():
            if (nested_root / "metadata.json").exists() or (nested_root / "metadata.jsonld").exists():
                package_root = nested_root

        # Determine version
        version = _determine_package_version(package_root)
        
        # Load and save based on version
        if version == "v1":
            from mapping_suite_sdk.mapping_package_v1.services.load_mapping_package_v1 import (
                load_mapping_package_v1_from_folder
            )
            mapping_package = load_mapping_package_v1_from_folder(
                mapping_package_folder_path=package_root
            )
            repository = PackageRepository[MappingPackageV1](
                model_class=MappingPackageV1,
                mongo_client=mongo_client,
                database_name=database_name,
                collection_name=collection_name
            )
            return repository.create_package(mapping_package)

        if version == "v2":
            from mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2 import (
                load_mapping_package_v2_from_folder
            )
            mapping_package = load_mapping_package_v2_from_folder(
                mapping_package_folder_path=package_root
            )
            repository = PackageRepository[MappingPackageV2](
                model_class=MappingPackageV2,
                mongo_client=mongo_client,
                database_name=database_name,
                collection_name=collection_name
            )
            return repository.create_package(mapping_package)

        if version == "v3":
            from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3 import (
                load_mapping_package_v3_from_folder
            )
            mapping_package = load_mapping_package_v3_from_folder(
                mapping_package_folder_path=package_root
            )
            repository = PackageRepository[MappingPackageV3](
                model_class=MappingPackageV3,
                mongo_client=mongo_client,
                database_name=database_name,
                collection_name=collection_name
            )
            return repository.create_package(mapping_package)

        if version == "v3L":
            from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight import (
                load_mapping_package_v3_from_folder
            )
            mapping_package = load_mapping_package_v3_from_folder(
                mapping_package_folder_path=package_root
            )
            repository = PackageRepository[MappingPackageV3Lightweight](
                model_class=MappingPackageV3Lightweight,
                mongo_client=mongo_client,
                database_name=database_name,
                collection_name=collection_name
            )
            return repository.create_package(mapping_package)


def _determine_package_version(package_root: Path) -> str:
    """Determine mapping package version from package root folder structure.
    
    Args:
        package_root: Root path of the extracted package
        
    Returns:
        Version string: "v1", "v2", "v3", or "v3L"
    """
    # Check for metadata.jsonld (v3)
    metadata_jsonld = package_root / "metadata.jsonld"
    if metadata_jsonld.exists():
        # Check if it's lightweight by looking for test_data folder
        test_data_path = package_root / "test_data"
        if not test_data_path.exists():
            return "v3L"
        else:
            return "v3"

    # Check for metadata.json (v1 or v2)
    metadata_json = package_root / "metadata.json"
    if metadata_json.exists():
        import json
        with metadata_json.open(encoding='utf-8') as f:
            metadata_content = json.load(f)
        
        # Check for v2 indicator: eforms_sdk_versions in constraints
        constraints = metadata_content.get("metadata_constraints", {}).get("constraints", {})
        if "eforms_sdk_versions" in constraints:
            return "v2"

    # Default to v1
    return "v1"

