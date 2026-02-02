from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.tools.entrypoints.cli.convert import mssdk_cli_convert_subcommand


def test_convert_cli_command_shows_help(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_convert_subcommand, ["--help"])

    assert result.exit_code == 0
    assert "convert" in result.stdout
    assert "v3" in result.stdout or "v3L" in result.stdout
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


def test_convert_cli_command_v2_to_v3l_source_version_accepted(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    """Test that v3L conversion accepts v2 as source version."""
    with (
        patch("mapping_suite_sdk.tools.entrypoints.cli.convert.is_mapping_package_already_converted", return_value=False),
        patch("mapping_suite_sdk.tools.entrypoints.cli.convert.convert_mapping_package_from_folder") as mock_convert,
    ):
        result = typer_cli_runner.invoke(
            mssdk_cli_convert_subcommand,
            ["--to-version", "v3L", "--from-version", "v2", "from-package", str(tmp_path)]
        )

        assert result.exit_code == 0
        mock_convert.assert_called_once_with("v2", "v3L", tmp_path)


def test_convert_cli_command_invalid_target_version(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    """Test that invalid target versions are rejected."""
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v1", "--from-version", "v2", "from-package", str(tmp_path)]
    )

    assert result.exit_code != 0


def test_convert_cli_command_v3l_invalid_source_version(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    """Test that v3L conversion rejects invalid source versions."""
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3L", "--from-version", "v1", "from-package", str(tmp_path)]
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
    """Test that from-package command skips already converted V3L packages."""
    import json
    from datetime import datetime
    
    # Create a V3L package structure (no conceptual mapping file)
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
    
    # Test converting from v3 to v3L (should skip since already v3L)
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3L", "--from-version", "v3", "from-package", str(package_path)]
    )
    
    assert result.exit_code == 0
    assert "Package is already v3L, skipping conversion" in caplog.text


def test_convert_from_folder_handles_nested_package_structure_v3_lightweight(
    typer_cli_runner: CliRunner,
    tmp_path: Path,
    caplog
) -> None:
    """Test that detection works with nested V3L package structure."""
    import json
    from datetime import datetime
    
    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    
    # Create nested V3L package structure
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
    
    # Test converting from v3 to v3L (should skip since already v3L)
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3L", "--from-version", "v3", "from-folder", str(folder_path)]
    )
    
    assert result.exit_code == 0
    assert "Package is already v3L, skipping conversion" in caplog.text


@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.convert_mapping_packages_from_folder")
def test_convert_from_folder_handles_nested_package_structure(
    mock_convert_service,
    typer_cli_runner: CliRunner,
    tmp_path: Path,
    caplog
) -> None:
    """Test that CLI correctly calls service for nested package structure."""
    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    
    # Create nested package structure
    nested_package = folder_path / "nested_package"
    nested_package.mkdir()
    inner_package = nested_package / "nested_package"
    inner_package.mkdir()
    
    # Mock service to return success (service handles nested structure detection)
    mock_convert_service.return_value = {'converted': 0, 'skipped': 1, 'total': 1}
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-folder", str(folder_path)]
    )
    
    assert result.exit_code == 0
    # Service should be called with folder path (service handles nested detection)
    mock_convert_service.assert_called_once_with("v2", "v3", folder_path)


# Note: Tests for load_mapping_package_from_folder, convert_mapping_package_model, 
# and serialise_mapping_package are now in test_convert_mapping_package.py (service tests)
# CLI tests focus on CLI-specific behavior: argument parsing, error handling, service integration


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
    from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser import MappingPackageV3Serialiser
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
    """Test that is_mapping_package_already_converted correctly detects V3L packages."""
    from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_serialiser import MappingPackageV3LightweightSerialiser
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import is_mapping_package_already_converted
    from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import convert_mapping_package_v3_to_v3_lightweight
    
    # Create a lightweight package
    lightweight_package = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    serialiser = MappingPackageV3LightweightSerialiser()
    serialiser.serialise(tmp_path, lightweight_package)
    
    # Check if it's detected as already converted
    # V3L packages should NOT match V3_FULL_SPEC (which requires conceptual_mappings.xlsx)
    result = is_mapping_package_already_converted(tmp_path, "v3")
    
    assert result is False


