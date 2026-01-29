import json
import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk import mssdk_config
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
        project_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=mssdk_config.mapping_suite_config_file_asset_path,
    )

    assert isinstance(config, MappingSuiteConfig)
    assert isinstance(config.mapping_suite_metadata, MappingSuiteMetadata)
    assert isinstance(config.metadata_config, DocumentMetadataConfig)
    assert isinstance(config.eligibility_constraint_config, EligibilityConstraintConfig)


def test_mapping_suite_config_loader_parses_metadata():
    """Test that config loader correctly parses mapping suite metadata."""
    loader = MappingSuiteConfigLoader()
    config = loader.load(
        project_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=mssdk_config.mapping_suite_config_file_asset_path,
    )

    assert isinstance(config.mapping_suite_metadata, MappingSuiteMetadata)
    assert config.mapping_suite_metadata.mapping_suite_identifier == "eForms"
    assert "eForms" in config.mapping_suite_metadata.mapping_suite_description


def test_mapping_suite_config_loader_parses_metadata_config():
    """Test that config loader correctly parses document metadata configuration."""
    loader = MappingSuiteConfigLoader()
    config = loader.load(
        project_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=mssdk_config.mapping_suite_config_file_asset_path,
    )

    assert isinstance(config.metadata_config, DocumentMetadataConfig)
    assert len(config.metadata_config.metadata_properties) > 0
    assert config.metadata_config.document_type_probing is not None


def test_mapping_suite_config_loader_parses_eligibility_config():
    """Test that config loader correctly parses eligibility constraint configuration."""
    loader = MappingSuiteConfigLoader()
    config = loader.load(
        project_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=mssdk_config.mapping_suite_config_file_asset_path,
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
                project_folder_path=temp_dir_path,
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
                project_folder_path=temp_dir_path,
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
                project_folder_path=temp_dir_path,
                relative_asset_path=Path("invalid_schema.json"),
            )


# ============================================================================
# ResourceReferencesLoader Tests
# ============================================================================


def test_resource_references_loader_loads_successfully():
    """Test that resources loader successfully loads resource files."""
    loader = ResourceReferencesLoader()
    config = MappingSuiteConfigLoader().load(
        project_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=mssdk_config.mapping_suite_config_file_asset_path,
    )
    resources = loader.load(
        package_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        config=config,
    )
    assert resources is not None
    assert isinstance(resources, list)
    assert len(resources) > 0


def test_resource_references_loader_finds_file_paths():
    """Test that resources loader correctly identifies resource file paths."""
    loader = ResourceReferencesLoader()
    config = MappingSuiteConfigLoader().load(
        project_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=mssdk_config.mapping_suite_config_file_asset_path,
    )
    resources = loader.load(
        package_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        config=config,
    )
    assert any("winner-selection-status.json" in r["file_name"] for r in resources)


def test_resource_references_loader_returns_sorted_files():
    """Test that resources loader returns files in sorted order."""
    loader = ResourceReferencesLoader()
    config = MappingSuiteConfigLoader().load(
        project_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        relative_asset_path=mssdk_config.mapping_suite_config_file_asset_path,
    )
    resources = loader.load(
        package_folder_path=TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH,
        config=config,
    )
    file_names = [r["file_name"] for r in resources]
    assert file_names == sorted(file_names)


def test_resource_references_loader_handles_missing_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        loader = ResourceReferencesLoader()
        config = MappingSuiteConfig(
            mapping_suite_metadata=MappingSuiteMetadata(mapping_suite_identifier="dummy", mapping_suite_description="dummy"),
            metadata_config=DocumentMetadataConfig(metadata_properties=[], document_type_probing=None),
            eligibility_constraint_config=EligibilityConstraintConfig(eligibility_mapping=[]),
            resource_references=ResourceReferences(file_paths=[])
        )
        resources = loader.load(
            package_folder_path=temp_dir_path,
            config=config,
        )
        assert resources is None


