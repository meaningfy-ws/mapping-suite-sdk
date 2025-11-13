from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.tools.entrypoints.cli.convert import (
    _convert_mapping_package,
    _load_mapping_package_from_folder,
    _serialise_mapping_package,
    mssdk_cli_convert_subcommand
)


def test_convert_cli_command_shows_help(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_convert_subcommand, ["--help"])

    assert result.exit_code == 0
    assert "convert" in result.stdout
    assert "v3" in result.stdout or "v3-lightweight" in result.stdout
    assert "from-package" in result.stdout
    assert "from-folder" in result.stdout


def test_convert_cli_command_invalid_new_version(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_convert_subcommand, ["--to-version", "v2", "--from-version", "v2", "from-package", str(tmp_path)])

    assert result.exit_code != 0


def test_convert_cli_command_valid_version_shows_from_command(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_convert_subcommand, ["--help"])

    assert result.exit_code == 0
    assert "--from-version" in result.stdout
    assert "from-package" in result.stdout
    assert "from-folder" in result.stdout


def test_convert_cli_command_invalid_base_version(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v1", "from-package", str(tmp_path)]
    )

    assert result.exit_code != 0


def test_convert_cli_command_invalid_v3_lightweight_source_version(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    """Test that v3-lightweight conversion requires v3 as source version."""
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3-lightweight", "--from-version", "v2", "from-package", str(tmp_path)]
    )

    assert result.exit_code != 0


def test_convert_cli_command_invalid_target_version(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    """Test that invalid target versions are rejected."""
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v1", "--from-version", "v2", "from-package", str(tmp_path)]
    )

    assert result.exit_code != 0


def test_convert_cli_command_invalid_input_path(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    invalid_path = tmp_path / "nonexistent"
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-package", str(invalid_path)]
    )

    assert result.exit_code != 0


def test_convert_from_folder_invalid_path(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    invalid_path = tmp_path / "nonexistent"
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-folder", str(invalid_path)]
    )

    assert result.exit_code != 0


@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.is_mapping_package_already_converted", return_value=True)
def test_convert_from_package_skips_already_converted(
    mock_is_already_converted,
    typer_cli_runner: CliRunner,
    tmp_path: Path,
    caplog
) -> None:
    """Test that from-package command skips already converted V3 packages."""
    import json
    from datetime import datetime
    
    # Create a V3 package structure
    package_path = tmp_path / "already_v3_package"
    package_path.mkdir()
    metadata_path = package_path / "metadata.json"
    
    # Create valid V3 metadata (with path field required by MappingPackageMetadata base class)
    v3_metadata = {
        "path": "metadata.json",
        "id": "test_package",
        "title": "Test Package",
        "project_identifier": "test:project",
        "created_at": datetime.now().isoformat(),
        "mapping_version": "1.0.0",
        "model_version": "1.0.0",
        "description": "Test description",
        "mapping_suite_hash_digest": "test_hash"
    }
    metadata_path.write_text(json.dumps(v3_metadata, indent=2))
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-package", str(package_path)]
    )
    
    assert result.exit_code == 0
    assert "Package is already v3, skipping conversion" in caplog.text
    mock_is_already_converted.assert_called_once_with(package_path, "v3")


def test_convert_from_package_skips_already_converted_v3_lightweight(
    typer_cli_runner: CliRunner,
    tmp_path: Path,
    caplog
) -> None:
    """Test that from-package command skips already converted V3-lightweight packages."""
    import json
    from datetime import datetime
    
    # Create a V3-lightweight package structure (no conceptual mapping file)
    package_path = tmp_path / "already_v3_lightweight_package"
    package_path.mkdir()
    metadata_path = package_path / "metadata.jsonld"
    
    # Create valid V3 metadata
    v3_metadata = {
        "@context": "http://example.org/context",
        "path": "metadata.jsonld",
        "id": "test_lightweight_package",
        "title": "Test Lightweight Package",
        "project_identifier": "test:project",
        "created_at": datetime.now().isoformat(),
        "mapping_version": "1.0.0",
        "model_version": "1.0.0",
        "description": "Test lightweight description",
        "mapping_suite_hash_digest": "test_hash"
    }
    metadata_path.write_text(json.dumps(v3_metadata, indent=2))
    
    # Create technical and vocabulary directories (lightweight has these)
    (package_path / "transformation" / "mappings").mkdir(parents=True)
    (package_path / "transformation" / "resources").mkdir(parents=True)
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3-lightweight", "--from-version", "v3", "from-package", str(package_path)]
    )
    
    assert result.exit_code == 0
    assert "Package is already v3-lightweight, skipping conversion" in caplog.text


