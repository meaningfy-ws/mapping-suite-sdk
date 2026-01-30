import pytest

from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_hasher import MappingPackageV3Hasher
from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import convert_mapping_package_v3_to_v3_lightweight


def test_convert_mapping_package_v3_to_v3_lightweight_creates_successfully(fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    """Test that conversion from V3 to V3-lightweight succeeds with valid input."""
    result = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    
    assert isinstance(result, MappingPackageV3Lightweight)
    assert result.metadata == fixture_mapping_package_v3_model.metadata
    assert result.technical_mapping_suite == fixture_mapping_package_v3_model.technical_mapping_suite
    assert result.vocabulary_mapping_suite == fixture_mapping_package_v3_model.vocabulary_mapping_suite
    assert result.metadata.mapping_suite_hash_digest == MappingPackageV3Hasher(result).hash()


def test_convert_mapping_package_v3_to_v3_lightweight_preserves_essential_components(fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    """Test that essential components are preserved during conversion."""
    result = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    
    assert isinstance(result, MappingPackageV3Lightweight)
    # Essential components should be preserved
    assert result.metadata is not None
    assert result.technical_mapping_suite is not None
    assert result.vocabulary_mapping_suite is not None
    
    # Metadata is copied (we recompute the signature for the lightweight package).
    assert result.metadata is not fixture_mapping_package_v3_model.metadata
    assert result.technical_mapping_suite is fixture_mapping_package_v3_model.technical_mapping_suite
    assert result.vocabulary_mapping_suite is fixture_mapping_package_v3_model.vocabulary_mapping_suite


def test_convert_mapping_package_v3_to_v3_lightweight_excludes_non_essential_components(fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    """Test that non-essential components are excluded from lightweight version."""
    result = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    
    assert isinstance(result, MappingPackageV3Lightweight)
    # Non-essential components should not be in lightweight version
    assert not hasattr(result, 'conceptual_mapping_asset')
    assert not hasattr(result, 'test_data_suites')
    assert not hasattr(result, 'test_suites_sparql')
    assert not hasattr(result, 'test_suites_shacl')
    assert not hasattr(result, 'test_results')
    
    # Verify source still has these components
    assert hasattr(fixture_mapping_package_v3_model, 'conceptual_mapping_asset')
    assert hasattr(fixture_mapping_package_v3_model, 'test_data_suites')
    assert hasattr(fixture_mapping_package_v3_model, 'test_suites_sparql')
    assert hasattr(fixture_mapping_package_v3_model, 'test_suites_shacl')
    assert hasattr(fixture_mapping_package_v3_model, 'test_results')


def test_convert_mapping_package_v3_to_v3_lightweight_fails_with_invalid_input() -> None:
    """Test that conversion fails appropriately with invalid input."""
    # Test with None input - should raise an error
    with pytest.raises((TypeError, AttributeError, ValueError)):
        convert_mapping_package_v3_to_v3_lightweight(None)  # type: ignore


def test_convert_mapping_package_v3_to_v3_lightweight_metadata_unchanged(fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    """Test that metadata is copied as-is without modification."""
    original_metadata = fixture_mapping_package_v3_model.metadata
    result = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    
    # Metadata content should be preserved, but it's a copy (signature is recomputed).
    assert result.metadata is not original_metadata
    assert result.metadata.id == original_metadata.id
    assert result.metadata.title == original_metadata.title
    assert result.metadata.project_identifier == original_metadata.project_identifier
    assert result.metadata.mapping_version == original_metadata.mapping_version
    assert result.metadata.model_version == original_metadata.model_version
    assert result.metadata.mapping_suite_hash_digest == MappingPackageV3Hasher(result).hash()


def test_convert_mapping_package_v3_to_v3_lightweight_technical_mapping_unchanged(fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    """Test that technical mapping suite is preserved unchanged."""
    original_technical = fixture_mapping_package_v3_model.technical_mapping_suite
    result = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    
    # Technical mapping suite should be the same object
    assert result.technical_mapping_suite is original_technical
    assert result.technical_mapping_suite.path == original_technical.path
    assert len(result.technical_mapping_suite.files) == len(original_technical.files)


def test_convert_mapping_package_v3_to_v3_lightweight_vocabulary_mapping_unchanged(fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    """Test that vocabulary mapping suite is preserved unchanged."""
    original_vocabulary = fixture_mapping_package_v3_model.vocabulary_mapping_suite
    result = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    
    # Vocabulary mapping suite should be the same object
    assert result.vocabulary_mapping_suite is original_vocabulary
    assert result.vocabulary_mapping_suite.path == original_vocabulary.path
    assert len(result.vocabulary_mapping_suite.files) == len(original_vocabulary.files)

