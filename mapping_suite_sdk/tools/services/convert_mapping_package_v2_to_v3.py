"""
Conversion service for MappingPackageV2 to MappingPackageV3.

This module provides functionality to convert MappingPackageV2 (V2) to MappingPackageV3 (V3),
including conversion of metadata structures, constraints, and all package assets.
"""
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2MetadataLoader
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import MappingPackageV2Constraints
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import MappingPackageV2Metadata
from mapping_suite_sdk.mapping_package_v3.adapters.metadata_loader import MappingPackageV3MetadataLoader
from mapping_suite_sdk.mapping_package_v3.adapters.package_loader import MappingPackageV3Loader
from mapping_suite_sdk.mapping_package_v3.adapters.package_loader_lightweight import MappingPackageV3LightweightLoader
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import ApplicabilityConstraints
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import DateTimeInterval
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata_jsonld import MappingPackageV3MetadataJSONLD


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
    # Note: start_date and end_date are Optional[List[str]] - empty list is falsy, so checking the list itself is sufficient
    document_time_interval = None
    start_date_str = v2_constraints.start_date[0] if v2_constraints.start_date else None
    end_date_str = v2_constraints.end_date[0] if v2_constraints.end_date else None
    
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


def detect_mapping_package_version(mapping_package_folder_path: Path) -> Optional[str]:
    """
    Detect the version of a mapping package by attempting to load it.
    
    Tries to load the package with different version loaders to determine its version.
    Returns the version string if detected, None if the package format is not recognized.
    
    Args:
        mapping_package_folder_path: Path to the mapping package folder
        
    Returns:
        Version string (e.g., "v2", "v3", "v3-lightweight") or None if not recognized
    """
    if not mapping_package_folder_path.exists() or not mapping_package_folder_path.is_dir():
        return None
    
    # Handle nested package structure (folder_name/folder_name/metadata.json)
    root_folder = mapping_package_folder_path / mapping_package_folder_path.name
    possible_paths = [mapping_package_folder_path]
    if root_folder.exists():
        possible_paths.append(root_folder)
    
    # Find metadata file
    metadata_file = None
    for path in possible_paths:
        test_file = path / "metadata.json"
        if test_file.exists():
            metadata_file = test_file
            break
        test_file = path / "metadata.jsonld"
        if test_file.exists():
            metadata_file = test_file
            break
    
    if not metadata_file:
        return None
    
    package_root_path = metadata_file.parent
    
    # Try V3 lightweight first (check if conceptual mapping exists)
    has_conceptual_mapping = False
    for path in possible_paths:
        conceptual_mapping_path = path / mssdk_config.MPV3_CONCEPTUAL_MAPPING_FILE_ASSET_PATH
        if conceptual_mapping_path.exists():
            has_conceptual_mapping = True
            break
    
    if not has_conceptual_mapping:
        # No conceptual mapping found, try loading as lightweight
        try:
            loader = MappingPackageV3LightweightLoader()
            loader.load(package_root_path)
            return "v3-lightweight"
        except (ValidationError, FileNotFoundError, ValueError):
            pass
    
    # Try V3 (full)
    try:
        metadata_loader = MappingPackageV3MetadataLoader()
        metadata_loader.load(
            package_folder_path=mapping_package_folder_path,
            relative_asset_path=Path(metadata_file.name)
        )
        # Metadata is valid V3, check if it's full v3
        loader = MappingPackageV3Loader()
        package = loader.load(package_root_path)
        if hasattr(package, 'conceptual_mapping_asset') and package.conceptual_mapping_asset is not None:
            return "v3"
    except (ValidationError, FileNotFoundError, ValueError):
        pass
    
    # Try V2
    try:
        metadata_loader = MappingPackageV2MetadataLoader()
        metadata_loader.load(
            package_folder_path=mapping_package_folder_path,
            relative_asset_path=Path(metadata_file.name)
        )
        # If metadata loads successfully, try loading full package
        loader = MappingPackageV2Loader()
        loader.load(package_root_path)
        return "v2"
    except (ValidationError, FileNotFoundError, ValueError):
        pass
    
    # Not recognized
    return None


def is_mapping_package_already_converted(mapping_package_folder_path: Path, to_version: str) -> bool:
    """
    Check if a mapping package is already in the target version.
    
    Uses version detection to determine the current version and compares it to the target version.
    
    Args:
        mapping_package_folder_path: Path to the mapping package folder
        to_version: Target version string (e.g., "v3", "v3-lightweight")
        
    Returns:
        True if the package is already in the target version, False otherwise
    """
    detected_version = detect_mapping_package_version(mapping_package_folder_path)
    return detected_version == to_version
