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


def _load_source_package(
    version: Version,
    package_folder_path: Path,
    include_test_data: bool,
    include_output: bool,
):
    """Load a mapping package from folder using the version-specific loader."""
    if version == Version.V1:
        from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_loader import MappingPackageV1Loader
        from mapping_suite_sdk.mapping_package_v1.services.load_mapping_package_v1 import (
            load_mapping_package_v1_from_folder,
        )
        loader = MappingPackageV1Loader(include_test_data=include_test_data, include_output=include_output)
        return load_mapping_package_v1_from_folder(
            mapping_package_folder_path=package_folder_path,
            mapping_package_loader=loader,
        )
    if version == Version.V2:
        from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader
        from mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2 import (
            load_mapping_package_v2_from_folder,
        )
        loader = MappingPackageV2Loader(include_test_data=include_test_data, include_output=include_output)
        return load_mapping_package_v2_from_folder(
            mapping_package_folder_path=package_folder_path,
            mapping_package_loader=loader,
        )
    if version == Version.V3:
        from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_loader import MappingPackageV3Loader
        from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3 import (
            load_mapping_package_v3_from_folder,
        )
        loader = MappingPackageV3Loader(include_test_data=include_test_data, include_output=include_output)
        return load_mapping_package_v3_from_folder(
            mapping_package_folder_path=package_folder_path,
            mapping_package_loader=loader,
        )
    if version == Version.V3L:
        from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_loader import (
            MappingPackageV3LightweightLoader,
        )
        from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight import (
            load_mapping_package_v3_lightweight_from_folder,
        )
        loader = MappingPackageV3LightweightLoader(
            include_test_data=include_test_data, include_output=include_output
        )
        return load_mapping_package_v3_lightweight_from_folder(
            mapping_package_folder_path=package_folder_path,
            mapping_package_loader=loader,
        )
    raise UnsupportedVersionError(f"Unsupported source version: {version}")


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


def _validate_package_path(package_folder_path: Path) -> None:
    """Validate that the package path exists and is a directory."""
    if not package_folder_path.exists():
        raise InvalidPackagePathError(f"Package path does not exist: {package_folder_path}")
    if not package_folder_path.is_dir():
        raise InvalidPackagePathError(
            f"Package path is not a directory: {package_folder_path}"
        )


def _resolve_version(version: Optional[str], package_folder_path: Path) -> Version:
    """Resolve the package version from explicit input or auto-detection."""
    if version is not None:
        return _normalize_version(version)

    detected = detect_mapping_package_version(package_folder_path)
    if detected is None:
        raise VersionDetectionError(
            f"Could not detect mapping package version for: {package_folder_path}"
        )
    return _normalize_version(detected)


def _validate_conversion_path(source_version: Version, target_version: Version) -> None:
    """Validate that conversion from source to target is supported."""
    if source_version == Version.V3L and target_version == Version.V3:
        raise UnsupportedConversionError(
            "Cannot produce v3 (full) from a v3L source; v3L has no test data or validation assets."
        )


def _validate_if_requested(package, validate_package: bool) -> None:
    """Validate package if validation is enabled."""
    if validate_package:
        from mapping_suite_sdk.tools.services.validate_mapping_package import (
            validate_mapping_package,
        )
        validate_mapping_package(package)


def _persist_if_requested(
    mapping_package,
    persist_to_mongodb: bool,
    mongo_client: Optional[MongoClient],
    database_name: Optional[str],
    collection_name: str,
):
    """Persist package to MongoDB if requested."""
    if not persist_to_mongodb:
        return mapping_package

    if mongo_client is None or database_name is None:
        raise ValueError(
            "persist_to_mongodb requires mongo_client and database_name"
        )

    return _persist_to_mongodb(
        mapping_package, mongo_client, database_name, collection_name
    )


@traced_routine
def load_mapping_package(
    package_folder_path: Path,
    *,
    version: Optional[str] = None,
    include_test_data: bool = False,
    include_output: bool = True,
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
        include_output: If True, load output/results artefacts from the package. Defaults to True.
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
    _validate_package_path(package_folder_path)

    source_version = _resolve_version(version, package_folder_path)
    target_version = Version.V3 if include_test_data else Version.V3L

    _validate_conversion_path(source_version, target_version)
    _validate_if_requested(package_folder_path, validate_package)

    source_package = _load_source_package(
        source_version, package_folder_path, include_test_data=include_test_data, include_output=include_output
    )

    converted = (
        convert_mapping_package_model(source_version, target_version, source_package)
        if source_version != target_version
        else source_package
    )

    _validate_if_requested(converted, validate_package)

    return _persist_if_requested(
        converted, persist_to_mongodb, mongo_client, database_name, collection_name
    )
