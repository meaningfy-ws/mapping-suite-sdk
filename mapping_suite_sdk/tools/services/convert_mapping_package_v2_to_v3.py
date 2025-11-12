"""
Conversion service for MappingPackageV2 to MappingPackageV3.

This module provides functionality to convert MappingPackageV2 (V2) to MappingPackageV3 (V3),
including conversion of metadata structures, constraints, and all package assets.
"""
from typing import Optional

from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import (
    MappingPackageV2Constraints,
    MappingPackageV2Metadata
)
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import (
    ApplicabilityConstraints,
    DateTimeInterval
)
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata_jsonld import \
    MappingPackageV3MetadataJSONLD


def _convert_v2_constraints_to_v3_applicability_constraints(
        v2_constraints: Optional[MappingPackageV2Constraints]
) -> Optional[ApplicabilityConstraints]:
    """
    Convert V2 eligibility constraints to V3 applicability constraints.
    
    Args:
        v2_constraints: V2 constraints object
        
    Returns:
        V3 ApplicabilityConstraints or None if no constraints provided
    """
    if not v2_constraints:
        return None
    
    # Pass date strings directly - Pydantic will auto-convert ISO format strings to datetime
    document_time_interval = None
    start_date_str = v2_constraints.start_date[0] if v2_constraints.start_date and len(v2_constraints.start_date) > 0 else None
    end_date_str = v2_constraints.end_date[0] if v2_constraints.end_date and len(v2_constraints.end_date) > 0 else None
    
    # Create interval if at least one date is provided (open intervals are supported)
    # - Only start: "from this date onwards" (open-ended future)
    # - Only end: "until this date" (open-ended past)
    # - Both: closed interval "[start, end]"
    if start_date_str or end_date_str:
        document_time_interval = DateTimeInterval(
            start=start_date_str,
            end=end_date_str
        )
    
    return ApplicabilityConstraints(
        document_type_list=v2_constraints.eforms_subtype,
        document_time_interval=document_time_interval,
        document_version_list=v2_constraints.eforms_sdk_versions if v2_constraints.eforms_sdk_versions else None
    )


def convert_mapping_package_v2_to_v3(mpv2: MappingPackageV2) -> MappingPackageV3:
    """
    Convert a MappingPackageV2 to MappingPackageV3.
    
    This function converts the entire package structure including:
    - Metadata (with constraint conversion from V2 eligibility to V3 applicability)
    - All assets (conceptual mapping, technical mapping suite, vocabulary mapping suite,
      test data suites, SPARQL test suites, SHACL test suites, test results)
    
    Args:
        mpv2: The V2 mapping package to convert
        
    Returns:
        A V3 mapping package with all components converted
    """
    mpv2_metadata: MappingPackageV2Metadata = mpv2.metadata
    v2_constraints = mpv2_metadata.eligibility_constraints.constraints

    # Convert V2 constraints to V3 format
    applicability_constraints = _convert_v2_constraints_to_v3_applicability_constraints(v2_constraints)

    return MappingPackageV3(

        metadata=MappingPackageV3MetadataJSONLD(
            path=mpv2_metadata.path,

            id=mpv2_metadata.identifier,
            title=mpv2_metadata.title,
            project_identifier=mpv2_metadata.type,
            created_at=mpv2_metadata.issue_date,  # Pass string directly - Pydantic will auto-convert ISO format string to datetime
            mapping_version=mpv2_metadata.mapping_version,
            model_version=mpv2_metadata.ontology_version,
            description=mpv2_metadata.description,
            applicability_constraints=applicability_constraints,
            mapping_suite_hash_digest=mpv2_metadata.signature,
        ),

        conceptual_mapping_asset=mpv2.conceptual_mapping_asset.model_copy(),
        technical_mapping_suite=mpv2.technical_mapping_suite.model_copy(),
        vocabulary_mapping_suite=mpv2.vocabulary_mapping_suite.model_copy(),
        test_data_suites=mpv2.test_data_suites.copy(),
        test_suites_sparql=mpv2.test_suites_sparql.copy(),
        test_suites_shacl=mpv2.test_suites_shacl.model_copy(),
        test_results=mpv2.test_results.model_copy()
    )