def test_is_already_converted_v3_hard_fails_for_lightweight_package(
    tmp_path: Path,
    fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    """Test that is_mapping_package_already_converted returns False when trying to load lightweight package as V3."""
    from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_serialiser import MappingPackageV3LightweightSerialiser
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import is_mapping_package_already_converted
    from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import convert_mapping_package_v3_to_v3_lightweight
    
    # Create a lightweight package (no conceptual mapping)
    lightweight_package = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    serialiser = MappingPackageV3LightweightSerialiser()
    serialiser.serialise(tmp_path, lightweight_package)
    
    # Check if it returns False when trying to load as V3
    # V3L packages should NOT match V3_FULL_SPEC (which requires conceptual_mappings.xlsx)
    result = is_mapping_package_already_converted(tmp_path, "v3")
    
    assert result is False


@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.is_mapping_package_already_converted", return_value=False)
@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.convert_mapping_packages_from_folder")
def test_convert_from_folder_actually_converts(
    mock_convert_service,
    mock_is_already_converted,
    typer_cli_runner: CliRunner,
    tmp_path: Path,
    caplog
) -> None:
    """Test that from-folder command calls service when package is not already converted."""
    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    package_folder = folder_path / "test_package"
    package_folder.mkdir()
    
    mock_convert_service.return_value = {'converted': 1, 'skipped': 0, 'total': 1}
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-folder", str(folder_path)]
    )
    
    assert result.exit_code == 0
    mock_convert_service.assert_called_once_with("v2", "v3", folder_path)
    assert "Conversion complete" in caplog.text


@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.convert_mapping_packages_from_folder")
def test_convert_from_folder_v3_to_v3_lightweight(
    mock_convert_service,
    typer_cli_runner: CliRunner,
    tmp_path: Path,
    caplog
) -> None:
    """Test that from-folder command works for V3 to V3L conversion."""
    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    package_folder = folder_path / "test_package"
    package_folder.mkdir()
    
    mock_convert_service.return_value = {'converted': 1, 'skipped': 0, 'total': 1}
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3L", "--from-version", "v3", "from-folder", str(folder_path)]
    )
    
    assert result.exit_code == 0
    mock_convert_service.assert_called_once_with("v3", "v3L", folder_path)
    assert "Conversion complete" in caplog.text


def test_is_already_converted_v3_lightweight_returns_false_when_conceptual_mapping_exists(
    tmp_path: Path,
    fixture_mapping_package_v3_model: MappingPackageV3
) -> None:
    """Test that is_mapping_package_already_converted returns False for lightweight when conceptual mapping exists."""
    from mapping_suite_sdk import mssdk_config
    from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser import MappingPackageV3Serialiser
    from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import is_mapping_package_already_converted
    
    # Serialise a full V3 package (with conceptual mapping)
    serialiser = MappingPackageV3Serialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model)
    
    # Check if it's detected as NOT lightweight (should return False since it has conceptual mapping)
    result = is_mapping_package_already_converted(tmp_path, "v3L")
    
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
    
    # Invalid metadata without @context should not match V3_FULL_SPEC
    result = is_mapping_package_already_converted(package_path, "v3")
    
    assert result is False




@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.is_mapping_package_already_converted", return_value=False)
@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.convert_mapping_package_from_folder")
def test_convert_from_package_calls_service(
    mock_convert_service,
    mock_is_already_converted,
    typer_cli_runner: CliRunner,
    tmp_path: Path
) -> None:
    """Test that from-package command calls the service."""
    package_path = tmp_path / "test_package"
    package_path.mkdir()
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-package", str(package_path)]
    )
    
    assert result.exit_code == 0
    mock_convert_service.assert_called_once_with("v2", "v3", package_path)


@patch("mapping_suite_sdk.tools.entrypoints.cli.convert.convert_mapping_packages_from_folder")
def test_convert_from_folder_calls_service_with_correct_params(
    mock_convert_service,
    typer_cli_runner: CliRunner,
    tmp_path: Path
) -> None:
    """Test that from-folder command calls the service with correct parameters."""
    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    
    # Create two package folders
    package1 = folder_path / "package1"
    package1.mkdir()
    package2 = folder_path / "package2"
    package2.mkdir()
    
    mock_convert_service.return_value = {'converted': 2, 'skipped': 0, 'total': 2}
    
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-folder", str(folder_path)]
    )
    
    assert result.exit_code == 0
    mock_convert_service.assert_called_once_with("v2", "v3", folder_path)


# Note: Tests for serialization behavior (removing old files, etc.) are now in 
# test_convert_mapping_package.py (service tests) since that logic moved to the service layer

