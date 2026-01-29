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
    priority=0,

    path_conditions=[
        # No path conditions for metadata files - rely on metadata content for detection
        # (metadata.jsonld may be supported for v2 in the future; JSON-LD format is cross-cutting)
    ],

    metadata_conditions=[
        # V2-specific differentiating field:
        # - V2 uses eforms_sdk_versions (V1 uses xsd versions instead)
        # Note: In raw JSON, the field is "metadata_constraints" (not "eligibility_constraints")
        # because the Pydantic model uses an alias. The version detector reads raw JSON.
        MetadataCondition("metadata_constraints.constraints.eforms_sdk_versions", must_exist=True),

        # - V2 does NOT have @context (JSON-LD marker used by V3)
        #   Note: JSON-LD format is cross-cutting, but @context in metadata is V3-specific
        MetadataCondition("@context", must_exist=False),
    ]
)

# Convert spec to rule
v2_detection_rule = V2_SPEC.to_rule()

# Self-register when this module is imported
VersionDetectionRegistry.register(v2_detection_rule, priority=V2_SPEC.priority)