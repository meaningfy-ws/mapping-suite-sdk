from pathlib import Path
from typing import Optional, List

from mapping_suite_sdk.adapters.extractor import ArchivePackageExtractor, GithubPackageExtractor
from mapping_suite_sdk.adapters.loader import MappingPackageAssetLoader, MappingPackageLoader
from mapping_suite_sdk.models.mapping_package import MappingPackage


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


def load_mapping_packages_from_github(
        github_repository_url: str,
        packages_path_pattern: str,
        branch_or_tag_name: str,
        github_package_extractor: Optional[GithubPackageExtractor] = None,
        mapping_package_loader: Optional[MappingPackageAssetLoader] = None,
) -> List[MappingPackage]:
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

        return [
            load_mapping_package_from_folder(
                mapping_package_folder_path=package_path,
                mapping_package_loader=mapping_package_loader
            )
            for package_path in package_paths]
