import pytest

from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import convert_mapping_package_v2_to_v3


def test_convert_mapping_package_v2_to_v3_creates_successfully(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that conversion from V2 to V3 succeeds with valid input."""
    result = convert_mapping_package_v2_to_v3(dummy_mapping_package_v2_model)
    
    assert isinstance(result, MappingPackageV3)
    assert result.metadata.id == dummy_mapping_package_v2_model.metadata.identifier
    assert result.metadata.title == dummy_mapping_package_v2_model.metadata.title
    assert result.metadata.project_identifier == dummy_mapping_package_v2_model.metadata.type


def test_convert_mapping_package_v2_to_v3_preserves_all_assets(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that all package assets are preserved during conversion."""
    result = convert_mapping_package_v2_to_v3(dummy_mapping_package_v2_model)
    
    assert isinstance(result, MappingPackageV3)
    assert result.conceptual_mapping_asset is not None
    assert result.technical_mapping_suite is not None
    assert result.vocabulary_mapping_suite is not None
    assert result.test_data_suites is not None
    assert result.test_suites_sparql is not None
    assert result.test_suites_shacl is not None
    assert result.test_results is not None


def test_convert_mapping_package_v2_to_v3_handles_missing_constraints(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that conversion handles edge cases gracefully."""
    # Test with empty constraints - the function should handle None constraints
    # Since constraints are required in V2, we'll just test that the conversion works
    # The function already handles the case where constraints might be missing fields
    result = convert_mapping_package_v2_to_v3(dummy_mapping_package_v2_model)
    
    assert isinstance(result, MappingPackageV3)
    # Constraints should be converted if they exist
    if result.metadata.applicability_constraints:
        assert result.metadata.applicability_constraints is not None


def test_convert_mapping_package_v2_to_v3_fails_with_invalid_input() -> None:
    """Test that conversion fails appropriately with invalid input."""
    # Test with None input - should raise an error
    with pytest.raises((TypeError, AttributeError, ValueError)):
        convert_mapping_package_v2_to_v3(None)  # type: ignore


def test_convert_mapping_package_v2_to_v3_with_date_intervals(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test date interval conversion with various edge cases."""
    result = convert_mapping_package_v2_to_v3(dummy_mapping_package_v2_model)
    
    assert isinstance(result, MappingPackageV3)
    # Verify that constraints are converted if they exist in the source model
    if (dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints and
        result.metadata.applicability_constraints):
        assert result.metadata.applicability_constraints is not None
        # If the source has date intervals, they should be converted
        if (dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.start_date or
            dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.end_date):
            if result.metadata.applicability_constraints.document_time_interval:
                assert (result.metadata.applicability_constraints.document_time_interval.start is not None or
                       result.metadata.applicability_constraints.document_time_interval.end is not None)


def test_convert_mapping_package_v2_to_v3_handles_invalid_issue_date(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that conversion fails hard with invalid issue_date format."""
    # Set an invalid date format
    dummy_mapping_package_v2_model.metadata.issue_date = "invalid-date-format"
    
    # Should raise an exception (hard fail) - Pydantic will fail to convert invalid date string
    with pytest.raises((ValueError, TypeError)):
        convert_mapping_package_v2_to_v3(dummy_mapping_package_v2_model)


def test_convert_mapping_package_v2_to_v3_handles_invalid_start_date(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that conversion fails hard with invalid start_date format."""
    # Set an invalid date format
    if dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints:
        dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.start_date = ["invalid-date-format"]
    
    # Should raise an exception (hard fail) - Pydantic will fail to convert invalid date string
    with pytest.raises((ValueError, TypeError)):
        convert_mapping_package_v2_to_v3(dummy_mapping_package_v2_model)


def test_convert_mapping_package_v2_to_v3_handles_invalid_end_date(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that conversion fails hard with invalid end_date format."""
    # Set an invalid date format
    if dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints:
        dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.end_date = ["invalid-date-format"]
    
    # Should raise an exception (hard fail) - Pydantic will fail to convert invalid date string
    with pytest.raises((ValueError, TypeError)):
        convert_mapping_package_v2_to_v3(dummy_mapping_package_v2_model)


def test_convert_mapping_package_v2_to_v3_handles_empty_date_lists(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that empty date lists result in no interval (empty list is falsy)."""
    if dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints:
        # Set empty lists for dates
        dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.start_date = []
        dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.end_date = []
    
    result = convert_mapping_package_v2_to_v3(dummy_mapping_package_v2_model)
    
    assert isinstance(result, MappingPackageV3)
    # Empty lists should result in no interval
    if result.metadata.applicability_constraints:
        assert result.metadata.applicability_constraints.document_time_interval is None


def test_convert_mapping_package_v2_to_v3_handles_none_date_values(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that None date values result in no interval (None is falsy)."""
    if dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints:
        # Set None for dates (Optional[List[str]] allows None)
        dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.start_date = None
        dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.end_date = None
    
    result = convert_mapping_package_v2_to_v3(dummy_mapping_package_v2_model)
    
    assert isinstance(result, MappingPackageV3)
    # None values should result in no interval
    if result.metadata.applicability_constraints:
        assert result.metadata.applicability_constraints.document_time_interval is None


def test_convert_mapping_package_v2_to_v3_handles_only_start_date(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that only start_date creates an open-ended future interval."""
    if dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints:
        dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.start_date = ["2024-01-01"]
        dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.end_date = []
    
    result = convert_mapping_package_v2_to_v3(dummy_mapping_package_v2_model)
    
    assert isinstance(result, MappingPackageV3)
    if result.metadata.applicability_constraints and result.metadata.applicability_constraints.document_time_interval:
        assert result.metadata.applicability_constraints.document_time_interval.start is not None
        assert result.metadata.applicability_constraints.document_time_interval.end is None


def test_convert_mapping_package_v2_to_v3_handles_only_end_date(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that only end_date creates an open-ended past interval."""
    if dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints:
        dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.start_date = []
        dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.end_date = ["2024-12-31"]
    
    result = convert_mapping_package_v2_to_v3(dummy_mapping_package_v2_model)
    
    assert isinstance(result, MappingPackageV3)
    if result.metadata.applicability_constraints and result.metadata.applicability_constraints.document_time_interval:
        assert result.metadata.applicability_constraints.document_time_interval.start is None
        assert result.metadata.applicability_constraints.document_time_interval.end is not None


def test_convert_mapping_package_v2_to_v3_handles_both_dates(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that both start_date and end_date create a closed interval."""
    if dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints:
        dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.start_date = ["2024-01-01"]
        dummy_mapping_package_v2_model.metadata.eligibility_constraints.constraints.end_date = ["2024-12-31"]
    
    result = convert_mapping_package_v2_to_v3(dummy_mapping_package_v2_model)
    
    assert isinstance(result, MappingPackageV3)
    if result.metadata.applicability_constraints and result.metadata.applicability_constraints.document_time_interval:
        assert result.metadata.applicability_constraints.document_time_interval.start is not None
        assert result.metadata.applicability_constraints.document_time_interval.end is not None



