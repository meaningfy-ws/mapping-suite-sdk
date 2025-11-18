"""
Version detection rule for MappingPackageV1.

Defines the detection criteria for identifying V1 format mapping packages
using declarative specifications.
"""

from mapping_suite_sdk.core import VersionDetectionRegistry
from mapping_suite_sdk.core.adapters.version_detector import (
    VersionDetectionSpec,
    PathCondition,
    MetadataCondition,
)

# Declarative V1 specification
V1_SPEC = VersionDetectionSpec(
    version_id="v1",
    priority=-1
)

# Convert spec to rule
v1_detection_rule = V1_SPEC.to_rule()

# Self-register when this module is imported
VersionDetectionRegistry.register(v1_detection_rule, priority=V1_SPEC.priority)