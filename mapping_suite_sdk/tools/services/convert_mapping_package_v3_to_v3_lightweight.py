"""
Conversion service for MappingPackageV3 to MappingPackageV3Lightweight.

This module provides functionality to convert a full MappingPackageV3 (heavyweight)
to a lightweight version (MappingPackageV3Lightweight) by extracting only the
essential components needed for data transformation.
"""
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight


def convert_mapping_package_v3_to_v3_lightweight(mpv3: MappingPackageV3) -> MappingPackageV3Lightweight:
    """
    Convert a MappingPackageV3 (full/heavyweight) to MappingPackageV3Lightweight.
    
    The lightweight version contains only the essential components for data transformation:
    - Metadata (copied as-is)
    - Technical mapping suite (RML files)
    - Vocabulary mapping suite (resource files)
    
    All other components (conceptual mapping, test suites, test results) are excluded.
    
    Args:
        mpv3: The full V3 mapping package to convert
        
    Returns:
        A lightweight V3 mapping package containing only essential transformation components
    """
    return MappingPackageV3Lightweight(
        metadata=mpv3.metadata,
        technical_mapping_suite=mpv3.technical_mapping_suite,
        vocabulary_mapping_suite=mpv3.vocabulary_mapping_suite
    )

