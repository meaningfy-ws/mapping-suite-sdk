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
    
    This function transforms the metadata structure from V2 (eForms-specific) to V3 (Unified) format,
    while preserving all package assets (conceptual mappings, technical mappings, vocabulary mappings,
    test suites, etc.).
    
    Args:
        mpv2: The MappingPackageV2 instance to convert.
        
    Returns:
        A new MappingPackageV3 instance with converted metadata and all original assets.
    """
    # Get V2 metadata as dict for manipulation
    v2_metadata_dict = mpv2.metadata.model_dump(by_alias=True, exclude_unset=True)
    
    # Convert created_at from string to datetime
    created_at_value = v2_metadata_dict.get("created_at") or v2_metadata_dict.get("issue_date")
    if created_at_value:
        if isinstance(created_at_value, datetime):
            created_at = created_at_value
        elif isinstance(created_at_value, str):
            # Try parsing with various formats
            try:
                created_at = datetime.fromisoformat(created_at_value.replace("Z", "+00:00"))
            except ValueError:
                # Fallback: try other common formats
                try:
                    created_at = datetime.strptime(created_at_value, "%Y-%m-%d %H:%M:%S.%f%z")
                except ValueError:
                    try:
                        created_at = datetime.strptime(created_at_value, "%Y-%m-%d %H:%M:%S%z")
                    except ValueError:
                        # Last resort: use current time
                        created_at = datetime.now()
        else:
            created_at = datetime.now()
    else:
        created_at = datetime.now()
    
    # Build V3 metadata dict
    v3_metadata_dict = {
        "id": v2_metadata_dict.get("identifier", ""),
        "title": v2_metadata_dict.get("title", ""),
        "project_identifier": v2_metadata_dict.get("mapping_type") or v2_metadata_dict.get("type", ""),
        "created_at": created_at,  # datetime object
        "mapping_version": v2_metadata_dict.get("mapping_version", ""),
        "model_version": v2_metadata_dict.get("ontology_version", ""),
        "description": v2_metadata_dict.get("description"),
        "mapping_suite_hash_digest": v2_metadata_dict.get("mapping_suite_hash_digest") or v2_metadata_dict.get("signature", ""),
        "path": v2_metadata_dict.get("path", mpv2.metadata.path),
    }
    
    # Convert eligibility_constraints to applicability_constraints
    eligibility_constraints = v2_metadata_dict.get("metadata_constraints") or v2_metadata_dict.get("eligibility_constraints")
    if eligibility_constraints:
        constraints = eligibility_constraints.get("constraints", {})
        
        # Map document types (eforms_subtype -> document_type_list)
        eforms_subtype = constraints.get("eforms_subtype", [])
        document_type_list = eforms_subtype if isinstance(eforms_subtype, list) else []
        
        # Map time interval (start_date/end_date -> document_time_interval)
        start_date_str = constraints.get("start_date")
        end_date_str = constraints.get("end_date")
        
        document_time_interval = None
        # V2 has Optional[List[str]], check if we have valid values
        if (start_date_str and (isinstance(start_date_str, list) and len(start_date_str) > 0)) or \
           (end_date_str and (isinstance(end_date_str, list) and len(end_date_str) > 0)):
            start_datetime = None
            end_datetime = None
            
            # V2 has List[str] or None, we take first if list
            if start_date_str and isinstance(start_date_str, list) and len(start_date_str) > 0:
                start_date_value = start_date_str[0]
                if start_date_value:
                    try:
                        start_datetime = datetime.fromisoformat(start_date_value.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass
            
            if end_date_str and isinstance(end_date_str, list) and len(end_date_str) > 0:
                end_date_value = end_date_str[0]
                if end_date_value:
                    try:
                        end_datetime = datetime.fromisoformat(end_date_value.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass
            
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
        
        v3_metadata_dict["applicability_constraints"] = ApplicabilityConstraints(
            document_type_list=document_type_list,
            document_time_interval=document_time_interval,
            document_version_list=document_version_list,
            document_version_range=document_version_range,
        )
    
    # Create V3 metadata instance
    v3_metadata = MappingPackageV3Metadata(**v3_metadata_dict)
    
    # Create V3 package with converted metadata and all original assets
    v3_package_dict = mpv2.model_dump(exclude={"metadata"})
    v3_package_dict["metadata"] = v3_metadata
    
    return MappingPackageV3(**v3_package_dict)