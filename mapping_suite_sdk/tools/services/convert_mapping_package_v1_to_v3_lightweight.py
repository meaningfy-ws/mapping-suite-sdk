"""
Conversion service for MappingPackageV1 to MappingPackageV3Lightweight.

This module provides a direct (in-memory) conversion path from V1 to V3L by
composing the existing converters:
- V1 -> V3
- V3 -> V3L

This avoids a filesystem roundtrip via an intermediate V3 serialization.
"""

from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.tools.services.convert_mapping_package_v1_to_v3 import convert_mapping_package_v1_to_v3
from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import (
    convert_mapping_package_v3_to_v3_lightweight,
)


def convert_mapping_package_v1_to_v3_lightweight(mpv1: MappingPackageV1) -> MappingPackageV3Lightweight:
    """
    Convert a MappingPackageV1 to MappingPackageV3Lightweight.

    Args:
        mpv1: The V1 mapping package to convert

    Returns:
        A V3 lightweight mapping package
    """
    mpv3 = convert_mapping_package_v1_to_v3(mpv1)
    return convert_mapping_package_v3_to_v3_lightweight(mpv3)

