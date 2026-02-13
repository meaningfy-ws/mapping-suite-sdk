"""
One-stop service for loading mapping packages with autoconversion.

This service provides a single, version-agnostic entry point that:
- Detects package version when not provided
- Routes to the appropriate version-specific loader
- Converts to v3 (full) or v3L (lightweight) based on include_test_data
- Optionally validates before and after conversion (hash is only updated by conversion)
- Optionally persists the result to MongoDB

Consumers (e.g. TEDSWS pipeline) can load mapping packages without
version-specific imports. Version-specific concerns stay encapsulated in the SDK.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

from pymongo import MongoClient

from mapping_suite_sdk.core.adapters.tracer import traced_routine
from mapping_suite_sdk.core.adapters.version_detector import detect_mapping_package_version
from mapping_suite_sdk.tools.services.convert_mapping_package import (
    InvalidPackagePathError,
    UnsupportedVersionError,
    Version,
    convert_mapping_package_model,
    load_mapping_package_from_folder,
)

logger = logging.getLogger(__name__)


class VersionDetectionError(UnsupportedVersionError):
    """Raised when package version cannot be detected from path."""


class UnsupportedConversionError(UnsupportedVersionError):
    """Raised when source version cannot be converted to the requested target (e.g. v3L -> v3)."""


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


def _load_source_package(version: Version, package_folder_path: Path):
    """Load a mapping package from folder using the version-specific loader."""
    if version == Version.V3L:
        from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight import (
            load_mapping_package_v3_lightweight_from_folder,
        )
        return load_mapping_package_v3_lightweight_from_folder(
            mapping_package_folder_path=package_folder_path,
        )
    return load_mapping_package_from_folder(version, package_folder_path)


def _persist_to_mongodb(
    mapping_package: Union["MappingPackageV3", "MappingPackageV3Lightweight"],
    mongo_client: MongoClient,
    database_name: str,
    collection_name: str,
):
    """Persist the package to MongoDB using the appropriate version-specific saver."""
    from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
    from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import (
        MappingPackageV3Lightweight,
    )
    from mapping_suite_sdk.mapping_package_v3.services.save_mapping_package_v3 import (
        save_mapping_package_v3_to_mongo_db,
    )
    from mapping_suite_sdk.mapping_package_v3.services.save_mapping_package_v3_lightweight import (
        save_mapping_package_v3_lightweight_to_mongo_db,
    )

    if isinstance(mapping_package, MappingPackageV3):
        return save_mapping_package_v3_to_mongo_db(
            mapping_package=mapping_package,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name,
        )
    if isinstance(mapping_package, MappingPackageV3Lightweight):
        return save_mapping_package_v3_lightweight_to_mongo_db(
            mapping_package=mapping_package,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name,
        )
    raise UnsupportedConversionError(
        f"Cannot persist to MongoDB: unsupported package type {type(mapping_package)}"
    )


@traced_routine
def load_mapping_package(
    package_folder_path: Path,
    *,
    version: Optional[str] = None,
    include_test_data: bool = False,
    validate_package: bool = True,
    persist_to_mongodb: bool = False,
    mongo_client: Optional[MongoClient] = None,
    database_name: Optional[str] = None,
    collection_name: str = "mapping_package",
):
    """
    Load a mapping package from a folder with optional autoconversion and persistence.

    Version is auto-detected when not provided. The package is converted to v3 (full)
    when include_test_data is True, or to v3L (lightweight) when False. Hash is updated
    only by the conversion step; validation before conversion fails if the hash is invalid.

    Args:
        package_folder_path: Path to the mapping package folder (must exist and be a directory).
        version: Optional explicit version ("v1", "v2", "v3", "v3L"). When omitted, version
            is detected from the package structure.
        include_test_data: If True, target v3 (full package); if False, target v3L (lightweight).
            Defaults to False.
        validate_package: If True, validate the source package before conversion and the
            result after conversion. Validation before conversion fails on invalid hash (no update).
            Defaults to True.
        persist_to_mongodb: If True, persist the resulting package to MongoDB. Requires
            mongo_client and database_name.
        mongo_client: MongoDB client (required when persist_to_mongodb is True).
        database_name: MongoDB database name (required when persist_to_mongodb is True).
        collection_name: MongoDB collection name; default "mapping_package".

    Returns:
        The loaded (and optionally converted) package as MappingPackageV3 or
        MappingPackageV3Lightweight.

    Raises:
        InvalidPackagePathError: If the path does not exist or is not a directory.
        VersionDetectionError: If version is not provided and could not be detected.
        UnsupportedVersionError: If the version is not supported.
        UnsupportedConversionError: If the source cannot be converted to the target
            (e.g. v3L source with include_test_data True).
    """
    if not package_folder_path.exists():
        raise InvalidPackagePathError(f"Package path does not exist: {package_folder_path}")
    if not package_folder_path.is_dir():
        raise InvalidPackagePathError(
            f"Package path is not a directory: {package_folder_path}"
        )

    if version is not None:
        source_version = _normalize_version(version)
    else:
        detected = detect_mapping_package_version(package_folder_path)
        if detected is None:
            raise VersionDetectionError(
                f"Could not detect mapping package version for: {package_folder_path}"
            )
        source_version = _normalize_version(detected)

    target_version = Version.V3 if include_test_data else Version.V3L
    if source_version == Version.V3L and target_version == Version.V3:
        raise UnsupportedConversionError(
            "Cannot produce v3 (full) from a v3L source; v3L has no test data or validation assets."
        )

    if validate_package:
        from mapping_suite_sdk.tools.services.validate_mapping_package import (
            validate_mapping_package,
        )
        validate_mapping_package(package_folder_path, version=source_version.value)

    source_package = _load_source_package(source_version, package_folder_path)

    if source_version != target_version:
        converted = convert_mapping_package_model(
            source_version, target_version, source_package
        )
    else:
        converted = source_package

    if validate_package:
        from mapping_suite_sdk.tools.services.validate_mapping_package import (
            validate_mapping_package,
        )
        validate_mapping_package(converted)

    if persist_to_mongodb:
        if mongo_client is None or database_name is None:
            raise ValueError(
                "persist_to_mongodb requires mongo_client and database_name"
            )
        converted = _persist_to_mongodb(
            converted, mongo_client, database_name, collection_name
        )

    return converted
