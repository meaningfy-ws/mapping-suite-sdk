"""
Orchestration service for converting mapping packages.

This service handles the complete workflow:
1. Loading packages from filesystem
2. Converting between versions
3. Serializing back to filesystem
4. Handling file operations (context.jsonld, metadata cleanup, etc.)
"""
import importlib.resources
import logging
import shutil
from enum import Enum
from pathlib import Path
from typing import Union

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.adapters.version_detector import _resolve_package_root
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader
from mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2 import load_mapping_package_v2_from_folder
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_loader import MappingPackageV3Loader
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser import MappingPackageV3Serialiser
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_serialiser import MappingPackageV3LightweightSerialiser
from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3 import load_mapping_package_v3_from_folder
from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import (
    convert_mapping_package_v2_to_v3,
    is_mapping_package_already_converted  # Re-export for convenience
)
from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import (
    convert_mapping_package_v3_to_v3_lightweight
)

logger = logging.getLogger(__name__)


class Version(str, Enum):
    """Mapping package versions supported by the SDK."""
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"
    V3L = "v3L"


class ConversionError(Exception):
    """Base exception for conversion errors."""
    pass


class UnsupportedVersionError(ConversionError):
    """Raised when an unsupported version is specified."""
    pass


class InvalidPackagePathError(ConversionError):
    """Raised when package path is invalid."""
    pass


def load_mapping_package_from_folder(from_version: str, mapping_package_folder_path: Path):
    """
    Load a mapping package from filesystem based on version.

    Args:
        from_version: Source version (v2 or v3)
        mapping_package_folder_path: Path to the mapping package folder

    Returns:
        Loaded mapping package model

    Raises:
        UnsupportedVersionError: If from_version is not supported
        InvalidPackagePathError: If path is invalid
    """
    if not mapping_package_folder_path.exists():
        raise InvalidPackagePathError(f"Package path does not exist: {mapping_package_folder_path}")
    if not mapping_package_folder_path.is_dir():
        raise InvalidPackagePathError(f"Package path is not a directory: {mapping_package_folder_path}")

    if from_version == Version.V2:
        loader = MappingPackageV2Loader()
        return load_mapping_package_v2_from_folder(
            mapping_package_folder_path=mapping_package_folder_path,
            mapping_package_loader=loader
        )
    elif from_version == Version.V3:
        loader = MappingPackageV3Loader()
        return load_mapping_package_v3_from_folder(
            mapping_package_folder_path=mapping_package_folder_path,
            mapping_package_loader=loader
        )
    else:
        raise UnsupportedVersionError(f"Unsupported source version: {from_version}")


def convert_mapping_package_model(from_version: str, to_version: str, source_package):
    """
    Convert mapping package model between versions.

    Args:
        from_version: Source version
        to_version: Target version
        source_package: Source package model

    Returns:
        Converted package model

    Raises:
        UnsupportedVersionError: If conversion is not supported
    """
    if from_version == Version.V2 and to_version == Version.V3:
        return convert_mapping_package_v2_to_v3(source_package)
    elif from_version == Version.V3 and to_version == Version.V3L:
        return convert_mapping_package_v3_to_v3_lightweight(source_package)
    else:
        raise UnsupportedVersionError(f"Unsupported conversion: {from_version} -> {to_version}")


def _get_context_jsonld_path() -> Path:
    """
    Get the path to context.jsonld file using importlib.resources.

    Works both in installed package (via importlib.resources) and development environment
    (by finding resources relative to package location).

    Returns:
        Path to context.jsonld file

    Raises:
        FileNotFoundError: If context.jsonld file cannot be found
    """
    package_ref = importlib.resources.files("mapping_suite_sdk")
    package_path = Path(package_ref)
    project_root = package_path.parent
    context_path = project_root / "resources" / "schema" / "mapping_package_v3" / "models" / "context.jsonld"

    if not context_path.exists():
        raise FileNotFoundError(
            f"context.jsonld not found at {context_path}. "
            f"Run 'make generate-models' to generate it."
        )

    return context_path


def _copy_context_jsonld_to_package(mapping_package_folder_path: Path, converted_package) -> None:
    """
    Copy context.jsonld from schema directory to the package.

    The context.jsonld file is generated in the schema directory when models are generated.
    This function copies it to the same directory as metadata.jsonld in the package.

    Args:
        mapping_package_folder_path: Path to the mapping package folder
        converted_package: The converted package (V3 or V3L) containing metadata with path information

    Raises:
        FileNotFoundError: If context.jsonld file cannot be found in schema directory
    """
    schema_context_path = _get_context_jsonld_path()
    metadata_path = mapping_package_folder_path / converted_package.metadata.path
    metadata_directory = metadata_path.parent
    package_context_path = metadata_directory / "context.jsonld"

    shutil.copy2(schema_context_path, package_context_path)
    logger.debug(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=mapping_package_folder_path,
        message=f"Copied context.jsonld from {schema_context_path} to {package_context_path}"))


