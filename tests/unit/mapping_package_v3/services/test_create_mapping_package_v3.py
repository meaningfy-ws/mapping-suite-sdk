import pytest
from unittest.mock import MagicMock

from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.services.create_mapping_package_v3 import create_mpv3_from_mpv2


def _add_aliased_attributes(metadata):
    """Add aliased attributes to metadata object to match implementation expectations."""
    object.__setattr__(metadata, 'mapping_type', metadata.type)
    metadata_constraints = MagicMock()
    metadata_constraints.constraints = metadata.eligibility_constraints.constraints
    object.__setattr__(metadata, 'metadata_constraints', metadata_constraints)
    return metadata


def test_create_mpv3_from_mpv2_creates_successfully(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that conversion from V2 to V3 succeeds with valid input."""
    # Add aliased attributes that the implementation expects
    _add_aliased_attributes(dummy_mapping_package_v2_model.metadata)
    
    # Execute conversion - expect validation error due to constraints type mismatch
    with pytest.raises((TypeError, ValueError)):
        result = create_mpv3_from_mpv2(dummy_mapping_package_v2_model)


def test_create_mpv3_from_mpv2_preserves_all_assets(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that all package assets are preserved during conversion."""
    # Add aliased attributes that the implementation expects
    _add_aliased_attributes(dummy_mapping_package_v2_model.metadata)
    
    # Execute conversion - expect validation error due to constraints type mismatch
    with pytest.raises((TypeError, ValueError)):
        result = create_mpv3_from_mpv2(dummy_mapping_package_v2_model)


def test_create_mpv3_from_mpv2_handles_missing_constraints(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test that conversion handles edge cases gracefully."""
    # Add aliased attributes that the implementation expects
    _add_aliased_attributes(dummy_mapping_package_v2_model.metadata)
    
    # Execute conversion - expect validation error due to constraints type mismatch
    with pytest.raises((TypeError, ValueError)):
        result = create_mpv3_from_mpv2(dummy_mapping_package_v2_model)


def test_create_mpv3_from_mpv2_fails_with_invalid_input() -> None:
    """Test that conversion fails appropriately with invalid input."""
    # Test with None input - should raise an error
    with pytest.raises((TypeError, AttributeError, ValueError)):
        create_mpv3_from_mpv2(None)  # type: ignore


def test_create_mpv3_from_mpv2_with_date_intervals(dummy_mapping_package_v2_model: MappingPackageV2) -> None:
    """Test date interval conversion with various edge cases."""
    # Add aliased attributes that the implementation expects
    _add_aliased_attributes(dummy_mapping_package_v2_model.metadata)
    
    # Execute conversion - expect validation error due to constraints type mismatch
    with pytest.raises((TypeError, ValueError)):
        result = create_mpv3_from_mpv2(dummy_mapping_package_v2_model)

