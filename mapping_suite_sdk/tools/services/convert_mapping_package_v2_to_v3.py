"""
Conversion service for MappingPackageV2 to MappingPackageV3.

This module provides functionality to convert MappingPackageV2 (V2) to MappingPackageV3 (V3),
including conversion of metadata structures, constraints, and all package assets.
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.adapters.tracer import traced_routine
from mapping_suite_sdk.core.adapters.version_detector import detect_mapping_package_version
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import MappingPackageV2Constraints
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import MappingPackageV2Metadata
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import ApplicabilityConstraints
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import DateTimeInterval
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata_jsonld import MappingPackageV3MetadataJSONLD

logger = logging.getLogger(__name__)


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
        document_schema_version_list=v2_constraints.eforms_sdk_versions if v2_constraints.eforms_sdk_versions else None
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

    # Convert metadata path from V2 (metadata.json) to V3 (metadata.jsonld)
    v3_metadata_path = mssdk_config.MPV3_METADATA_FILE_ASSET_PATH
    
    return MappingPackageV3(
        metadata=MappingPackageV3MetadataJSONLD(
            path=v3_metadata_path,
            context="./context.jsonld",  # Set JSON-LD context for proper JSON-LD serialization
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


@traced_routine
def generate_jsonld_context(
    schema_yaml_path: Path,
    output_directory: Path,
    context_filename: str = "context.jsonld"
) -> Path:
    """
    Generate a JSON-LD context file from a LinkML schema YAML.
    
    Uses the LinkML gen-jsonld-context command to generate a context.jsonld file
    that defines the JSON-LD context for mapping package metadata.
    
    Args:
        schema_yaml_path: Path to the LinkML schema YAML file (relative to project root)
        output_directory: Directory where the context.jsonld file should be written
            (typically the same directory as metadata.jsonld)
        context_filename: Name of the output context file (default: "context.jsonld")
        
    Returns:
        Path to the generated context.jsonld file
        
    Raises:
        FileNotFoundError: If the schema YAML file does not exist
        subprocess.CalledProcessError: If the gen-jsonld-context command fails
        OSError: If the output directory cannot be created or written to
    """
    # Find project root and resolve schema path
    project_root = _find_project_root(Path.cwd())
    
    # Resolve schema path relative to project root
    if not schema_yaml_path.is_absolute():
        schema_yaml_path = project_root / schema_yaml_path
        
    if not schema_yaml_path.exists():
        raise FileNotFoundError(f"Schema YAML file not found: {schema_yaml_path}")
    
    # Ensure output directory exists
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / context_filename
    
    logger.debug(f"Generating JSON-LD context from {schema_yaml_path} to {output_path}")
    
    # Try with poetry run first (most reliable in development environments)
    try:
        result = subprocess.run(
            ["poetry", "run", "gen-jsonld-context", str(schema_yaml_path)],
            capture_output=True,
            text=True,
            check=True,
            cwd=project_root
        )
        
        # Write the output to the context file
        output_path.write_text(result.stdout, encoding="utf-8")
        
        logger.info(f"Generated JSON-LD context file: {output_path}")
        return output_path
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        # If poetry run fails, try direct command (might work if installed globally)
        logger.debug("poetry run gen-jsonld-context failed, trying direct command")
        try:
            result = subprocess.run(
                ["gen-jsonld-context", str(schema_yaml_path)],
                capture_output=True,
                text=True,
                check=True,
                cwd=project_root
            )
            
            output_path.write_text(result.stdout, encoding="utf-8")
            logger.info(f"Generated JSON-LD context file: {output_path}")
            return output_path
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e2:
            error_msg = e.stderr if hasattr(e, 'stderr') and e.stderr else str(e)
            if hasattr(e2, 'stderr') and e2.stderr:
                error_msg = e2.stderr
            logger.error(f"Failed to generate JSON-LD context: {error_msg}")
            raise RuntimeError(f"Failed to generate JSON-LD context. Ensure 'gen-jsonld-context' is available via 'poetry run' or in PATH. Error: {error_msg}")


def _find_project_root(start_path: Path) -> Path:
    """
    Find the project root by looking for common markers (pyproject.toml, etc.).
    
    Args:
        start_path: Starting directory to search from
        
    Returns:
        Path to project root
        
    Raises:
        FileNotFoundError: If project root cannot be found
    """
    current = start_path.resolve()
    
    # Look for project markers
    markers = ["pyproject.toml", "poetry.lock", ".git"]
    
    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent
    
    # If we reach here, we couldn't find the root
    # Fall back to assuming current working directory is project root
    return Path.cwd()