def _remove_old_metadata_json(mapping_package_folder_path: Path) -> None:
    """
    Remove old metadata.json file when converting to V3.

    V2 uses metadata.json, but V3 uses metadata.jsonld. If both exist after conversion,
    validation may check the wrong file or emit warnings. This ensures only metadata.jsonld
    exists after conversion.

    Handles both flat and nested package structures.

    Args:
        mapping_package_folder_path: Path to the mapping package folder
    """
    package_root = _resolve_package_root(mapping_package_folder_path)
    if package_root is None:
        package_root = mapping_package_folder_path

    old_metadata_path = package_root / "metadata.json"
    if old_metadata_path.exists():
        old_metadata_path.unlink()
        logger.debug(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
            package_source=mapping_package_folder_path,
            message=f"Removed old metadata.json file from {old_metadata_path}"))


def _remove_conceptual_mapping_file(mapping_package_folder_path: Path) -> None:
    """
    Remove conceptual_mappings.xlsx file when converting to V3L.

    V3 Full includes conceptual_mappings.xlsx, but V3L does not. If the file exists after
    conversion to V3L, version detection may incorrectly identify it as V3 Full.

    Args:
        mapping_package_folder_path: Path to the mapping package folder
    """
    package_root = _resolve_package_root(mapping_package_folder_path)
    if package_root is None:
        package_root = mapping_package_folder_path

    conceptual_mapping_path = package_root / mssdk_config.MPV3_CONCEPTUAL_MAPPING_FILE_ASSET_PATH
    if conceptual_mapping_path.exists():
        conceptual_mapping_path.unlink()
        logger.debug(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
            package_source=mapping_package_folder_path,
            message=f"Removed conceptual_mappings.xlsx file from {conceptual_mapping_path}"))


def serialise_mapping_package(to_version: str, mapping_package_folder_path: Path, converted_package) -> None:
    """
    Serialize a mapping package to filesystem based on version.

    Also handles post-serialization file operations:
    - Copies context.jsonld to package
    - Removes old metadata.json (for V3 conversions)
    - Removes conceptual_mappings.xlsx (for V3L conversions)

    Args:
        to_version: Target version (v3 or v3L)
        mapping_package_folder_path: Path to the mapping package folder
        converted_package: The converted package model to serialize

    Raises:
        UnsupportedVersionError: If to_version is not supported
    """
    if to_version == Version.V3:
        serialiser = MappingPackageV3Serialiser()
        serialiser.serialise(mapping_package_folder_path, converted_package)
        _copy_context_jsonld_to_package(mapping_package_folder_path, converted_package)
        _remove_old_metadata_json(mapping_package_folder_path)
    elif to_version == Version.V3L:
        serialiser = MappingPackageV3LightweightSerialiser()
        serialiser.serialise(mapping_package_folder_path, converted_package)
        _copy_context_jsonld_to_package(mapping_package_folder_path, converted_package)
        _remove_old_metadata_json(mapping_package_folder_path)
        _remove_conceptual_mapping_file(mapping_package_folder_path)
    else:
        raise UnsupportedVersionError(f"Unsupported target version: {to_version}")


def convert_mapping_package_from_folder(
    from_version: str,
    to_version: str,
    mapping_package_folder_path: Path
) -> None:
    """
    Convert a mapping package from filesystem to filesystem.

    Complete workflow:
    1. Load package from folder
    2. Convert package model
    3. Serialize converted package back to folder
    4. Handle file operations (context.jsonld, cleanup)

    Args:
        from_version: Source version (v2 or v3)
        to_version: Target version (v3 or v3L)
        mapping_package_folder_path: Path to the mapping package folder

    Raises:
        InvalidPackagePathError: If package path is invalid
        UnsupportedVersionError: If version or conversion is not supported
        FileNotFoundError: If required files are missing
        ConversionError: For other conversion errors
    """
    source_package = load_mapping_package_from_folder(from_version, mapping_package_folder_path)
    converted_package = convert_mapping_package_model(from_version, to_version, source_package)
    serialise_mapping_package(to_version, mapping_package_folder_path, converted_package)


def convert_mapping_packages_from_folder(
    from_version: str,
    to_version: str,
    folder_path: Path
) -> dict[str, int]:
    """
    Convert multiple mapping packages from a folder.

    Iterates through all subdirectories in the folder and converts each one.
    Skips packages that are already in the target version.

    Args:
        from_version: Source version (v2 or v3)
        to_version: Target version (v3 or v3L)
        folder_path: Path to folder containing mapping package directories

    Returns:
        Dictionary with counts: {'converted': int, 'skipped': int, 'total': int}

    Raises:
        InvalidPackagePathError: If folder path is invalid
        UnsupportedVersionError: If version or conversion is not supported
    """
    if not folder_path.exists():
        raise InvalidPackagePathError(f"Path does not exist: {folder_path}")
    if not folder_path.is_dir():
        raise InvalidPackagePathError(f"Path is not a directory: {folder_path}")

    mp_folders = [d for d in folder_path.iterdir() if d.is_dir()]
    total_count = len(mp_folders)
    converted_count = 0
    skipped_count = 0

    for mp_folder in mp_folders:
        if is_mapping_package_already_converted(mp_folder, to_version):
            skipped_count += 1
            logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
                package_source=mp_folder,
                message=f"Package is already {to_version}, skipping conversion"))
            continue

        # Hard fail on conversion errors - let exceptions propagate
        convert_mapping_package_from_folder(from_version, to_version, mp_folder)
        converted_count += 1
        logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
            package_source=mp_folder,
            message=f"✅ Converted {from_version} package to {to_version} package"))

    return {
        'converted': converted_count,
        'skipped': skipped_count,
        'total': total_count
    }