def test_convert_from_folder_handles_nested_package_structure_v3_lightweight(
    typer_cli_runner: CliRunner,
    tmp_path: Path,
    caplog
) -> None:
    """Test that detection works with nested V3-lightweight package structure."""
    import json
    from datetime import datetime
    
    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    
    # Create nested V3-lightweight package structure
    nested_package = folder_path / "nested_lightweight_package"
    nested_package.mkdir()
    inner_package = nested_package / "nested_lightweight_package"
    inner_package.mkdir()
    metadata_path = inner_package / "metadata.jsonld"
    
    v3_metadata = {
        "@context": "http://example.org/context",
        "path": "metadata.jsonld",
        "id": "nested_lightweight_package",
        "title": "Nested Lightweight Package",
        "project_identifier": "test:project",
        "created_at": datetime.now().isoformat(),
        "mapping_version": "1.0.0",
        "model_version": "1.0.0",
        "description": "Nested lightweight package",
        "mapping_suite_hash_digest": "test_hash"
    }
    metadata_path.write_text(json.dumps(v3_metadata, indent=2))
    
    # Create technical and vocabulary directories
    (inner_package / "transformation" / "mappings").mkdir(parents=True)
    (inner_package / "transformation" / "resources").mkdir(parents=True)
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3-lightweight", "--from-version", "v3", "from-folder", str(folder_path)]
    )
    
    assert result.exit_code == 0
    assert "Package is already v3-lightweight, skipping conversion" in caplog.text


@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.is_mapping_package_already_converted", return_value=True)
def test_convert_from_folder_handles_nested_package_structure(
    mock_is_already_converted,
    typer_cli_runner: CliRunner,
    tmp_path: Path,
    caplog
) -> None:
    """Test that detection works with nested package structure (folder_name/folder_name/metadata.json)."""
    import json
    from datetime import datetime
    
    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    
    # Create nested V3 package structure
    nested_package = folder_path / "nested_package"
    nested_package.mkdir()
    inner_package = nested_package / "nested_package"
    inner_package.mkdir()
    metadata_path = inner_package / "metadata.json"
    
    v3_metadata = {
        "path": "metadata.json",
        "id": "nested_package",
        "title": "Nested Package",
        "project_identifier": "test:project",
        "created_at": datetime.now().isoformat(),
        "mapping_version": "1.0.0",
        "model_version": "1.0.0",
        "description": "Nested package",
        "mapping_suite_hash_digest": "test_hash"
    }
    metadata_path.write_text(json.dumps(v3_metadata, indent=2))
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-folder", str(folder_path)]
    )
    
    assert result.exit_code == 0
    assert "Package is already v3, skipping conversion" in caplog.text
    # Should be called for the nested package
    assert mock_is_already_converted.called


def test_load_mapping_package_from_folder_v3(dummy_mapping_package_v3_path: Path) -> None:
    """Test that _load_mapping_package_from_folder works with V3 as from_version."""
    result = _load_mapping_package_from_folder("v3", dummy_mapping_package_v3_path)
    
    assert isinstance(result, MappingPackageV3)
    assert result.metadata is not None
    assert result.conceptual_mapping_asset is not None


def test_load_mapping_package_from_folder_raises_error_for_unsupported_version(tmp_path: Path) -> None:
    """Test that _load_mapping_package_from_folder raises BadParameter for unsupported source version."""
    import typer
    
    with pytest.raises(typer.BadParameter) as excinfo:
        _load_mapping_package_from_folder("v1", tmp_path)
    
    assert "Unsupported source version" in str(excinfo.value)
    assert "v1" in str(excinfo.value)


