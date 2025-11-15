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
    priority=-1,

    path_conditions=[
        # No path conditions for metadata files - rely on metadata content for detection
        # (metadata.json or metadata.jsonld are both supported, format is cross-cutting)
    ],

    metadata_conditions=[
        # V1-specific differentiating fields:
        # - V1 uses XSD version constraints (min_xsd_version or max_xsd_version)
        #   Note: We check for min_xsd_version as the primary indicator
        MetadataCondition("eligibility_constraints.constraints.min_xsd_version", must_exist=True),

        # - V1 does NOT have eforms_sdk_versions (that's V2)
        MetadataCondition("eligibility_constraints.constraints.eforms_sdk_versions", must_exist=False),

        # - V1 does NOT have "type" or "mapping_type" fields (V2 may have these)
        MetadataCondition("type", must_exist=False),
        MetadataCondition("mapping_type", must_exist=False),

        # - V1 does NOT have @context (JSON-LD marker used by V3)
        #   Note: JSON-LD format is cross-cutting, but @context in metadata is V3-specific
        MetadataCondition("@context", must_exist=False),
    ]
)

# Convert spec to rule
v1_detection_rule = V1_SPEC.to_rule()

# Self-register when this module is imported
VersionDetectionRegistry.register(v1_detection_rule, priority=V1_SPEC.priority)