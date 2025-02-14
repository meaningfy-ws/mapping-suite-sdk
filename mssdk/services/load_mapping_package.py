import shutil
import tempfile
from pathlib import Path
from typing import Optional

from mssdk.adapters.loader import MappingPackageAssetLoader, MappingPackageLoader
from mssdk.models.mapping_package import MappingPackage


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


def load_mapping_package_from_zip_file(
        mapping_package_zip_path: Path,
        mapping_package_loader: Optional[MappingPackageAssetLoader] = None
) -> MappingPackage:
    """
    Load a mapping package from a ZIP archive.

    Args:
        mapping_package_zip_path: Path to the mapping package ZIP archive
        mapping_package_loader: Optional custom loader implementation. If not provided,
                              a default MappingPackageLoader will be used.

    Returns:
        MappingPackage: The loaded mapping package with all its components

    Raises:
        FileNotFoundError: If the archive file doesn't exist
        ValueError: If the path is not a file or if the archive format is invalid
        zipfile.BadZipFile: If the archive is corrupted or invalid
    """

    if not mapping_package_zip_path.exists():
        raise FileNotFoundError(f"Mapping package archive not found: {mapping_package_zip_path}")

    if not mapping_package_zip_path.is_file():
        raise ValueError(f"Specified path is not a file: {mapping_package_zip_path}")

    with tempfile.TemporaryDirectory() as temp_mapping_package_dir:
        temp_mapping_package_dir_path: Path = Path(temp_mapping_package_dir)

        temp_mapping_package_folder_path: Path = temp_mapping_package_dir_path / mapping_package_zip_path.stem
        temp_mapping_package_folder_path.mkdir()

        try:
            shutil.unpack_archive(mapping_package_zip_path, temp_mapping_package_folder_path)
        except shutil.ReadError as e:
            raise ValueError(f"Failed to extract archive: {e}")

        return load_mapping_package_from_folder(mapping_package_folder_path=temp_mapping_package_folder_path,
                                                mapping_package_loader=mapping_package_loader)
