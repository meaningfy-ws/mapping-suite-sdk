from datetime import datetime
from typing import Optional

from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import MappingPackageV2Metadata
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import MappingPackageV3Metadata
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_linkml_metadata import (
    ApplicabilityConstraints,
    DateTimeInterval
)


def convert_mpv3_from_mpv2(mpv2: MappingPackageV2) -> MappingPackageV3:
    """
    Convert a MappingPackageV2 to MappingPackageV3.
    """
    mpv2_metadata: MappingPackageV2Metadata = mpv2.metadata
    v2_constraints = mpv2_metadata.eligibility_constraints.constraints
    
    # Convert V2 constraints to V3 format
    applicability_constraints: Optional[ApplicabilityConstraints] = None
    if v2_constraints:
        # Convert date strings to datetime objects
        start_datetime: Optional[datetime] = None
        end_datetime: Optional[datetime] = None
        
        if v2_constraints.start_date and len(v2_constraints.start_date) > 0:
            try:
                start_datetime = datetime.fromisoformat(v2_constraints.start_date[0])
            except (ValueError, AttributeError):
                pass
        
        if v2_constraints.end_date and len(v2_constraints.end_date) > 0:
            try:
                end_datetime = datetime.fromisoformat(v2_constraints.end_date[0])
            except (ValueError, AttributeError):
                pass
        
        document_time_interval = None
        if start_datetime or end_datetime:
            document_time_interval = DateTimeInterval(
                start=start_datetime,
                end=end_datetime
            )
        
        applicability_constraints = ApplicabilityConstraints(
            document_type_list=v2_constraints.eforms_subtype,
            document_time_interval=document_time_interval,
            document_version_list=v2_constraints.eforms_sdk_versions if v2_constraints.eforms_sdk_versions else None
        )
    
    # Convert issue_date string to datetime
    try:
        created_at_datetime = datetime.fromisoformat(mpv2_metadata.issue_date)
    except (ValueError, AttributeError):
        # Fallback: try parsing as ISO format or use current time
        created_at_datetime = datetime.now()
    
    return MappingPackageV3(

        metadata=MappingPackageV3Metadata(
            path=mpv2_metadata.path,

            id=mpv2_metadata.identifier,
            title=mpv2_metadata.title,
            project_identifier=mpv2_metadata.type,
            created_at=created_at_datetime,
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
