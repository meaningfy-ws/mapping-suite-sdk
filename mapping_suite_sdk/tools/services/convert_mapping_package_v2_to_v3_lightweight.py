"""
Conversion service for MappingPackageV2 to MappingPackageV3Lightweight.

This module provides a direct (in-memory) conversion path from V2 to V3L by
composing the existing converters:
- V2 -> V3
- V3 -> V3L

This avoids a filesystem roundtrip via an intermediate V3 serialization.
"""

from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_hasher import MappingPackageV3Hasher
from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import convert_mapping_package_v2_to_v3
from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import (
    convert_mapping_package_v3_to_v3_lightweight,
)


def convert_mapping_package_v2_to_v3_lightweight(mpv2: MappingPackageV2) -> MappingPackageV3Lightweight:
    """
    Convert a MappingPackageV2 to MappingPackageV3Lightweight.

    Args:
        mpv2: The V2 mapping package to convert

    Returns:
        A V3 lightweight mapping package
    """
    mpv3 = convert_mapping_package_v2_to_v3(mpv2)
    mpv3l = convert_mapping_package_v3_to_v3_lightweight(mpv3)

    # Recompute hash for the converted V3L package so it validates immediately.
    mpv3l.metadata.mapping_suite_hash_digest = MappingPackageV3Hasher(mpv3l).hash()

    return mpv3l

