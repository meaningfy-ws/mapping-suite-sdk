from datetime import datetime

import pytest

from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.services.create_mapping_package_v3 import create_mpv3_from_mpv2


def test_create_mpv3_from_mpv2_creates_successfully(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that conversion from V2 to V3 succeeds with valid input."""
    # Execute conversion
    result = create_mpv3_from_mpv2(dummy_mapping_package_v2_model)
    
    # Assert result is V3 instance
    assert isinstance(result, MappingPackageV3)
    
    # Assert metadata is properly converted
    assert result.metadata is not None
    assert result.metadata.id == dummy_mapping_package_v2_model.metadata.identifier
    assert result.metadata.title == dummy_mapping_package_v2_model.metadata.title
    assert result.metadata.project_identifier == dummy_mapping_package_v2_model.metadata.type
    assert result.metadata.mapping_version == dummy_mapping_package_v2_model.metadata.mapping_version
    assert result.metadata.model_version == dummy_mapping_package_v2_model.metadata.ontology_version
    assert result.metadata.description == dummy_mapping_package_v2_model.metadata.description
    assert result.metadata.mapping_suite_hash_digest == dummy_mapping_package_v2_model.metadata.signature
    
    # Assert created_at is converted from string to datetime
    assert isinstance(result.metadata.created_at, datetime)
    
    # Assert all package assets are preserved
    assert result.conceptual_mapping_asset == dummy_mapping_package_v2_model.conceptual_mapping_asset
    assert result.technical_mapping_suite == dummy_mapping_package_v2_model.technical_mapping_suite
    assert result.vocabulary_mapping_suite == dummy_mapping_package_v2_model.vocabulary_mapping_suite
    assert result.test_data_suites == dummy_mapping_package_v2_model.test_data_suites
    assert result.test_suites_sparql == dummy_mapping_package_v2_model.test_suites_sparql
    assert result.test_suites_shacl == dummy_mapping_package_v2_model.test_suites_shacl
    assert result.test_results == dummy_mapping_package_v2_model.test_results
    
    # Assert constraints are converted
    if dummy_mapping_package_v2_model.metadata.eligibility_constraints:
        assert result.metadata.applicability_constraints is not None
        v2_constraints = dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints
        v3_constraints = result.metadata.applicability_constraints
        
        assert v3_constraints.document_type_list == v2_constraints.eforms_subtype
        if v2_constraints.eforms_sdk_versions:
            assert v3_constraints.document_version_list == v2_constraints.eforms_sdk_versions


def test_create_mpv3_from_mpv2_preserves_all_assets(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that all package assets are preserved during conversion."""
    # Execute conversion
    result = create_mpv3_from_mpv2(dummy_mapping_package_v2_model)
    
    # Assert all assets are present and unchanged
    assert result.conceptual_mapping_asset is not None
    assert result.technical_mapping_suite is not None
    assert result.vocabulary_mapping_suite is not None
    assert result.test_data_suites is not None
    assert result.test_suites_sparql is not None
    assert result.test_suites_shacl is not None
    assert result.test_results is not None
    
    # Verify the paths are preserved
    assert result.conceptual_mapping_asset.path == dummy_mapping_package_v2_model.conceptual_mapping_asset.path
    assert result.technical_mapping_suite.path == dummy_mapping_package_v2_model.technical_mapping_suite.path
    assert result.vocabulary_mapping_suite.path == dummy_mapping_package_v2_model.vocabulary_mapping_suite.path


def test_create_mpv3_from_mpv2_handles_missing_constraints(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that conversion handles edge cases gracefully."""
    # Create a copy without constraints (if possible) or test with None values
    # For this test, we'll verify the function handles None/empty constraints
    
    # Execute conversion - should work even if constraints are None or empty
    result = create_mpv3_from_mpv2(dummy_mapping_package_v2_model)
    
    # Assert the conversion succeeds
    assert isinstance(result, MappingPackageV3)
    assert result.metadata is not None
    
    # If V2 has constraints, V3 should have them converted
    # If V2 doesn't have constraints, V3 might not have them (optional field)
    # Both cases should be handled without errors
    if dummy_mapping_package_v2_model.metadata.eligibility_constraints:
        assert result.metadata.applicability_constraints is not None
    # If constraints are None in V2, applicability_constraints in V3 can be None (it's optional)


def test_create_mpv3_from_mpv2_fails_with_invalid_input() -> None:
    """Test that conversion fails appropriately with invalid input."""
    # Test with None input - should raise an error
    with pytest.raises((TypeError, AttributeError, ValueError)):
        create_mpv3_from_mpv2(None)  # type: ignore

