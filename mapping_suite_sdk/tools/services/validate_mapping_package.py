"""
Cross-version validation service for mapping packages.

This module provides a single public `validate_mapping_package(...)` function that:
- validates a mapping package model instance, OR a folder/archive path
- auto-detects the mapping package version only when `version` is not provided
- dispatches to the appropriate version-specific validator

Consumers should not need to import version-specific validation modules.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Optional, Literal, NoReturn

from mapping_suite_sdk.core.adapters.extractor import ArchiveExtractor
from mapping_suite_sdk.core.adapters.tracer import traced_class, traced_routine
from mapping_suite_sdk.core.adapters.validator import MPValidationException, MPValidationStepABC
from mapping_suite_sdk.core.adapters.version_detector import detect_mapping_package_version
from mapping_suite_sdk.core.models.mapping_package import MappingPackage
from mapping_suite_sdk.tools.services.convert_mapping_package import Version


@traced_class
class CrossVersionValidationError(MPValidationException):
    """Raised when cross-version validation cannot route to a validator."""


def _normalize_version(version: str) -> Version:
    """
    Normalize version string input to a Version enum member.

    Handles case-insensitive input and whitespace trimming.

    Args:
        version: Version string (e.g., "V1", "  v3L  ", "V2")

    Returns:
        Version enum member

    Raises:
        CrossVersionValidationError: If version is not supported
    """
    normalized = version.strip().lower()

    # Map lowercase input to Version enum
    version_map = {
        "v1": Version.V1,
        "v2": Version.V2,
        "v3": Version.V3,
        "v3l": Version.V3L,
    }

    if normalized not in version_map:
        raise CrossVersionValidationError(f"Unsupported version: {version}")

    return version_map[normalized]


def _validate_model(mapping_package: MappingPackage, version: Version) -> Literal[True] | NoReturn:
    # Import lazily to avoid version-specific imports in consumer code.
    from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1
    from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
    from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
    from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight

    from mapping_suite_sdk.mapping_package_v1.services.validate_mapping_package_v1 import validate_mapping_package_v1
    from mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2 import validate_mapping_package_v2
    from mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3 import validate_mapping_package_v3
    from mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3_lightweight import (
        validate_mapping_package_v3_lightweight,
    )

    if version == Version.V1:
        if not isinstance(mapping_package, MappingPackageV1):
            raise CrossVersionValidationError(f"Version 'v1' requires MappingPackageV1, got: {type(mapping_package)}")
        return validate_mapping_package_v1(mapping_package=mapping_package)
    if version == Version.V2:
        if not isinstance(mapping_package, MappingPackageV2):
            raise CrossVersionValidationError(f"Version 'v2' requires MappingPackageV2, got: {type(mapping_package)}")
        return validate_mapping_package_v2(mapping_package=mapping_package)
    if version == Version.V3:
        if not isinstance(mapping_package, MappingPackageV3):
            raise CrossVersionValidationError(f"Version 'v3' requires MappingPackageV3, got: {type(mapping_package)}")
        return validate_mapping_package_v3(mapping_package=mapping_package)
    if version == Version.V3L:
        if not isinstance(mapping_package, MappingPackageV3Lightweight):
            raise CrossVersionValidationError(
                f"Version 'v3L' requires MappingPackageV3Lightweight, got: {type(mapping_package)}"
            )
        return validate_mapping_package_v3_lightweight(mapping_package=mapping_package)

    raise CrossVersionValidationError(f"Unsupported version: {version}")


def _validate_folder_from_path(path: Path, version: Version) -> Literal[True] | NoReturn:
    """Call the appropriate version-specific folder validator."""
    from mapping_suite_sdk.mapping_package_v1.services.validate_mapping_package_v1 import validate_mapping_package_v1_from_folder
    from mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2 import validate_mapping_package_v2_from_folder
    from mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3 import validate_mapping_package_v3_from_folder
    from mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3_lightweight import (
        validate_mapping_package_v3_lightweight_from_folder,
    )

    if version == Version.V1:
        return validate_mapping_package_v1_from_folder(mapping_package_folder_path=path)
    if version == Version.V2:
        return validate_mapping_package_v2_from_folder(mapping_package_folder_path=path)
    if version == Version.V3:
        return validate_mapping_package_v3_from_folder(mapping_package_folder_path=path)
    if version == Version.V3L:
        return validate_mapping_package_v3_lightweight_from_folder(mapping_package_folder_path=path)

    raise CrossVersionValidationError(f"Unsupported version: {version}")


def _validate_archive_path(path: Path, version: Optional[str]) -> Literal[True] | NoReturn:
    """Validate a mapping package from an archive file."""
    MPValidationStepABC.validate_archive_path(path, context="validate mapping package archive")
    extractor = ArchiveExtractor()
    with tempfile.TemporaryDirectory() as temp_dir:
        extracted_folder = extractor.extract(path, Path(temp_dir))

        detected = _normalize_version(version) if version else detect_mapping_package_version(extracted_folder)
        if not detected:
            raise CrossVersionValidationError(f"Unknown or unsupported mapping package version for: {path}")
        return _validate_folder_from_path(extracted_folder, detected)


def _validate_folder_path(path: Path, version: Optional[str]) -> Literal[True] | NoReturn:
    """Validate a mapping package from a folder path."""
    MPValidationStepABC.validate_folder_path(path, context="validate mapping package folder")
    detected = _normalize_version(version) if version else detect_mapping_package_version(path)
    if not detected:
        raise CrossVersionValidationError(f"Unknown or unsupported mapping package version for: {path}")
    return _validate_folder_from_path(path, detected)


def _validate_path(path: Path, version: Optional[str]) -> Literal[True] | NoReturn:
    """Validate a mapping package from a Path (file or folder)."""
    MPValidationStepABC.validate_path_exists(path, context="validate mapping package")

    if path.is_file():
        return _validate_archive_path(path, version)
    
    return _validate_folder_path(path, version)


def _detect_version_from_model(mapping_package: MappingPackage) -> Version:
    """Auto-detect version from model instance type."""
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

    raise CrossVersionValidationError(f"Cannot auto-detect version from mapping package type: {type(mapping_package)}")


@traced_routine
def validate_mapping_package(
    mapping_package: Path | MappingPackage,
    version: Optional[str] = None,
) -> Literal[True] | NoReturn:
    """
    Validate a mapping package using version-specific logic, with optional auto-detection.

    - If `version` is provided, no auto-detection is performed.
    - If `version` is not provided, the version is auto-detected:
      - for `Path`: via `detect_mapping_package_version(path)` (folder), or via temp extraction (archive)
      - for model instances: via `isinstance(...)` checks

    Args:
        mapping_package: Either a mapping package model instance or a folder/archive path.
        version: Optional explicit version ("v1", "v2", "v3", "v3L"). When provided, version detection is skipped.

    Returns:
        True if validation passes, otherwise raises.
    """
    if isinstance(mapping_package, Path):
        return _validate_path(mapping_package, version)

    # Model instance case
    detected = _normalize_version(version) if version else _detect_version_from_model(mapping_package)
    return _validate_model(mapping_package, detected)
