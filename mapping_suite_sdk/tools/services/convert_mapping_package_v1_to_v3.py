"""
Conversion service for MappingPackageV1 to MappingPackageV3.

This module provides functionality to convert MappingPackageV1 (V1 / Standard Forms)
to MappingPackageV3 (V3), including conversion of metadata structures, constraints,
and all package assets.
"""

from __future__ import annotations

from typing import Optional

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1_metadata import MappingPackageV1Constraints
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import (
    ApplicabilityConstraints,
    DateTimeInterval,
    VersionRange,
)
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata_jsonld import MappingPackageV3MetadataJSONLD
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_hasher import MappingPackageV3Hasher


def _convert_v1_constraints_to_v3_applicability_constraints(
        v1_constraints: Optional[MappingPackageV1Constraints]
) -> Optional[ApplicabilityConstraints]:
    """
    Convert V1 eligibility constraints to V3 applicability constraints.

    V1 uses min/max XSD versions; in V3 this maps naturally to document_version_range.
    """
    if not v1_constraints:
        return None

    # Convert dates (open intervals supported)
    start_date_str = v1_constraints.start_date[0] if v1_constraints.start_date else None
    end_date_str = v1_constraints.end_date[0] if v1_constraints.end_date else None
    document_time_interval = None
    if start_date_str or end_date_str:
        document_time_interval = DateTimeInterval(start=start_date_str, end=end_date_str)

    min_version = v1_constraints.min_xsd_version[0] if v1_constraints.min_xsd_version else None
    max_version = v1_constraints.max_xsd_version[0] if v1_constraints.max_xsd_version else None

    document_version_range = None
    if min_version or max_version:
        document_version_range = VersionRange(min=min_version, max=max_version)

    # V1 uses ints for eforms_subtype in metadata.json; V3 expects strings
    document_type_list = [str(x) for x in v1_constraints.eforms_subtype] if v1_constraints.eforms_subtype else []

    return ApplicabilityConstraints(
        document_type_list=document_type_list,
        document_time_interval=document_time_interval,
        document_schema_version_list=None,
        document_version_range=document_version_range,
    )


def convert_mapping_package_v1_to_v3(mpv1: MappingPackageV1) -> MappingPackageV3:
    """
    Convert a MappingPackageV1 to MappingPackageV3.
    """
    mpv1_metadata = mpv1.metadata
    v1_constraints = mpv1_metadata.eligibility_constraints.constraints if mpv1_metadata.eligibility_constraints else None

    applicability_constraints = _convert_v1_constraints_to_v3_applicability_constraints(v1_constraints)

    v3_metadata_path = mssdk_config.MPV3_METADATA_FILE_ASSET_PATH

    mpv3 = MappingPackageV3(
        metadata=MappingPackageV3MetadataJSONLD(
            path=v3_metadata_path,
            context="context.jsonld",
            id=mpv1_metadata.identifier,
            title=mpv1_metadata.title,
            project_identifier="standard_forms",
            created_at=mpv1_metadata.issue_date,
            mapping_version=mpv1_metadata.mapping_version,
            model_version=mpv1_metadata.ontology_version,
            description=mpv1_metadata.description,
            applicability_constraints=applicability_constraints,
            # This will be recomputed below for the converted V3 package.
            mapping_suite_hash_digest=mpv1_metadata.signature,
        ),
        conceptual_mapping_asset=mpv1.conceptual_mapping_asset.model_copy(),
        technical_mapping_suite=mpv1.technical_mapping_suite.model_copy(),
        vocabulary_mapping_suite=mpv1.vocabulary_mapping_suite.model_copy(),
        test_data_suites=mpv1.test_data_suites.copy(),
        test_suites_sparql=mpv1.test_suites_sparql.copy(),
        test_suites_shacl=mpv1.test_suites_shacl.model_copy(),
        test_results=mpv1.test_results.model_copy(),
    )

    # Recompute hash for the converted V3 package so it validates immediately.
    mpv3.metadata.mapping_suite_hash_digest = MappingPackageV3Hasher(mpv3).hash()

    return mpv3

