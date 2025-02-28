from pathlib import Path
from typing import Optional

from mapping_suite_sdk.adapters.extractor import ArchiveExtractor
from mapping_suite_sdk.adapters.loader import MappingPackageAssetLoader, MappingPackageLoader
from mapping_suite_sdk.adapters.repository import MongoDBRepository
from mapping_suite_sdk.adapters.tracer import traced_routine
from mapping_suite_sdk.models.mapping_package import MappingPackage


@traced_routine
def load_mapping_package_from_folder(
        mapping_package_folder_path: Path,
        mapping_package_loader: Optional[MappingPackageAssetLoader] = None
) -> MappingPackage:
    """
    Load a mapping package from a folder path.

    This function loads a mapping package from a specified directory. The mapping package
    is expected to follow the standard structure with subdirectories for mappings,
    resources, test data, and validation rules.

    Args:
        mapping_package_folder_path: Path to the mapping package folder. The folder must exist
            and contain the required mapping package structure.
        mapping_package_loader: Optional custom loader implementation. If not provided,
            a default MappingPackageLoader will be used. This allows for custom loading
            strategies if needed.

    Returns:
        MappingPackage: The loaded mapping package containing all components including
            technical mappings, vocabulary mappings, test suites, and metadata.

    Raises:
        FileNotFoundError: If the specified mapping package folder does not exist
        ValueError: If the specified path is not a directory
        Exception: Any additional exceptions that might be raised by the loader implementation
    """
    if not mapping_package_folder_path.exists():
        raise FileNotFoundError(f"Mapping package folder not found: {mapping_package_folder_path}")
    if not mapping_package_folder_path.is_dir():
        raise ValueError(f"Specified path is not a directory: {mapping_package_folder_path}")

    mapping_package_loader = mapping_package_loader or MappingPackageLoader()

    return mapping_package_loader.load(mapping_package_folder_path)


@traced_routine
def load_mapping_package_from_archive(
        mapping_package_archive_path: Path,
        mapping_package_loader: Optional[MappingPackageAssetLoader] = None,
        archive_unpacker: Optional[ArchiveExtractor] = None
) -> MappingPackage:
    """Load a mapping package from an archive file.

    This function extracts an archive containing a mapping package to a temporary location
    and loads its contents. The temporary files are automatically cleaned up after loading
    is complete.

    Args:
        mapping_package_archive_path: Path to the archive file containing the mapping package
        mapping_package_loader: Optional custom loader implementation for reading the mapping
            package contents. If not provided, a default MappingPackageLoader will be used
        archive_unpacker: Optional custom archive unpacker implementation. If not provided,
            a default ArchiveUnpacker will be used

    Returns:
        MappingPackage: The loaded mapping package containing all components including
            technical mappings, vocabulary mappings, test suites, and metadata

    Raises:
        FileNotFoundError: If the archive file doesn't exist
        ValueError: If the specified path is not a file
        Exception: Any additional exceptions that might be raised during archive extraction
            or mapping package loading
    """
    if not mapping_package_archive_path.exists():
        raise FileNotFoundError(f"Mapping package archive not found: {mapping_package_archive_path}")

    if not mapping_package_archive_path.is_file():
        raise ValueError(f"Specified path is not a file: {mapping_package_archive_path}")

    archive_unpacker: ArchiveExtractor = archive_unpacker or ArchiveExtractor()

    with archive_unpacker.extract_temporary(mapping_package_archive_path) as temp_mapping_package_folder_path:

        return load_mapping_package_from_folder(mapping_package_folder_path=temp_mapping_package_folder_path,
                                                mapping_package_loader=mapping_package_loader)


@traced_routine
def load_mapping_package_from_mongo_db(
        mapping_package_id: str,
        mapping_package_repository: MongoDBRepository[MappingPackage]
) -> MappingPackage:
    """
    Load a mapping package from a MongoDB database.

    This function retrieves a mapping package from a MongoDB database using its unique ID.
    The mapping package is retrieved using a provided MongoDB repository instance, which
    should be configured with the appropriate database connection and collection settings.

    Args:
        mapping_package_id: The unique identifier of the mapping package to load. This ID
            corresponds to the '_id' field in the MongoDB collection.
        mapping_package_repository: A configured MongoDBRepository instance specifically for
            MappingPackage objects. This repository should already be initialized with the
            correct MongoDB client, database name, and collection name.

    Returns:
        MappingPackage: The loaded mapping package containing all components including
            technical mappings, vocabulary mappings, test suites, and metadata.

    Raises:
        ValueError: If mapping_package_id or mapping_package_repository is not provided
        ModelNotFoundError: If the mapping package with the specified ID is not found
        Exception: Any additional exceptions that might be raised by the repository
            implementation during the read operation
    """
    if not mapping_package_id:
        raise ValueError("Mapping package ID must be provided")

    if not mapping_package_repository:
        raise ValueError("MongoDB repository must be provided")

    return mapping_package_repository.read(mapping_package_id)
