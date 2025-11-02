from datetime import datetime
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import MappingPackageV3Metadata
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_linkml_metadata import (
    ApplicabilityConstraints,
    DateTimeInterval,
)


def create_mpv3_from_mpv2(mpv2: MappingPackageV2) -> MappingPackageV3:
    """
    Convert a MappingPackageV2 to MappingPackageV3.
    """
    # Get V2 metadata as dict for manipulation
    v2_metadata_dict = mpv2.metadata.model_dump(by_alias=True, exclude_unset=True)
    
    # Convert created_at from string to datetime
    # V2 has issue_date as string, V3 needs created_at as datetime
    created_at_str = v2_metadata_dict.get("created_at") or v2_metadata_dict.get("issue_date")
    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    
    # Convert eligibility_constraints to applicability_constraints
    eligibility_constraints = v2_metadata_dict.get("metadata_constraints") or v2_metadata_dict.get("eligibility_constraints")
    applicability_constraints = None
    
    if eligibility_constraints:
        constraints = eligibility_constraints.get("constraints", {})
        
        # Map document types (eforms_subtype -> document_type_list)
        eforms_subtype = constraints.get("eforms_subtype", [])
        document_type_list = eforms_subtype if isinstance(eforms_subtype, list) else []
        
        # Map time interval (start_date/end_date -> document_time_interval)
        start_date_str = constraints.get("start_date")
        end_date_str = constraints.get("end_date")
        
        start_datetime = None
        end_datetime = None
        
        if start_date_str:
            try:
                start_datetime = datetime.fromisoformat(start_date_str[0].replace("Z", "+00:00"))
            except (ValueError, IndexError):
                pass
        
        if end_date_str:
            try:
                end_datetime = datetime.fromisoformat(end_date_str[0].replace("Z", "+00:00"))
            except (ValueError, IndexError):
                pass
        
        document_time_interval = None
        if start_datetime or end_datetime:
            document_time_interval = DateTimeInterval(
                start=start_datetime,
                end=end_datetime,
            )
        
        # Map document versions (eforms_sdk_versions -> document_version_list or document_version_range)
        eforms_sdk_versions = constraints.get("eforms_sdk_versions", [])
        document_version_list = None
        document_version_range = None
        
        if eforms_sdk_versions and isinstance(eforms_sdk_versions, list) and len(eforms_sdk_versions) > 0:
            # Use document_version_list (could use range for many versions, but list is simpler)
            document_version_list = eforms_sdk_versions
        
        applicability_constraints = ApplicabilityConstraints(
            document_type_list=document_type_list,
            document_time_interval=document_time_interval,
            document_version_list=document_version_list,
            document_version_range=document_version_range,
        )
    
    # Create V3 metadata instance using field arguments directly
    v3_metadata = MappingPackageV3Metadata(
        id=v2_metadata_dict.get("identifier", ""),
        title=v2_metadata_dict.get("title", ""),
        project_identifier=v2_metadata_dict.get("mapping_type") or v2_metadata_dict.get("type", ""),
        created_at=created_at,
        mapping_version=v2_metadata_dict.get("mapping_version", ""),
        model_version=v2_metadata_dict.get("ontology_version", ""),
        description=v2_metadata_dict.get("description"),
        mapping_suite_hash_digest=v2_metadata_dict.get("mapping_suite_hash_digest") or v2_metadata_dict.get("signature", ""),
        path=v2_metadata_dict.get("path", mpv2.metadata.path),
        applicability_constraints=applicability_constraints,
    )
    
    # Create V3 package with converted metadata and all original assets
    v3_package_dict = mpv2.model_dump(exclude={"metadata"})
    v3_package_dict["metadata"] = v3_metadata
    
    return MappingPackageV3(**v3_package_dict)