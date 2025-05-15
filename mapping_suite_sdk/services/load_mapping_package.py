import logging
from pathlib import Path
from typing import Optional, List

from pydantic import ValidationError

from mapping_suite_sdk.adapters.extractor import ArchivePackageExtractor, GithubPackageExtractor
from mapping_suite_sdk.adapters.loader import MappingPackageAssetLoader, MappingPackageLoader
from mapping_suite_sdk.adapters.repository import MongoDBRepository
from mapping_suite_sdk.adapters.tracer import traced_routine
from mapping_suite_sdk.models.mapping_package import MappingPackage
from mapping_suite_sdk.vars import MSSDK_LOGGING_MESSAGE_FORMAT

logger = logging.getLogger(__name__)


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
        raise NotADirectoryError(f"Specified path is not a directory: {mapping_package_folder_path}")

    mapping_package_loader = mapping_package_loader or MappingPackageLoader()

    return mapping_package_loader.load(mapping_package_folder_path)


@traced_routine
def load_mapping_package_from_archive(
        mapping_package_archive_path: Path,
        mapping_package_loader: Optional[MappingPackageAssetLoader] = None,
        archive_unpacker: Optional[ArchivePackageExtractor] = None
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

    archive_unpacker: ArchivePackageExtractor = archive_unpacker or ArchivePackageExtractor()

    with archive_unpacker.extract_temporary(mapping_package_archive_path) as temp_mapping_package_folder_path:

        return load_mapping_package_from_folder(mapping_package_folder_path=temp_mapping_package_folder_path,
                                                mapping_package_loader=mapping_package_loader)


@traced_routine
def load_mapping_packages_from_github(
        github_repository_url: str,
        packages_path_pattern: str,
        branch_or_tag_name: Optional[str] = None,
        github_package_extractor: Optional[GithubPackageExtractor] = None,
        mapping_package_loader: Optional[MappingPackageAssetLoader] = None,
) -> List[MappingPackage]:
    """Load mapping packages from a GitHub repository.

    This function downloads mapping packages from a GitHub repository and loads them.
    It supports loading multiple packages that match a specified path pattern within
    the repository. The function uses shallow cloning to minimize download size and
    automatically cleans up temporary files after loading. If a package is not valid,
    it will be skipped and a warning will be logged.

    The function follows these steps:
    1. Clones the specified repository (shallow clone)
    2. Finds all directories matching the packages_path_pattern
    3. Loads each matching directory as a mapping package
    4. Cleans up temporary files
    5. Returns the list of loaded packages

    Args:
        github_repository_url: The URL of the GitHub repository. Must be a valid GitHub
            repository URL (e.g., "https://github.com/org/repo").
        packages_path_pattern: Glob pattern to match package paths within the repository.
            The pattern is relative to the repository root and supports glob-style
            matching (e.g., "mappings/package*" or "mappings/*_can_*").
        branch_or_tag_name: Name of the branch, tag, or commit to checkout. This allows
            loading packages from specific versions or development branches
            (e.g., "main", "v1.0.0", "feature/new-mapping").
        github_package_extractor: Optional custom GitHub extractor implementation.
            If not provided, a default GithubPackageExtractor will be used.
            This allows for custom GitHub interaction strategies if needed.
        mapping_package_loader: Optional custom loader implementation for reading
            the mapping package contents. If not provided, a default
            MappingPackageLoader will be used.

    Returns:
        List[MappingPackage]: A list of loaded mapping packages. Each package
            contains all components including technical mappings, vocabulary
            mappings, test suites, and metadata. The list will be empty if no
            packages are found matching the pattern.

    Raises:
        ValueError: If any of the following conditions are met:
            - repository_url is empty or invalid
            - packages_path_pattern is empty
            - No packages are found matching the pattern
            - Repository cloning fails
        git.exc.GitCommandError: If there are Git-specific errors (e.g., repository
            not found, invalid branch name)
        Exception: Any additional exceptions that might be raised during package
            loading or processing

    Example:
        >>> # Load all packages from a specific branch
        >>> packages = load_mapping_packages_from_github(
        ...     repository_url="https://github.com/org/repo",
        ...     packages_path_pattern="mappings/package*",
        ...     branch_or_tag_name="main"
        ... )
        >>> for package in packages:
        ...     print(f"Loaded package: {package.metadata.name}")

        >>> # Load packages with custom loader and specific version
        >>> custom_loader = CustomMappingPackageLoader()
        >>> packages = load_mapping_packages_from_github(
        ...     repository_url="https://github.com/org/repo",
        ...     packages_path_pattern="mappings/*_can_*",
        ...     branch_or_tag_name="v1.0.0",
        ...     mapping_package_loader=custom_loader
        ... )

    Note:
        - The function uses shallow cloning (depth=1) to minimize download size
          and time.
        - Temporary files are automatically cleaned up after loading, regardless
          of success or failure.
        - The packages_path_pattern supports glob-style patterns for flexible
          package matching.
        - The function can handle multiple packages in a single repository,
          returning them as a list.
    """

    if not github_repository_url:
        raise ValueError("Repository URL is required")

    if not packages_path_pattern:
        raise ValueError("Packages path pattern is required")

    github_extractor = github_package_extractor or GithubPackageExtractor()

    with github_extractor.extract_temporary(repository_url=github_repository_url,
                                            packages_path_pattern=packages_path_pattern,
                                            branch_or_tag_name=branch_or_tag_name
                                            ) as package_paths:
        if len(package_paths) < 1:
            raise ValueError(
                f"No mapping packages found matching pattern '{packages_path_pattern}' "
                f"in repository {github_repository_url} at {branch_or_tag_name}")

        mapping_packages: List[MappingPackage] = []
        for package_path in package_paths:
            try:
                package = load_mapping_package_from_folder(
                    mapping_package_folder_path=package_path,
                    mapping_package_loader=mapping_package_loader
                )
                mapping_packages.append(package)
            except (ValidationError, Exception) as pydantic_validation_error:
                logger.warning(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=package_path,
                                                                   message=f"Cannot load package {package_path} from GitHub:\n{pydantic_validation_error}\nSkipping {package_path}"))
        return mapping_packages


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
