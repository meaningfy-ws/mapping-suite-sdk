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
from typing import cast

from mapping_suite_sdk.config import mssdk_config
from mapping_suite_sdk.core.adapters.tracer import traced_routine
from mapping_suite_sdk.core.adapters.version_detector import _resolve_package_root
from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_loader import MappingPackageV1Loader
from mapping_suite_sdk.mapping_package_v1.services.load_mapping_package_v1 import load_mapping_package_v1_from_folder
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader
from mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2 import load_mapping_package_v2_from_folder
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_loader import MappingPackageV3Loader
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser import MappingPackageV3Serialiser
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_serialiser import MappingPackageV3LightweightSerialiser
from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3 import load_mapping_package_v3_from_folder
from mapping_suite_sdk.tools.services.convert_mapping_package_v1_to_v3 import convert_mapping_package_v1_to_v3
from mapping_suite_sdk.tools.services.convert_mapping_package_v1_to_v3_lightweight import (
    convert_mapping_package_v1_to_v3_lightweight,
)
from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import (
    convert_mapping_package_v2_to_v3,
    is_mapping_package_already_converted,  # Re-export for convenience
)
from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3_lightweight import (
    convert_mapping_package_v2_to_v3_lightweight,
)
from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import (
    convert_mapping_package_v3_to_v3_lightweight,
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


class VersionDetectionError(UnsupportedVersionError):
    """Raised when package version cannot be detected from path."""


class UnsupportedConversionError(UnsupportedVersionError):
    """Raised when source version cannot be converted to the requested target (e.g. v3L -> v3)."""


class InvalidPackagePathError(ConversionError):
    """Raised when package path is invalid."""

    pass


@traced_routine
def load_mapping_package_from_folder(from_version: str, mapping_package_folder_path: Path):
    """
    Load a mapping package from filesystem based on version.

    Args:
        from_version: Source version (v1, v2 or v3)
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

    if from_version == Version.V1:
        loader_v1 = MappingPackageV1Loader()
        return load_mapping_package_v1_from_folder(
            mapping_package_folder_path=mapping_package_folder_path, mapping_package_loader=loader_v1
        )
    elif from_version == Version.V2:
        loader_v2 = MappingPackageV2Loader()
        return load_mapping_package_v2_from_folder(
            mapping_package_folder_path=mapping_package_folder_path, mapping_package_loader=loader_v2
        )
    elif from_version == Version.V3:
        loader_v3 = MappingPackageV3Loader()
        return load_mapping_package_v3_from_folder(
            mapping_package_folder_path=mapping_package_folder_path, mapping_package_loader=loader_v3
        )
    else:
        raise UnsupportedVersionError(f"Unsupported source version: {from_version}")


@traced_routine
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
    if from_version == Version.V1 and to_version == Version.V3:
        return convert_mapping_package_v1_to_v3(source_package)
    elif from_version == Version.V1 and to_version == Version.V3L:
        return convert_mapping_package_v1_to_v3_lightweight(source_package)
    elif from_version == Version.V2 and to_version == Version.V3:
        return convert_mapping_package_v2_to_v3(source_package)
    elif from_version == Version.V2 and to_version == Version.V3L:
        return convert_mapping_package_v2_to_v3_lightweight(source_package)
    elif from_version == Version.V3 and to_version == Version.V3L:
        return convert_mapping_package_v3_to_v3_lightweight(source_package)
    else:
        raise UnsupportedVersionError(f"Unsupported conversion: {from_version} -> {to_version}")


_VERSION_MAP = {
    "v1": Version.V1,
    "v2": Version.V2,
    "v3": Version.V3,
    "v3l": Version.V3L,
}


def _normalize_version(version: str) -> Version:
    """Normalize version string to Version enum (case-insensitive, strips whitespace)."""
    normalized = version.strip().lower()
    if normalized not in _VERSION_MAP:
        raise UnsupportedVersionError(f"Unsupported version: {version}")
    return _VERSION_MAP[normalized]


def _validate_conversion_path(source_version: Version, target_version: Version) -> None:
    """Validate that conversion from source to target is supported."""
    if source_version == Version.V3L and target_version == Version.V3:
        raise UnsupportedConversionError(
            "Cannot produce v3 (full) from a v3L source; v3L has no test data or validation assets."
        )


def _detect_version_from_model(mapping_package) -> Version:
    """Detect the version of a loaded mapping package from its type."""
    from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1
    from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
    from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
    from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight

    if isinstance(mapping_package, MappingPackageV1):
        return Version.V1
    if isinstance(mapping_package, MappingPackageV2):
        return Version.V2
    if isinstance(mapping_package, MappingPackageV3Lightweight):
        return Version.V3L
    if isinstance(mapping_package, MappingPackageV3):
        return Version.V3

    raise VersionDetectionError(f"Cannot auto-detect version from mapping package type: {type(mapping_package)}")


def _normalize_target_version(version: str) -> Version:
    """Normalize a conversion target: only v3 (full) and v3L (lightweight) are allowed."""
    target = _normalize_version(version)
    if target not in (Version.V3, Version.V3L):
        raise UnsupportedVersionError(f"Unsupported target version: {version}; use v3 or v3L")
    return target


@traced_routine
def convert_mapping_package(mapping_package, to_version: str = "v3"):
    """Convert a loaded mapping package to v3 (full) or v3L (lightweight).

    The source version is detected from the package type. A package already at the target version
    is returned as is.

    Raises:
        UnsupportedVersionError: If ``to_version`` is not "v3" or "v3L".
        VersionDetectionError: If ``mapping_package`` is not a v1, v2, v3 or v3-lightweight package.
        UnsupportedConversionError: If the source cannot become the target (v3L -> v3).
    """
    target_version = _normalize_target_version(to_version)
    source_version = _detect_version_from_model(mapping_package)
    _validate_conversion_path(source_version, target_version)
    if source_version == target_version:
        return mapping_package
    return convert_mapping_package_model(source_version, target_version, mapping_package)


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
    package_path = Path(cast(Path, package_ref))  # files() is a real directory for an installed package
    project_root = package_path.parent
    context_path = project_root / "resources" / "schema" / "mapping_package_v3" / "models" / "context.jsonld"

    if not context_path.exists():
        raise FileNotFoundError(f"context.jsonld not found at {context_path}. Run 'make generate-models' to generate it.")

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

    package_root = _resolve_package_root(mapping_package_folder_path)
    if package_root is None:
        package_root = mapping_package_folder_path

    metadata_path = package_root / converted_package.metadata.path
    metadata_directory = metadata_path.parent
    package_context_path = metadata_directory / "context.jsonld"

    shutil.copy2(schema_context_path, package_context_path)
    logger.debug(
        mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
            package_source=mapping_package_folder_path,
            message=f"Copied context.jsonld from {schema_context_path} to {package_context_path}",
        )
    )


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
        logger.debug(
            mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
                package_source=mapping_package_folder_path, message=f"Removed old metadata.json file from {old_metadata_path}"
            )
        )


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
        logger.debug(
            mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
                package_source=mapping_package_folder_path,
                message=f"Removed conceptual_mappings.xlsx file from {conceptual_mapping_path}",
            )
        )


def _remove_folder(mapping_package_folder_path: Path, relative_folder_path: str | Path, folder_name: str) -> None:
    """
    Remove a folder when converting to V3L.

    V3 Full includes various folders (test_data, output, validation) that V3L does not.
    If these folders exist after conversion to V3L, version detection may incorrectly identify it as V3 Full.

    Args:
        mapping_package_folder_path: Path to the mapping package folder
        relative_folder_path: Relative path to the folder to remove (from package root)
        folder_name: Name of the folder for logging purposes
    """
    package_root = _resolve_package_root(mapping_package_folder_path)
    if package_root is None:
        package_root = mapping_package_folder_path

    folder_path = package_root / relative_folder_path
    if folder_path.exists() and folder_path.is_dir():
        shutil.rmtree(folder_path)
        logger.debug(
            mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
                package_source=mapping_package_folder_path, message=f"Removed {folder_name} folder from {folder_path}"
            )
        )


@traced_routine
def serialise_mapping_package(to_version: str, mapping_package_folder_path: Path, converted_package) -> None:
    """
    Serialize a mapping package to filesystem based on version.

    Also handles post-serialization file operations:
    - Copies context.jsonld to package
    - Removes old metadata.json (for V3 conversions)
    - Removes conceptual_mappings.xlsx (for V3L conversions)
    - Removes test_data, output, and validation folders (for V3L conversions)

    Args:
        to_version: Target version (v3 or v3L)
        mapping_package_folder_path: Path to the mapping package folder
        converted_package: The converted package model to serialize

    Raises:
        UnsupportedVersionError: If to_version is not supported
    """
    package_root = _resolve_package_root(mapping_package_folder_path)
    if package_root is None:
        package_root = mapping_package_folder_path

    if to_version == Version.V3:
        serialiser = MappingPackageV3Serialiser()
        serialiser.serialise(package_root, converted_package)
        _copy_context_jsonld_to_package(mapping_package_folder_path, converted_package)
        _remove_old_metadata_json(mapping_package_folder_path)
    elif to_version == Version.V3L:
        lightweight_serialiser = MappingPackageV3LightweightSerialiser()
        lightweight_serialiser.serialise(package_root, converted_package)
        _copy_context_jsonld_to_package(mapping_package_folder_path, converted_package)
        _remove_old_metadata_json(mapping_package_folder_path)
        _remove_conceptual_mapping_file(mapping_package_folder_path)
        _remove_folder(mapping_package_folder_path, mssdk_config.MPV3_TEST_DATA_COLLECTION_ASSET_PATH, "test_data")
        _remove_folder(mapping_package_folder_path, mssdk_config.MPV3_TEST_RESULT_COLLECTION_ASSET_PATH, "output")
        _remove_folder(mapping_package_folder_path, "validation", "validation")
    else:
        raise UnsupportedVersionError(f"Unsupported target version: {to_version}")


@traced_routine
def convert_mapping_package_from_folder(from_version: str, to_version: str, mapping_package_folder_path: Path) -> None:
    """
    Convert a mapping package from filesystem to filesystem.

    Complete workflow:
    1. Validate source package (fail if broken; no conversion of invalid packages)
    2. Load package from folder
    3. Convert package model (hash is updated on the converted model)
    4. Serialize converted package back to folder
    5. Handle file operations (context.jsonld, cleanup)
    6. Validate converted package (ensures hash and structure are sane)

    Args:
        from_version: Source version (v1, v2 or v3)
        to_version: Target version (v3 or v3L)
        mapping_package_folder_path: Path to the mapping package folder

    Raises:
        InvalidPackagePathError: If package path is invalid
        UnsupportedVersionError: If version or conversion is not supported
        FileNotFoundError: If required files are missing
        ConversionError: For other conversion errors
        MPValidationException: If source package fails validation (pre-conversion)
            or converted package fails validation (post-conversion)
    """
    if not mapping_package_folder_path.exists():
        raise InvalidPackagePathError(f"Package path does not exist: {mapping_package_folder_path}")
    if not mapping_package_folder_path.is_dir():
        raise InvalidPackagePathError(f"Package path is not a directory: {mapping_package_folder_path}")

    # Pre-conversion: validate source package; abort if invalid (e.g. wrong hash)
    from mapping_suite_sdk.tools.services.validate_mapping_package import validate_mapping_package

    validate_mapping_package(mapping_package_folder_path, version=from_version)

    source_package = load_mapping_package_from_folder(from_version, mapping_package_folder_path)
    converted_package = convert_mapping_package_model(from_version, to_version, source_package)
    serialise_mapping_package(to_version, mapping_package_folder_path, converted_package)

    # Post-conversion: validate converted package (hash already updated by converters)
    validate_mapping_package(converted_package)


@traced_routine
def convert_mapping_packages_from_folder(from_version: str, to_version: str, folder_path: Path) -> dict[str, int]:
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
            logger.info(
                mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
                    package_source=mp_folder, message=f"Package is already {to_version}, skipping conversion"
                )
            )
            continue

        # Hard fail on conversion errors - let exceptions propagate
        convert_mapping_package_from_folder(from_version, to_version, mp_folder)
        converted_count += 1
        logger.info(
            mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
                package_source=mp_folder, message=f"✅ Converted {from_version} package to {to_version} package"
            )
        )

    return {"converted": converted_count, "skipped": skipped_count, "total": total_count}
