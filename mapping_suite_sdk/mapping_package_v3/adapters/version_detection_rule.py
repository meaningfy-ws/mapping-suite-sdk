"""
Version detection rules for MappingPackageV3.

Defines detection criteria for identifying V3 format mapping packages,
including both full and lightweight variants, using declarative specifications.
"""

from mapping_suite_sdk.core import VersionDetectionRegistry
from mapping_suite_sdk.core.adapters.version_detector import (
    VersionDetectionSpec,
    PathCondition,
    MetadataCondition,
)

# V3 path constants (stable configuration constants)
_CONCEPTUAL_MAPPING_PATH = "transformation/conceptual_mappings.xlsx"
_TECHNICAL_MAPPING_PATH = "transformation/mappings"
_VOCABULARY_MAPPING_PATH = "transformation/resources"
_TEST_DATA_PATH = "test_data"
_SPARQL_TEST_PATH = "validation/sparql"
_SHACL_TEST_PATH = "validation/shacl"
_TEST_RESULTS_PATH = "output"

# Declarative V3 Full specification
V3_FULL_SPEC = VersionDetectionSpec(
    version_id="v3",
    priority=2
)

# Declarative V3 Lightweight specification
V3_LIGHTWEIGHT_SPEC = VersionDetectionSpec(
    version_id="v3L",
    priority=1,

    path_conditions=[
        # V3 Lightweight MUST have (essential for transformation):
        # - Technical mapping suite (RML files)
        PathCondition(_TECHNICAL_MAPPING_PATH, must_exist=True),
        # - Vocabulary mapping suite (resource files)
        PathCondition(_VOCABULARY_MAPPING_PATH, must_exist=True),
    ],

    metadata_conditions=[
        # V3 JSON-LD marker: @context distinguishes V3 (both Full and Lightweight) from V1/V2
        # Note: This is NOT a differentiator between V3L and V3 Full - both have @context
        # The differentiation between V3L and V3 Full is via path conditions above
        MetadataCondition("@context", must_exist=True),
    ]
)

# Convert specs to rules
v3_full_detection_rule = V3_FULL_SPEC.to_rule()
v3_lightweight_detection_rule = V3_LIGHTWEIGHT_SPEC.to_rule()

# Self-register when this module is imported
VersionDetectionRegistry.register(v3_full_detection_rule, priority=V3_FULL_SPEC.priority)
VersionDetectionRegistry.register(v3_lightweight_detection_rule, priority=V3_LIGHTWEIGHT_SPEC.priority)