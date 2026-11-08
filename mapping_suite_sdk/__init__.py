"""Mapping Suite SDK: load, convert, validate and save mapping packages.

The names below and the ``*.models`` packages are the public API; adapters and services are internal.
"""

import importlib.metadata

# config first: the services below read mssdk_config from this package at import time
from mapping_suite_sdk.config import MSSDKConfigResolver, mssdk_config

__version__ = importlib.metadata.version("mapping-suite-sdk")

from mapping_suite_sdk.core.adapters.validator import MPValidationException  # noqa: E402
from mapping_suite_sdk.core.adapters.version_detector import detect_mapping_package_version  # noqa: E402
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_validator import (  # noqa: E402
    MPV3HashValidationException,
    MPV3StructuralValidationException,
)
from mapping_suite_sdk.mapping_package_v3.models import MappingPackageV3, MappingPackageV3Lightweight  # noqa: E402
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import (  # noqa: E402
    ApplicabilityConstraints,
    DateTimeInterval,
    MappingPackageV3Metadata,
    VersionRange,
)
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata_jsonld import (  # noqa: E402
    MappingPackageV3MetadataJSONLD,
)
from mapping_suite_sdk.mapping_package_v3.services.serialise_mapping_package_v3 import (  # noqa: E402
    mapping_package_to_zip_bytes,
    save_mapping_package_v3_to_archive,
    save_mapping_package_v3_to_folder,
)
from mapping_suite_sdk.mapping_suite.services.load_mapping_suite import load_mapping_suite_from_folder  # noqa: E402
from mapping_suite_sdk.tools.services.convert_mapping_package import (  # noqa: E402
    ConversionError,
    InvalidPackagePathError,
    UnsupportedConversionError,
    UnsupportedVersionError,
    VersionDetectionError,
    convert_mapping_package,
)
from mapping_suite_sdk.tools.services.load_mapping_package import (  # noqa: E402
    load_mapping_package,
    load_mapping_package_from_bytes,
)
from mapping_suite_sdk.tools.services.save_mapping_package import save_mapping_package_to_mongodb  # noqa: E402
from mapping_suite_sdk.tools.services.validate_mapping_package import (  # noqa: E402
    CrossVersionValidationError,
    validate_mapping_package,
)

__all__ = [
    "__version__",
    "mssdk_config",
    "MSSDKConfigResolver",
    "load_mapping_package",
    "load_mapping_package_from_bytes",
    "mapping_package_to_zip_bytes",
    "save_mapping_package_v3_to_folder",
    "save_mapping_package_v3_to_archive",
    "validate_mapping_package",
    "convert_mapping_package",
    "detect_mapping_package_version",
    "load_mapping_suite_from_folder",
    "save_mapping_package_to_mongodb",
    "MappingPackageV3",
    "MappingPackageV3Lightweight",
    "MappingPackageV3Metadata",
    "MappingPackageV3MetadataJSONLD",
    "ApplicabilityConstraints",
    "VersionRange",
    "DateTimeInterval",
    "ConversionError",
    "UnsupportedVersionError",
    "UnsupportedConversionError",
    "VersionDetectionError",
    "InvalidPackagePathError",
    "MPValidationException",
    "CrossVersionValidationError",
    "MPV3StructuralValidationException",
    "MPV3HashValidationException",
]
