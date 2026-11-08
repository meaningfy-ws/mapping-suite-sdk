"""
One-stop service for loading mapping packages with autoconversion.

This service provides a single, version-agnostic entry point that:
- Detects package version when not provided
- Routes to the appropriate version-specific loader
- Converts to v3 (full) or v3L (lightweight) based on include_test_data
- Optionally validates before and after conversion (hash is only updated by conversion)

Consumers (e.g. TEDSWS pipeline) can load mapping packages without
version-specific imports. Version-specific concerns stay encapsulated in the SDK.
"""

from __future__ import annotations

import logging
from pathlib import Path

from mapping_suite_sdk.core.adapters.tracer import traced_routine
from mapping_suite_sdk.core.adapters.version_detector import detect_mapping_package_version
from mapping_suite_sdk.tools.services.convert_mapping_package import (
    InvalidPackagePathError,
    UnsupportedVersionError,
    Version,
    VersionDetectionError,
    _normalize_version,
    _validate_conversion_path,
    convert_mapping_package,
)
from mapping_suite_sdk.tools.services.convert_mapping_package import (
    UnsupportedConversionError as UnsupportedConversionError,  # re-exported: 1.x import path
)

logger = logging.getLogger(__name__)


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

        loader_v1 = MappingPackageV1Loader(include_test_data=include_test_data, include_output=include_output)
        return load_mapping_package_v1_from_folder(
            mapping_package_folder_path=package_folder_path,
            mapping_package_loader=loader_v1,
        )
    if version == Version.V2:
        from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader
        from mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2 import (
            load_mapping_package_v2_from_folder,
        )

        loader_v2 = MappingPackageV2Loader(include_test_data=include_test_data, include_output=include_output)
        return load_mapping_package_v2_from_folder(
            mapping_package_folder_path=package_folder_path,
            mapping_package_loader=loader_v2,
        )
    if version == Version.V3:
        from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_loader import MappingPackageV3Loader
        from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3 import (
            load_mapping_package_v3_from_folder,
        )

        loader_v3 = MappingPackageV3Loader(include_test_data=include_test_data, include_output=include_output)
        return load_mapping_package_v3_from_folder(
            mapping_package_folder_path=package_folder_path,
            mapping_package_loader=loader_v3,
        )
    if version == Version.V3L:
        from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_loader import (
            MappingPackageV3LightweightLoader,
        )
        from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight import (
            load_mapping_package_v3_lightweight_from_folder,
        )

        loader_v3l = MappingPackageV3LightweightLoader(include_test_data=include_test_data, include_output=include_output)
        return load_mapping_package_v3_lightweight_from_folder(
            mapping_package_folder_path=package_folder_path,
            mapping_package_loader=loader_v3l,
        )
    raise UnsupportedVersionError(f"Unsupported source version: {version}")


def _validate_package_path(package_folder_path: Path) -> None:
    """Validate that the package path exists and is a directory."""
    if not package_folder_path.exists():
        raise InvalidPackagePathError(f"Package path does not exist: {package_folder_path}")
    if not package_folder_path.is_dir():
        raise InvalidPackagePathError(f"Package path is not a directory: {package_folder_path}")


def _resolve_version(version: str | None, package_folder_path: Path) -> Version:
    """Resolve the package version from explicit input or auto-detection."""
    if version is not None:
        return _normalize_version(version)

    detected = detect_mapping_package_version(package_folder_path)
    if detected is None:
        raise VersionDetectionError(f"Could not detect mapping package version for: {package_folder_path}")
    return _normalize_version(detected)


def _validate_if_requested(
    package,
    validate_package: bool,
    include_test_data: bool = False,
    include_output: bool = False,
) -> None:
    """Validate package if validation is enabled."""
    if validate_package:
        from mapping_suite_sdk.tools.services.validate_mapping_package import (
            validate_mapping_package,
        )

        validate_mapping_package(
            package,
            include_test_data=include_test_data,
            include_output=include_output,
        )


@traced_routine
def load_mapping_package(
    package_folder_path: Path,
    *,
    version: str | None = None,
    include_test_data: bool = False,
    include_output: bool = False,
    validate_package: bool = True,
):
    """
    Load a mapping package from a folder with optional autoconversion.

    It never writes to a store; save the result with ``save_mapping_package_to_mongodb``.

    Version is auto-detected when not provided. The package is converted to v3 (full)
    when include_test_data is True, or to v3L (lightweight) when False. Hash is updated
    only by the conversion step; validation before conversion fails if the hash is invalid.

    Args:
        package_folder_path: Path to the mapping package folder (must exist and be a directory).
        version: Optional explicit version ("v1", "v2", "v3", "v3L"). When omitted, version
            is detected from the package structure.
        include_test_data: If True, target v3 (full package); if False, target v3L (lightweight).
            Defaults to False.
        include_output: If True, load output/results artefacts from the package. Defaults to False.
        validate_package: If True, validate the source package before conversion and the
            result after conversion. Validation before conversion fails on invalid hash (no update).
            Defaults to True.

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
    _validate_if_requested(
        package_folder_path,
        validate_package,
        include_test_data=include_test_data,
        include_output=include_output,
    )

    source_package = _load_source_package(
        source_version, package_folder_path, include_test_data=include_test_data, include_output=include_output
    )

    converted = convert_mapping_package(source_package, target_version)

    _validate_if_requested(
        converted,
        validate_package,
        include_test_data=include_test_data,
        include_output=include_output,
    )

    return converted
