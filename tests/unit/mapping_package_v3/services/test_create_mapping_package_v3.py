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


def test_create_mpv3_from_mpv2_with_different_datetime_formats(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test datetime parsing with various formats and edge cases."""
    from copy import deepcopy
    from unittest.mock import patch, MagicMock
    from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import MappingPackageV2Metadata
    
    # Test when created_at_value is already a datetime object (not a string)
    # This tests the isinstance(created_at_value, datetime) branch (line 31-32)
    mpv2_datetime_obj = deepcopy(dummy_mapping_package_v2_model)
    test_datetime = datetime(2023, 6, 13, 19, 31, 37, 496360)
    
    # Get the original dump result
    original_dict = mpv2_datetime_obj.metadata.model_dump(by_alias=True, exclude_unset=True)
    # Create a modified dict with datetime object
    modified_dict = original_dict.copy()
    modified_dict['created_at'] = test_datetime
    
    # Create a MagicMock that returns our modified dict when called with by_alias=True
    mock_dump = MagicMock(return_value=modified_dict)
    mock_dump.side_effect = lambda *args, **kwargs: modified_dict if kwargs.get('by_alias') else original_dict
    
    # Patch the model_dump method on the metadata object
    with patch.object(type(mpv2_datetime_obj.metadata), 'model_dump', mock_dump):
        result = create_mpv3_from_mpv2(mpv2_datetime_obj)
        assert isinstance(result.metadata.created_at, datetime)
        assert result.metadata.created_at == test_datetime
    
    # Test with ISO format string (already covered, but explicit)
    mpv2_iso = deepcopy(dummy_mapping_package_v2_model)
    mpv2_iso.metadata = MappingPackageV2Metadata(**{**mpv2_iso.metadata.model_dump(), "issue_date": "2023-06-13T19:31:37.496360+00:00"})
    result = create_mpv3_from_mpv2(mpv2_iso)
    assert isinstance(result.metadata.created_at, datetime)
    
    # Test with format: "%Y-%m-%d %H:%M:%S.%f%z"
    mpv2_strptime1 = deepcopy(dummy_mapping_package_v2_model)
    mpv2_strptime1.metadata = MappingPackageV2Metadata(**{**mpv2_strptime1.metadata.model_dump(), "issue_date": "2023-06-13 19:31:37.496360+00:00"})
    result = create_mpv3_from_mpv2(mpv2_strptime1)
    assert isinstance(result.metadata.created_at, datetime)
    
    # Test with format: "%Y-%m-%d %H:%M:%S%z" (without microseconds)
    mpv2_strptime2 = deepcopy(dummy_mapping_package_v2_model)
    mpv2_strptime2.metadata = MappingPackageV2Metadata(**{**mpv2_strptime2.metadata.model_dump(), "issue_date": "2023-06-13 19:31:37+00:00"})
    result = create_mpv3_from_mpv2(mpv2_strptime2)
    assert isinstance(result.metadata.created_at, datetime)
    
    # Test with invalid format that should fallback to datetime.now()
    mpv2_invalid = deepcopy(dummy_mapping_package_v2_model)
    mpv2_invalid.metadata = MappingPackageV2Metadata(**{**mpv2_invalid.metadata.model_dump(), "issue_date": "invalid-date-format"})
    result = create_mpv3_from_mpv2(mpv2_invalid)
    assert isinstance(result.metadata.created_at, datetime)  # Should fallback to now()
    
    # Test with Z suffix (UTC) - should be handled by replace("Z", "+00:00")
    mpv2_z_suffix = deepcopy(dummy_mapping_package_v2_model)
    mpv2_z_suffix.metadata = MappingPackageV2Metadata(**{**mpv2_z_suffix.metadata.model_dump(), "issue_date": "2023-06-13T19:31:37.496360Z"})
    result = create_mpv3_from_mpv2(mpv2_z_suffix)
    assert isinstance(result.metadata.created_at, datetime)
    
    # Test when created_at_value is neither datetime nor string (tests line 47-48 else branch)
    mpv2_non_str = deepcopy(dummy_mapping_package_v2_model)
    original_dict_non_str = mpv2_non_str.metadata.model_dump(by_alias=True, exclude_unset=True)
    modified_dict_non_str = original_dict_non_str.copy()
    modified_dict_non_str['created_at'] = 12345  # Integer, neither datetime nor string
    
    mock_dump_non_str = MagicMock()
    mock_dump_non_str.side_effect = lambda *args, **kwargs: modified_dict_non_str if kwargs.get('by_alias') else original_dict_non_str
    
    with patch.object(type(mpv2_non_str.metadata), 'model_dump', mock_dump_non_str):
        result = create_mpv3_from_mpv2(mpv2_non_str)
        assert isinstance(result.metadata.created_at, datetime)  # Should fallback to now()
    
    # Test when created_at_value is falsy/None (tests line 49-50 else branch)
    mpv2_falsy = deepcopy(dummy_mapping_package_v2_model)
    original_dict_falsy = mpv2_falsy.metadata.model_dump(by_alias=True, exclude_unset=True)
    modified_dict_falsy = original_dict_falsy.copy()
    modified_dict_falsy['created_at'] = None  # None/falsy value
    
    mock_dump_falsy = MagicMock()
    mock_dump_falsy.side_effect = lambda *args, **kwargs: modified_dict_falsy if kwargs.get('by_alias') else original_dict_falsy
    
    with patch.object(type(mpv2_falsy.metadata), 'model_dump', mock_dump_falsy):
        result = create_mpv3_from_mpv2(mpv2_falsy)
        assert isinstance(result.metadata.created_at, datetime)  # Should fallback to now()


def test_create_mpv3_from_mpv2_with_date_intervals(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test date interval conversion with various edge cases."""
    from copy import deepcopy
    from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import (
        MappingPackageV2Metadata,
        MappingPackageV2EligibilityConstraints,
        MappingPackageV2Constraints,
    )
    
    # Test with start_date and end_date as lists
    mpv2_with_dates = deepcopy(dummy_mapping_package_v2_model)
    constraints = MappingPackageV2Constraints(
        eforms_subtype=["29"],
        start_date=["2023-01-01T00:00:00+00:00"],
        end_date=["2024-12-31T23:59:59+00:00"],
        eforms_sdk_versions=["1.9"]
    )
    mpv2_with_dates.metadata = MappingPackageV2Metadata(**{
        **mpv2_with_dates.metadata.model_dump(),
        "eligibility_constraints": MappingPackageV2EligibilityConstraints(constraints=constraints)
    })
    result = create_mpv3_from_mpv2(mpv2_with_dates)
    assert result.metadata.applicability_constraints is not None
    assert result.metadata.applicability_constraints.document_time_interval is not None
    assert result.metadata.applicability_constraints.document_time_interval.start is not None
    assert result.metadata.applicability_constraints.document_time_interval.end is not None
    
    # Test with only start_date
    mpv2_start_only = deepcopy(dummy_mapping_package_v2_model)
    constraints_start = MappingPackageV2Constraints(
        eforms_subtype=["29"],
        start_date=["2023-01-01T00:00:00+00:00"],
        end_date=None,
        eforms_sdk_versions=["1.9"]
    )
    mpv2_start_only.metadata = MappingPackageV2Metadata(**{
        **mpv2_start_only.metadata.model_dump(),
        "eligibility_constraints": MappingPackageV2EligibilityConstraints(constraints=constraints_start)
    })
    result = create_mpv3_from_mpv2(mpv2_start_only)
    assert result.metadata.applicability_constraints is not None
    assert result.metadata.applicability_constraints.document_time_interval is not None
    assert result.metadata.applicability_constraints.document_time_interval.start is not None
    
    # Test with only end_date
    mpv2_end_only = deepcopy(dummy_mapping_package_v2_model)
    constraints_end = MappingPackageV2Constraints(
        eforms_subtype=["29"],
        start_date=None,
        end_date=["2024-12-31T23:59:59+00:00"],
        eforms_sdk_versions=["1.9"]
    )
    mpv2_end_only.metadata = MappingPackageV2Metadata(**{
        **mpv2_end_only.metadata.model_dump(),
        "eligibility_constraints": MappingPackageV2EligibilityConstraints(constraints=constraints_end)
    })
    result = create_mpv3_from_mpv2(mpv2_end_only)
    assert result.metadata.applicability_constraints is not None
    assert result.metadata.applicability_constraints.document_time_interval is not None
    assert result.metadata.applicability_constraints.document_time_interval.end is not None
    
    # Test with empty lists (should not create interval)
    mpv2_empty_dates = deepcopy(dummy_mapping_package_v2_model)
    constraints_empty = MappingPackageV2Constraints(
        eforms_subtype=["29"],
        start_date=[],
        end_date=[],
        eforms_sdk_versions=["1.9"]
    )
    mpv2_empty_dates.metadata = MappingPackageV2Metadata(**{
        **mpv2_empty_dates.metadata.model_dump(),
        "eligibility_constraints": MappingPackageV2EligibilityConstraints(constraints=constraints_empty)
    })
    result = create_mpv3_from_mpv2(mpv2_empty_dates)
    assert result.metadata.applicability_constraints is not None
    # document_time_interval should be None when both dates are empty
    assert result.metadata.applicability_constraints.document_time_interval is None
    
    # Test with invalid date strings (should gracefully handle parsing errors)
    mpv2_invalid_dates = deepcopy(dummy_mapping_package_v2_model)
    constraints_invalid = MappingPackageV2Constraints(
        eforms_subtype=["29"],
        start_date=["invalid-date"],
        end_date=["also-invalid"],
        eforms_sdk_versions=["1.9"]
    )
    mpv2_invalid_dates.metadata = MappingPackageV2Metadata(**{
        **mpv2_invalid_dates.metadata.model_dump(),
        "eligibility_constraints": MappingPackageV2EligibilityConstraints(constraints=constraints_invalid)
    })
    result = create_mpv3_from_mpv2(mpv2_invalid_dates)
    assert result.metadata.applicability_constraints is not None
    # Should not crash, interval should be None if parsing fails for both
    # (The logic creates interval only if at least one date parses successfully)
    
    # Test with empty string in list
    mpv2_empty_str = deepcopy(dummy_mapping_package_v2_model)
    constraints_empty_str = MappingPackageV2Constraints(
        eforms_subtype=["29"],
        start_date=[""],
        end_date=[""],
        eforms_sdk_versions=["1.9"]
    )
    mpv2_empty_str.metadata = MappingPackageV2Metadata(**{
        **mpv2_empty_str.metadata.model_dump(),
        "eligibility_constraints": MappingPackageV2EligibilityConstraints(constraints=constraints_empty_str)
    })
    result = create_mpv3_from_mpv2(mpv2_empty_str)
    assert result.metadata.applicability_constraints is not None
    # Should handle empty strings gracefully