def test_resource_references_loader_handles_empty_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        resources_dir = temp_dir_path / "resources"
        resources_dir.mkdir()
        loader = ResourceReferencesLoader()
        config = MappingSuiteConfig(
            mapping_suite_metadata=MappingSuiteMetadata(mapping_suite_identifier="dummy", mapping_suite_description="dummy"),
            metadata_config=DocumentMetadataConfig(metadata_properties=[], document_type_probing=None),
            eligibility_constraint_config=EligibilityConstraintConfig(eligibility_mapping=[]),
            resource_references=ResourceReferences(file_paths=[])
        )
        resources = loader.load(
            package_folder_path=temp_dir_path,
            config=config,
        )
        assert resources is None


def test_resource_references_loader_ignores_directories():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        resources_dir = temp_dir_path / "resources"
        resources_dir.mkdir()
        (resources_dir / "file1.json").write_text("{}")
        subdir = resources_dir / "subdir"
        subdir.mkdir()
        loader = ResourceReferencesLoader()
        config = MappingSuiteConfig(
            mapping_suite_metadata=MappingSuiteMetadata(mapping_suite_identifier="dummy", mapping_suite_description="dummy"),
            metadata_config=DocumentMetadataConfig(metadata_properties=[], document_type_probing=None),
            eligibility_constraint_config=EligibilityConstraintConfig(eligibility_mapping=[]),
            resource_references=ResourceReferences(file_paths=["resources/file1.json", "resources/subdir"])
        )
        resources = loader.load(
            package_folder_path=temp_dir_path,
            config=config,
        )

        file_names = [r["file_name"] for r in resources]
        assert "resources/file1.json" in file_names
        assert "resources/subdir" not in file_names


def test_resource_references_loader_handles_malformed_json():
    """Test that loader handles malformed JSON gracefully and continues loading valid files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        resources_dir = temp_dir_path / "resources"
        resources_dir.mkdir()
        
        # Create a malformed JSON file
        (resources_dir / "malformed.json").write_text("{ invalid json content {{")
        # Create a valid JSON file
        (resources_dir / "valid.json").write_text('{"key": "value"}')
        
        loader = ResourceReferencesLoader()
        config = MappingSuiteConfig(
            mapping_suite_metadata=MappingSuiteMetadata(mapping_suite_identifier="dummy", mapping_suite_description="dummy"),
            metadata_config=DocumentMetadataConfig(metadata_properties=[], document_type_probing=None),
            eligibility_constraint_config=EligibilityConstraintConfig(eligibility_mapping=[]),
            resource_references=ResourceReferences(file_paths=["resources/malformed.json", "resources/valid.json"])
        )
        resources = loader.load(
            package_folder_path=temp_dir_path,
            config=config,
        )
        
        # Should only contain the valid file, malformed file should be skipped
        assert resources is not None
        assert len(resources) == 1
        assert resources[0]["file_name"] == "resources/valid.json"
        assert resources[0]["object"] == {"key": "value"}


def test_resource_references_loader_handles_csv_files():
    """Test that loader successfully loads CSV files with various formats.
    
    Note: csv.DictReader is extremely tolerant and rarely raises csv.Error in practice.
    This test verifies that CSV files with inconsistent column counts are handled gracefully.
    While the loader has error handling for csv.Error, such errors are uncommon with DictReader.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        resources_dir = temp_dir_path / "resources"
        resources_dir.mkdir()
        
        # Create a CSV file with inconsistent columns (still valid for DictReader)
        irregular_csv_content = 'col1,col2,col3\nval1,val2\nval3,val4,val5,val6\n'
        (resources_dir / "irregular.csv").write_text(irregular_csv_content)
        
        # Create a standard CSV file
        standard_csv_content = 'name,value\nitem1,100\nitem2,200\n'
        (resources_dir / "standard.csv").write_text(standard_csv_content)
        
        loader = ResourceReferencesLoader()
        config = MappingSuiteConfig(
            mapping_suite_metadata=MappingSuiteMetadata(mapping_suite_identifier="dummy", mapping_suite_description="dummy"),
            metadata_config=DocumentMetadataConfig(metadata_properties=[], document_type_probing=None),
            eligibility_constraint_config=EligibilityConstraintConfig(eligibility_mapping=[]),
            resource_references=ResourceReferences(file_paths=["resources/irregular.csv", "resources/standard.csv"])
        )
        resources = loader.load(
            package_folder_path=temp_dir_path,
            config=config,
        )
        
        # Both files should load successfully - DictReader is tolerant of irregular formats
        assert resources is not None
        assert len(resources) == 2
        assert any("irregular.csv" in r["file_name"] for r in resources)
        assert any("standard.csv" in r["file_name"] for r in resources)


