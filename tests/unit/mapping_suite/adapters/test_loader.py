import json
import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk.mapping_suite.adapters.loader import (
    MappingSuiteLoader,
    MappingSuiteConfigLoader,
    ResourceReferencesLoader,
)
from mapping_suite_sdk.mapping_suite.models.mapping_suite import (
    MappingSuite,
    MappingSuiteConfig,
    ResourceReferences,
    MappingSuiteMetadata,
    DocumentMetadataConfig,
    EligibilityConstraintConfig,
)
from tests import TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH


# ============================================================================
# MappingSuiteConfigLoader Tests
# ============================================================================


def test_mapping_suite_config_loader_loads_successfully():
    """Test that config loader successfully loads a valid config file."""
    loader = MappingSuiteConfigLoader()
    config = loader.load(
        package_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=Path("config/mapping_suite_config.json"),
    )

    assert isinstance(config, MappingSuiteConfig)
    assert isinstance(config.mapping_suite_metadata, MappingSuiteMetadata)
    assert isinstance(config.metadata_config, DocumentMetadataConfig)
    assert isinstance(config.eligibility_constraint_config, EligibilityConstraintConfig)


def test_mapping_suite_config_loader_parses_metadata():
    """Test that config loader correctly parses mapping suite metadata."""
    loader = MappingSuiteConfigLoader()
    config = loader.load(
        package_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=Path("config/mapping_suite_config.json"),
    )

    assert isinstance(config.mapping_suite_metadata, MappingSuiteMetadata)
    assert config.mapping_suite_metadata.mapping_suite_identifier == "eForms"
    assert "eForms" in config.mapping_suite_metadata.mapping_suite_description


def test_mapping_suite_config_loader_parses_metadata_config():
    """Test that config loader correctly parses document metadata configuration."""
    loader = MappingSuiteConfigLoader()
    config = loader.load(
        package_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=Path("mapping_suite_config.json"),
    )

    assert isinstance(config.metadata_config, DocumentMetadataConfig)
    assert len(config.metadata_config.metadata_properties) > 0
    assert config.metadata_config.document_type_probing is not None


def test_mapping_suite_config_loader_parses_eligibility_config():
    """Test that config loader correctly parses eligibility constraint configuration."""
    loader = MappingSuiteConfigLoader()
    config = loader.load(
        package_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=Path("mapping_suite_config.json"),
    )

    assert isinstance(config.eligibility_constraint_config, EligibilityConstraintConfig)
    assert len(config.eligibility_constraint_config.eligibility_mapping) > 0


def test_mapping_suite_config_loader_handles_missing_file():
    """Test that config loader raises FileNotFoundError for missing files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        loader = MappingSuiteConfigLoader()

        with pytest.raises(FileNotFoundError):
            loader.load(
                package_folder_path=temp_dir_path,
                relative_asset_path=Path("non_existing_config.json"),
            )


def test_mapping_suite_config_loader_handles_invalid_json():
    """Test that config loader raises JSONDecodeError for invalid JSON."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        config_path = temp_dir_path / "invalid_config.json"
        config_path.write_text("invalid json content {{{")

        loader = MappingSuiteConfigLoader()

        with pytest.raises(json.JSONDecodeError):
            loader.load(
                package_folder_path=temp_dir_path,
                relative_asset_path=Path("invalid_config.json"),
            )


def test_mapping_suite_config_loader_handles_invalid_schema():
    """Test that config loader raises validation error for invalid schema."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        config_path = temp_dir_path / "invalid_schema.json"

        # Valid JSON but missing required fields
        invalid_config = {
            "mapping_suite_metadata": {
                "mapping_suite_identifier": "test"
            }
            # Missing metadata_config and eligibility_constraint_config
        }
        config_path.write_text(json.dumps(invalid_config))

        loader = MappingSuiteConfigLoader()

        with pytest.raises(Exception):  # Pydantic ValidationError
            loader.load(
                package_folder_path=temp_dir_path,
                relative_asset_path=Path("invalid_schema.json"),
            )


# ============================================================================
# ResourceReferencesLoader Tests
# ============================================================================


def test_resource_references_loader_loads_successfully():
    """Test that resources loader successfully loads resource files."""
    loader = ResourceReferencesLoader()
    resources = loader.load(
        package_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=Path("resources"),
    )

    assert isinstance(resources, ResourceReferences)
    assert resources.file_paths is not None
    assert len(resources.file_paths) > 0


def test_resource_references_loader_finds_file_paths():
    """Test that resources loader correctly identifies resource file paths."""
    loader = ResourceReferencesLoader()
    resources = loader.load(
        package_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=Path("resources"),
    )

    # Check that winner-selection-status.json is found
    assert any("winner-selection-status.json" in f for f in resources.file_paths)


def test_resource_references_loader_returns_sorted_files():
    """Test that resources loader returns files in sorted order."""
    loader = ResourceReferencesLoader()
    resources = loader.load(
        package_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=Path("resources"),
    )

    # Files should be sorted
    assert resources.file_paths == sorted(resources.file_paths)


def test_resource_references_loader_handles_missing_directory():
    """Test that resources loader handles missing resources directory gracefully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        loader = ResourceReferencesLoader()

        resources = loader.load(
            package_folder_path=temp_dir_path,
            relative_asset_path=Path("non_existing_resources"),
        )

        assert isinstance(resources, ResourceReferences)
        assert resources.file_paths is None