def test_convert_mapping_package_v3_to_v3_lightweight(
    fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    """Test that _convert_mapping_package works for V3 to V3-lightweight conversion."""
    result = _convert_mapping_package("v3", "v3-lightweight", fixture_mapping_package_v3_model)
    
    from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
    assert isinstance(result, MappingPackageV3Lightweight)
    assert result.metadata == fixture_mapping_package_v3_model.metadata
    assert result.technical_mapping_suite == fixture_mapping_package_v3_model.technical_mapping_suite
    assert result.vocabulary_mapping_suite == fixture_mapping_package_v3_model.vocabulary_mapping_suite


def test_convert_mapping_package_raises_error_for_unsupported_conversion(
    fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    """Test that _convert_mapping_package raises BadParameter for unsupported conversion."""
    import typer
    
    with pytest.raises(typer.BadParameter) as excinfo:
        _convert_mapping_package("v2", "v3-lightweight", fixture_mapping_package_v3_model)
    
    assert "Unsupported conversion" in str(excinfo.value)
    assert "v2" in str(excinfo.value)
    assert "v3-lightweight" in str(excinfo.value)


def test_serialise_mapping_package_v3_lightweight(
    tmp_path: Path,
    fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    """Test that _serialise_mapping_package works for V3-lightweight."""
    from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import convert_mapping_package_v3_to_v3_lightweight
    
    # Convert to lightweight first
    lightweight_package = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    
    # Serialise it
    _serialise_mapping_package("v3-lightweight", tmp_path, lightweight_package)
    
    # Verify files were created
    assert (tmp_path / lightweight_package.metadata.path).exists()
    assert (tmp_path / lightweight_package.technical_mapping_suite.path).exists()
    assert (tmp_path / lightweight_package.vocabulary_mapping_suite.path).exists()


def test_serialise_mapping_package_raises_error_for_unsupported_version(
    tmp_path: Path,
    fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    """Test that _serialise_mapping_package raises BadParameter for unsupported target version."""
    import typer
    
    with pytest.raises(typer.BadParameter) as excinfo:
        _serialise_mapping_package("v2", tmp_path, fixture_mapping_package_v3_model)
    
    assert "Unsupported target version" in str(excinfo.value)
    assert "v2" in str(excinfo.value)


def test_is_already_converted_v3_with_conceptual_mapping(dummy_mapping_package_v3_path: Path) -> None:
    """Test that is_mapping_package_already_converted correctly detects V3 packages with conceptual mapping."""
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import is_mapping_package_already_converted
    
    result = is_mapping_package_already_converted(dummy_mapping_package_v3_path, "v3")
    
    assert result is True


def test_is_already_converted_v3_metadata_without_path_field(
    tmp_path: Path,
    fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    """Test that is_mapping_package_already_converted handles metadata without path field."""
    import json
    from mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser import MappingPackageV3Serialiser
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import is_mapping_package_already_converted
    
    # Serialise a V3 package
    serialiser = MappingPackageV3Serialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model)
    
    # Read metadata and remove path field (simulating serialiser behavior)
    metadata_path = tmp_path / fixture_mapping_package_v3_model.metadata.path
    metadata_dict = json.loads(metadata_path.read_text())
    if 'path' in metadata_dict:
        del metadata_dict['path']
    metadata_path.write_text(json.dumps(metadata_dict, indent=2))
    
    # Check if it's detected as already converted (should add path field automatically)
    result = is_mapping_package_already_converted(tmp_path, "v3")
    
    assert result is True


def test_is_already_converted_v3_lightweight_loads_successfully(
    tmp_path: Path,
    fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    """Test that is_mapping_package_already_converted correctly detects V3-lightweight packages."""
    from mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser_lightweight import MappingPackageV3LightweightSerialiser
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import is_mapping_package_already_converted
    from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import convert_mapping_package_v3_to_v3_lightweight
    
    # Create a lightweight package
    lightweight_package = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    serialiser = MappingPackageV3LightweightSerialiser()
    serialiser.serialise(tmp_path, lightweight_package)
    
    # Check if it's detected as already converted
    result = is_mapping_package_already_converted(tmp_path, "v3-lightweight")
    
    assert result is True


def test_is_already_converted_v3_hard_fails_for_lightweight_package(
    tmp_path: Path,
    fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    """Test that is_mapping_package_already_converted returns False when trying to load lightweight package as V3."""
    from mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser_lightweight import MappingPackageV3LightweightSerialiser
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import is_mapping_package_already_converted
    from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import convert_mapping_package_v3_to_v3_lightweight
    
    # Create a lightweight package (no conceptual mapping)
    lightweight_package = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    serialiser = MappingPackageV3LightweightSerialiser()
    serialiser.serialise(tmp_path, lightweight_package)
    
    # Check if it returns False when trying to load as V3 (lightweight packages don't have conceptual mapping)
    # The version detection will detect it as v3-lightweight, not v3, so it returns False
    result = is_mapping_package_already_converted(tmp_path, "v3")
    
    assert result is False


@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.is_mapping_package_already_converted", return_value=False)
@patch("mapping_suite_sdk.tools.entrypoints.cli.convert._convert_package_from_folder")
def test_convert_from_folder_actually_converts(
    mock_convert,
    mock_is_already_converted,
    typer_cli_runner: CliRunner,
    tmp_path: Path,
    caplog
) -> None:
    """Test that from-folder command actually calls conversion when package is not already converted."""
    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    package_folder = folder_path / "test_package"
    package_folder.mkdir()
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-folder", str(folder_path)]
    )
    
    assert result.exit_code == 0
    assert mock_is_already_converted.called
    assert mock_convert.called
    assert "Converted v2 package to v3 package" in caplog.text


@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.is_mapping_package_already_converted", return_value=False)
@patch("mapping_suite_sdk.tools.entrypoints.cli.convert._convert_package_from_folder")
def test_convert_from_folder_v3_to_v3_lightweight(
    mock_convert,
    mock_is_already_converted,
    typer_cli_runner: CliRunner,
    tmp_path: Path,
    caplog
) -> None:
    """Test that from-folder command works for V3 to V3-lightweight conversion."""
    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    package_folder = folder_path / "test_package"
    package_folder.mkdir()
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3-lightweight", "--from-version", "v3", "from-folder", str(folder_path)]
    )
    
    assert result.exit_code == 0
    assert mock_is_already_converted.called
    assert mock_convert.called
    assert "Converted v3 package to v3-lightweight package" in caplog.text


def test_is_already_converted_v3_lightweight_returns_false_when_conceptual_mapping_exists(
    tmp_path: Path,
    fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    """Test that is_mapping_package_already_converted returns False for lightweight when conceptual mapping exists."""
    from mapping_suite_sdk import mssdk_config
    from mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser import MappingPackageV3Serialiser
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import is_mapping_package_already_converted
    
    # Serialise a full V3 package (with conceptual mapping)
    serialiser = MappingPackageV3Serialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model)
    
    # Check if it's detected as NOT lightweight (should return False since it has conceptual mapping)
    result = is_mapping_package_already_converted(tmp_path, "v3-lightweight")
    
    assert result is False
    # Verify conceptual mapping file exists
    conceptual_mapping_path = tmp_path / mssdk_config.MPV3_CONCEPTUAL_MAPPING_FILE_ASSET_PATH
    assert conceptual_mapping_path.exists()


def test_convert_from_package_raises_error_when_path_is_not_directory(
    typer_cli_runner: CliRunner,
    tmp_path: Path
) -> None:
    """Test that from-package command raises BadParameter when path is not a directory."""
    # Create a file instead of a directory
    file_path = tmp_path / "not_a_directory.txt"
    file_path.write_text("test")
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-package", str(file_path)]
    )
    
    assert result.exit_code != 0
    assert "Package path is not a directory" in result.stdout or "Package path is not a directory" in str(result.exception)


def test_convert_from_folder_raises_error_when_path_is_not_directory(
    typer_cli_runner: CliRunner,
    tmp_path: Path
) -> None:
    """Test that from-folder command raises BadParameter when path is not a directory."""
    # Create a file instead of a directory
    file_path = tmp_path / "not_a_directory.txt"
    file_path.write_text("test")
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-folder", str(file_path)]
    )
    
    assert result.exit_code != 0
    assert "Path is not a directory" in result.stdout or "Path is not a directory" in str(result.exception)


def test_is_already_converted_v3_returns_false_for_invalid_metadata(
    tmp_path: Path
) -> None:
    """Test that is_mapping_package_already_converted returns False when metadata is invalid (ValidationError)."""
    import json
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import is_mapping_package_already_converted
    
    # Create a package with invalid V3 metadata (missing required fields)
    package_path = tmp_path / "invalid_package"
    package_path.mkdir()
    metadata_path = package_path / "metadata.jsonld"
    
    # Create invalid metadata (missing required fields like id, title, etc.)
    invalid_metadata = {
        "path": "metadata.jsonld",
        # Missing required fields: id, title, project_identifier, created_at, etc.
    }
    metadata_path.write_text(json.dumps(invalid_metadata, indent=2))
    
    # Should return False because ValidationError is caught
    result = is_mapping_package_already_converted(package_path, "v3")
    
    assert result is False


@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.generate_jsonld_context")
def test_serialise_mapping_package_v3_generates_context_jsonld(
    mock_generate_context,
    tmp_path: Path,
    fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    """Test that _serialise_mapping_package generates context.jsonld for V3 packages."""
    from mapping_suite_sdk.tools.entrypoints.cli.convert import Version
    
    # Mock the context generation to return a path
    mock_generate_context.return_value = tmp_path / "metadata.jsonld" / "context.jsonld"
    
    # Serialise V3 package using enum value
    _serialise_mapping_package(Version.V3, tmp_path, fixture_mapping_package_v3_model)
    
    # Verify context generation was called
    mock_generate_context.assert_called_once()
    call_kwargs = mock_generate_context.call_args[1]
    assert call_kwargs["context_filename"] == "context.jsonld"
    # Verify it was called with the metadata directory
    metadata_dir = (tmp_path / fixture_mapping_package_v3_model.metadata.path).parent
    assert call_kwargs["output_directory"] == metadata_dir


@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.generate_jsonld_context")
def test_serialise_mapping_package_v3_lightweight_generates_context_jsonld(
    mock_generate_context,
    tmp_path: Path,
    fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    """Test that _serialise_mapping_package generates context.jsonld for V3-lightweight packages."""
    from mapping_suite_sdk.tools.entrypoints.cli.convert import Version
    from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import convert_mapping_package_v3_to_v3_lightweight
    
    # Mock the context generation
    mock_generate_context.return_value = tmp_path / "metadata.jsonld" / "context.jsonld"
    
    # Convert to lightweight and serialise using enum value
    lightweight_package = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    _serialise_mapping_package(Version.V3_LIGHTWEIGHT, tmp_path, lightweight_package)
    
    # Verify context generation was called
    mock_generate_context.assert_called_once()
    call_kwargs = mock_generate_context.call_args[1]
    assert call_kwargs["context_filename"] == "context.jsonld"


@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.generate_jsonld_context")
def test_serialise_mapping_package_v3_continues_on_context_generation_failure(
    mock_generate_context,
    tmp_path: Path,
    fixture_mapping_package_v3_model: MappingPackageV3,
    caplog
) -> None:
    """Test that _serialise_mapping_package continues even if context generation fails."""
    from mapping_suite_sdk.tools.entrypoints.cli.convert import Version
    
    # Mock context generation to raise an error
    mock_generate_context.side_effect = RuntimeError("Failed to generate context")
    
    # Serialise should still succeed (context generation failure is logged but doesn't fail)
    _serialise_mapping_package(Version.V3, tmp_path, fixture_mapping_package_v3_model)
    
    # Verify metadata file was still created
    assert (tmp_path / fixture_mapping_package_v3_model.metadata.path).exists()
    # Verify warning was logged
    assert "Failed to generate context.jsonld" in caplog.text


@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.generate_jsonld_context")
@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.is_mapping_package_already_converted", return_value=False)
@patch("mapping_suite_sdk.tools.entrypoints.cli.convert._load_mapping_package_from_folder")
@patch("mapping_suite_sdk.tools.entrypoints.cli.convert._convert_mapping_package")
def test_convert_from_package_generates_context_jsonld(
    mock_convert,
    mock_load,
    mock_is_already_converted,
    mock_generate_context,
    typer_cli_runner: CliRunner,
    tmp_path: Path,
    dummy_mapping_package_v2_model,
    fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    """Test that from-package command generates context.jsonld during conversion."""
    # Setup mocks to allow real serialization to run
    mock_load.return_value = dummy_mapping_package_v2_model
    mock_convert.return_value = fixture_mapping_package_v3_model
    mock_generate_context.return_value = tmp_path / "context.jsonld"
    
    package_path = tmp_path / "test_package"
    package_path.mkdir()
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-package", str(package_path)]
    )
    
    assert result.exit_code == 0
    # Verify context generation was called during serialisation
    assert mock_generate_context.called


@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.generate_jsonld_context")
@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.is_mapping_package_already_converted", return_value=False)
@patch("mapping_suite_sdk.tools.entrypoints.cli.convert._load_mapping_package_from_folder")
@patch("mapping_suite_sdk.tools.entrypoints.cli.convert._convert_mapping_package")
def test_convert_from_folder_generates_context_jsonld_for_each_package(
    mock_convert,
    mock_load,
    mock_is_already_converted,
    mock_generate_context,
    typer_cli_runner: CliRunner,
    tmp_path: Path,
    dummy_mapping_package_v2_model,
    fixture_mapping_package_v3_model: MappingPackageV3,
    caplog
) -> None:
    """Test that from-folder command generates context.jsonld for each converted package."""
    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    
    # Create two package folders
    package1 = folder_path / "package1"
    package1.mkdir()
    package2 = folder_path / "package2"
    package2.mkdir()
    
    # Setup mocks to allow real serialization to run
    mock_load.return_value = dummy_mapping_package_v2_model
    mock_convert.return_value = fixture_mapping_package_v3_model
    mock_generate_context.return_value = tmp_path / "context.jsonld"
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-folder", str(folder_path)]
    )
    
    assert result.exit_code == 0
    # Verify conversion was called for each package
    assert mock_load.call_count == 2
    assert mock_convert.call_count == 2
    # Context generation is called within the conversion process for each package
    assert mock_generate_context.call_count == 2