def test_resource_references_loader_handles_encoding_errors():
    """Test that loader handles encoding errors gracefully and continues loading valid files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        resources_dir = temp_dir_path / "resources"
        resources_dir.mkdir()
        
        # Create a file with invalid UTF-8 encoding
        invalid_encoding_file = resources_dir / "invalid_encoding.json"
        # Write bytes that are invalid UTF-8
        invalid_encoding_file.write_bytes(b'{"key": "\xff\xfe invalid utf-8"}')
        
        # Create a valid file
        (resources_dir / "valid.json").write_text('{"key": "value"}')
        
        loader = ResourceReferencesLoader()
        config = MappingSuiteConfig(
            mapping_suite_metadata=MappingSuiteMetadata(mapping_suite_identifier="dummy", mapping_suite_description="dummy"),
            metadata_config=DocumentMetadataConfig(metadata_properties=[], document_type_probing=None),
            eligibility_constraint_config=EligibilityConstraintConfig(eligibility_mapping=[]),
            resource_references=ResourceReferences(file_paths=["resources/invalid_encoding.json", "resources/valid.json"])
        )
        resources = loader.load(
            package_folder_path=temp_dir_path,
            config=config,
        )
        
        # Should only contain the valid file, file with encoding error should be skipped
        assert resources is not None
        assert len(resources) == 1
        assert resources[0]["file_name"] == "resources/valid.json"
        assert resources[0]["object"] == {"key": "value"}


def test_resource_references_loader_handles_all_files_failing():
    """Test that loader returns None when all files fail to parse."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        resources_dir = temp_dir_path / "resources"
        resources_dir.mkdir()
        
        # Create only malformed files
        (resources_dir / "malformed1.json").write_text("{ invalid json")
        (resources_dir / "malformed2.json").write_text("not json at all {{")
        
        loader = ResourceReferencesLoader()
        config = MappingSuiteConfig(
            mapping_suite_metadata=MappingSuiteMetadata(mapping_suite_identifier="dummy", mapping_suite_description="dummy"),
            metadata_config=DocumentMetadataConfig(metadata_properties=[], document_type_probing=None),
            eligibility_constraint_config=EligibilityConstraintConfig(eligibility_mapping=[]),
            resource_references=ResourceReferences(file_paths=["resources/malformed1.json", "resources/malformed2.json"])
        )
        resources = loader.load(
            package_folder_path=temp_dir_path,
            config=config,
        )
        
        # Should return None when all files fail to load
        assert resources is None


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
    assert mapping_suite.resource_file_contents is not None


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

    assert mapping_suite.resource_file_contents is not None
    assert isinstance(mapping_suite.resource_file_contents, list)
    assert len(mapping_suite.resource_file_contents) > 0


def test_mapping_suite_loader_skips_resources_when_disabled():
    """Test that main loader skips resources when include_resources=False."""
    loader = MappingSuiteLoader(include_resources=False)
    mapping_suite = loader.load(TEST_DATA_EXAMPLE_MAPPING_SUITE_FOLDER_PATH)

    assert mapping_suite.resource_file_contents is None


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
    resources_list = mapping_suite.resource_file_contents

    assert isinstance(mapping_suite_dict, dict)
    assert isinstance(config_dict, dict)
    assert isinstance(resources_list, list) or resources_list is None


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
    assert mapping_suite.resource_file_contents is not None
    assert len(mapping_suite.resource_file_contents) > 0
