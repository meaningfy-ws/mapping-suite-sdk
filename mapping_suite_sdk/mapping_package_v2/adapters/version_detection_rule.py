"""
Version detection rule for MappingPackageV2.

Defines the detection criteria for identifying V2 format mapping packages
using declarative specifications.
"""

from mapping_suite_sdk.core import VersionDetectionRegistry
from mapping_suite_sdk.core.adapters.version_detector import (
    VersionDetectionSpec,
    PathCondition,
    MetadataCondition,
)

# Declarative V2 specification
V2_SPEC = VersionDetectionSpec(
    version_id="v2",
    priority=0
)

# Convert spec to rule
v2_detection_rule = V2_SPEC.to_rule()

# Self-register when this module is imported
VersionDetectionRegistry.register(v2_detection_rule, priority=V2_SPEC.priority)