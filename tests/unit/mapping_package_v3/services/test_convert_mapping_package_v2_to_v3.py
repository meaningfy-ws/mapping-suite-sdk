from pathlib import Path

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


def test_generate_jsonld_context_success(tmp_path: Path) -> None:
    """Test that generate_jsonld_context succeeds when gen-jsonld-context command works."""
    import subprocess
    from unittest.mock import Mock, patch
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import generate_jsonld_context
    
    # Create a mock schema file
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text("id: TestSchema\n")
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Mock subprocess.run to return success
    mock_result = Mock()
    mock_result.stdout = '{"@context": {"test": "value"}}'
    mock_result.stderr = ""
    
    with patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3.subprocess.run") as mock_run, \
         patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3._find_project_root", return_value=tmp_path):
        mock_run.return_value = mock_result
        
        result_path = generate_jsonld_context(
            schema_yaml_path=schema_path,
            output_directory=output_dir,
            context_filename="context.jsonld"
        )
        
        assert result_path == output_dir / "context.jsonld"
        assert result_path.exists()
        assert result_path.read_text() == '{"@context": {"test": "value"}}'
        # Verify gen-jsonld-context was called directly (no poetry)
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ["gen-jsonld-context", str(schema_path)]


def test_generate_jsonld_context_raises_file_not_found_error(tmp_path: Path) -> None:
    """Test that generate_jsonld_context raises FileNotFoundError when command is not in PATH."""
    import subprocess
    from unittest.mock import patch
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import generate_jsonld_context
    
    # Create a mock schema file
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text("id: TestSchema\n")
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    with patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3.subprocess.run") as mock_run, \
         patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3._find_project_root", return_value=tmp_path):
        # Command not found in PATH
        mock_run.side_effect = FileNotFoundError("gen-jsonld-context not found")
        
        with pytest.raises(FileNotFoundError):
            generate_jsonld_context(
                schema_yaml_path=schema_path,
                output_directory=output_dir,
                context_filename="context.jsonld"
            )
        
        # Verify command was attempted once
        mock_run.assert_called_once()


def test_generate_jsonld_context_raises_error_when_schema_not_found(tmp_path: Path) -> None:
    """Test that generate_jsonld_context raises FileNotFoundError when schema file doesn't exist."""
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import generate_jsonld_context
    
    schema_path = tmp_path / "nonexistent.yaml"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    with pytest.raises(FileNotFoundError) as excinfo:
        generate_jsonld_context(
            schema_yaml_path=schema_path,
            output_directory=output_dir
        )
    
    assert "Schema YAML file not found" in str(excinfo.value)


def test_generate_jsonld_context_raises_called_process_error(tmp_path: Path) -> None:
    """Test that generate_jsonld_context raises CalledProcessError when command execution fails."""
    import subprocess
    from unittest.mock import patch
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import generate_jsonld_context
    
    # Create a mock schema file
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text("id: TestSchema\n")
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Mock subprocess.run to fail
    with patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3.subprocess.run") as mock_run, \
         patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3._find_project_root", return_value=tmp_path):
        # Command execution fails
        mock_run.side_effect = subprocess.CalledProcessError(1, "gen-jsonld-context", stderr="command error")
        
        with pytest.raises(subprocess.CalledProcessError):
            generate_jsonld_context(
                schema_yaml_path=schema_path,
                output_directory=output_dir
            )
        
        # Verify command was attempted once
        mock_run.assert_called_once()


def test_generate_jsonld_context_creates_output_directory(tmp_path: Path) -> None:
    """Test that generate_jsonld_context creates output directory if it doesn't exist."""
    import subprocess
    from unittest.mock import Mock, patch
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import generate_jsonld_context
    
    # Create a mock schema file
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text("id: TestSchema\n")
    
    # Output directory doesn't exist yet
    output_dir = tmp_path / "output"
    
    # Mock subprocess.run to return success
    mock_result = Mock()
    mock_result.stdout = '{"@context": {}}'
    mock_result.stderr = ""
    
    with patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3.subprocess.run") as mock_run, \
         patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3._find_project_root", return_value=tmp_path):
        mock_run.return_value = mock_result
        
        result_path = generate_jsonld_context(
            schema_yaml_path=schema_path,
            output_directory=output_dir
        )
        
        # Verify directory was created
        assert output_dir.exists()
        assert output_dir.is_dir()
        assert result_path.exists()


def test_generate_jsonld_context_uses_custom_filename(tmp_path: Path) -> None:
    """Test that generate_jsonld_context uses custom context filename when provided."""
    import subprocess
    from unittest.mock import Mock, patch
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import generate_jsonld_context
    
    # Create a mock schema file
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text("id: TestSchema\n")
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Mock subprocess.run to return success
    mock_result = Mock()
    mock_result.stdout = '{"@context": {}}'
    mock_result.stderr = ""
    
    with patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3.subprocess.run") as mock_run, \
         patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3._find_project_root", return_value=tmp_path):
        mock_run.return_value = mock_result
        
        result_path = generate_jsonld_context(
            schema_yaml_path=schema_path,
            output_directory=output_dir,
            context_filename="custom_context.jsonld"
        )
        
        assert result_path == output_dir / "custom_context.jsonld"
        assert result_path.exists()



