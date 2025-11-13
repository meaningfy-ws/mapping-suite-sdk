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
        # V2 uses metadata.json
        PathCondition("metadata.json", must_exist=True),
        # V2 does NOT use metadata.jsonld (that's V3)
        PathCondition("metadata.jsonld", must_exist=False),
    ],

    metadata_conditions=[
        # Required base keys
        MetadataCondition("identifier", must_exist=True),
        MetadataCondition("eligibility_constraints", must_exist=True),
        MetadataCondition("mapping_version", must_exist=True),
        MetadataCondition("ontology_version", must_exist=True),

        # V2-specific nested key: has eforms_sdk_versions (V1 has xsd versions instead)
        MetadataCondition("eligibility_constraints.constraints.eforms_sdk_versions", must_exist=True),
    ]
)

# Convert spec to rule
v2_detection_rule = V2_SPEC.to_rule()

# Self-register when this module is imported
VersionDetectionRegistry.register(v2_detection_rule, priority=V2_SPEC.priority)