def test_resource_references_loader_handles_empty_directory():
    """Test that resources loader handles empty resources directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        resources_dir = temp_dir_path / "resources"
        resources_dir.mkdir()

        loader = ResourceReferencesLoader()
        resources = loader.load(
            package_folder_path=temp_dir_path,
            relative_asset_path=Path("resources"),
        )

        assert isinstance(resources, ResourceReferences)
        assert resources.file_paths is None


def test_resource_references_loader_ignores_directories():
    """Test that resources loader only includes files, not directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        resources_dir = temp_dir_path / "resources"
        resources_dir.mkdir()

        # Create a file and a subdirectory
        (resources_dir / "file1.json").write_text("{}")
        subdir = resources_dir / "subdir"
        subdir.mkdir()
        (subdir / "file2.json").write_text("{}")

        loader = ResourceReferencesLoader()
        resources = loader.load(
            package_folder_path=temp_dir_path,
            relative_asset_path=Path("resources"),
        )

        # Should have 2 files (not 3 with the directory)
        assert len(resources.file_paths) == 2
        assert all(not Path(f).name == "subdir" for f in resources.file_paths)


# ============================================================================
# MappingSuiteLoader Tests
# ============================================================================


def test_mapping_suite_loader_initialization_default_values():
    """Test that loader initializes with correct default values."""
    loader = MappingSuiteLoader()

    assert loader.include_resources is True


def test_mapping_suite_loader_initialization_custom_values():
    """Test that loader initializes with custom values."""
    loader = MappingSuiteLoader(include_resources=False)

    assert loader.include_resources is False


def test_mapping_suite_loader_equality():
    """Test loader equality comparison."""
    loader1 = MappingSuiteLoader(include_resources=True)
    loader2 = MappingSuiteLoader(include_resources=True)
    loader3 = MappingSuiteLoader(include_resources=False)

    assert loader1 == loader2
    assert loader1 != loader3
    assert loader1 != "not a loader"


def test_mapping_suite_loader_loads_successfully():
    """Test that main loader successfully loads a complete mapping suite."""
    loader = MappingSuiteLoader()
    mapping_suite = loader.load(TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH)

    assert isinstance(mapping_suite, MappingSuite)
    assert isinstance(mapping_suite.mapping_suite_config, MappingSuiteConfig)
    assert isinstance(mapping_suite.resource_references, ResourceReferences)


def test_mapping_suite_loader_loads_config_correctly():
    """Test that main loader correctly loads the configuration component."""
    loader = MappingSuiteLoader()
    mapping_suite = loader.load(TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH)

    assert isinstance(mapping_suite.mapping_suite_config, MappingSuiteConfig)
    assert (
        mapping_suite.mapping_suite_config.mapping_suite_metadata.mapping_suite_identifier
        == "eForms"
    )


def test_mapping_suite_loader_loads_resources_when_enabled():
    """Test that main loader loads resources when include_resources=True."""
    loader = MappingSuiteLoader(include_resources=True)
    mapping_suite = loader.load(TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH)

    assert isinstance(mapping_suite.resource_references, ResourceReferences)
    assert mapping_suite.resource_references.file_paths is not None
    assert len(mapping_suite.resource_references.file_paths) > 0


def test_mapping_suite_loader_skips_resources_when_disabled():
    """Test that main loader skips resources when include_resources=False."""
    loader = MappingSuiteLoader(include_resources=False)
    mapping_suite = loader.load(TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH)

    assert isinstance(mapping_suite.resource_references, ResourceReferences)
    assert mapping_suite.resource_references.file_paths is None


def test_mapping_suite_loader_fails_on_wrong_path():
    """Test that main loader raises FileNotFoundError for non-existent paths."""
    loader = MappingSuiteLoader()

    with pytest.raises(FileNotFoundError):
        loader.load(Path("/nonexistent/path"))


def test_mapping_suite_loader_fails_on_missing_config_file():
    """Test that main loader raises FileNotFoundError when config file is missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        loader = MappingSuiteLoader()

        with pytest.raises(FileNotFoundError):
            loader.load(temp_dir_path)


def test_mapping_suite_loader_validates_pydantic_models():
    """Test that loader validates data through Pydantic models."""
    loader = MappingSuiteLoader()
    mapping_suite = loader.load(TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH)

    # Verify all models are properly instantiated Pydantic models by calling model_dump
    mapping_suite_dict = mapping_suite.model_dump()
    config_dict = mapping_suite.mapping_suite_config.model_dump()
    resources_dict = mapping_suite.resource_references.model_dump()

    assert isinstance(mapping_suite_dict, dict)
    assert isinstance(config_dict, dict)
    assert isinstance(resources_dict, dict)


def test_mapping_suite_loader_complete_integration():
    """Integration test: Load complete mapping suite and verify all components."""
    loader = MappingSuiteLoader(include_resources=True)
    mapping_suite = loader.load(TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH)

    # Verify top-level structure
    assert isinstance(mapping_suite, MappingSuite)

    # Verify config components
    config = mapping_suite.mapping_suite_config
    assert config.mapping_suite_metadata.mapping_suite_identifier == "eForms"
    assert len(config.metadata_config.metadata_properties) > 0
    assert len(config.eligibility_constraint_config.eligibility_mapping) > 0

    # Verify document probing
    assert config.metadata_config.document_type_probing is not None
    assert config.metadata_config.document_type_probing.must_exist is not None
    assert config.metadata_config.document_type_probing.must_not_exist is not None

    # Verify resources
    assert mapping_suite.resource_references.file_paths is not None
    assert len(mapping_suite.resource_references.file_paths) > 0