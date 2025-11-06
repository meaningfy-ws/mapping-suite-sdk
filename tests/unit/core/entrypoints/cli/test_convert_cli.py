from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from mapping_suite_sdk.core.entrypoints.cli.convert import mssdk_cli_convert_subcommand


def test_convert_cli_command_shows_help(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_convert_subcommand, ["--help"])

    assert result.exit_code == 0
    assert "convert" in result.stdout
    assert "Target mapping package version (v3)" in result.stdout
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


def test_convert_cli_command_invalid_input_path(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    invalid_path = tmp_path / "nonexistent"
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-package", str(invalid_path)]
    )

    assert result.exit_code != 0


@patch("mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser.MappingPackageV3Serialiser")
@patch("mapping_suite_sdk.core.entrypoints.cli.convert.convert_mpv3_from_mpv2")
@patch("mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2.load_mapping_package_v2_from_folder")
def test_create_from_command_success(mock_load,
                                     mock_create,
                                     mock_serialiser,
                                     typer_cli_runner: CliRunner,
                                     dummy_mapping_package_v2_path: Path,
                                     dummy_mapping_package_v2_model,
                                     tmp_path: Path) -> None:
    mock_mpv3 = MagicMock()
    mock_load.return_value = dummy_mapping_package_v2_model
    mock_create.return_value = mock_mpv3

    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-package", str(dummy_mapping_package_v2_path)]
    )

    assert result.exit_code == 0
    mock_load.assert_called_once()
    # Check that the path is passed as keyword argument
    assert mock_load.call_args[1]['mapping_package_folder_path'] == dummy_mapping_package_v2_path
    mock_create.assert_called_once_with(dummy_mapping_package_v2_model)
    mock_serialiser.return_value.serialise.assert_called_once_with(dummy_mapping_package_v2_path, mock_mpv3)


@patch("mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser.MappingPackageV3Serialiser")
@patch("mapping_suite_sdk.core.entrypoints.cli.convert.convert_mpv3_from_mpv2")
@patch("mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2.load_mapping_package_v2_from_folder")
def test_create_from_command_converts_in_place(mock_load,
                                               mock_create,
                                               mock_serialiser,
                                               typer_cli_runner: CliRunner,
                                               dummy_mapping_package_v2_path: Path,
                                               dummy_mapping_package_v2_model,
                                               tmp_path: Path,
                                               caplog) -> None:
    mock_mpv3 = MagicMock()
    mock_load.return_value = dummy_mapping_package_v2_model
    mock_create.return_value = mock_mpv3

    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-package", str(dummy_mapping_package_v2_path)]
    )

    assert result.exit_code == 0
    assert "✅ Converted v2 package to v3 package" in caplog.text


def test_create_verbose_option(typer_cli_runner: CliRunner,
                               dummy_mapping_package_v2_path: Path,
                               tmp_path: Path) -> None:
    with patch("mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser.MappingPackageV3Serialiser"), \
         patch("mapping_suite_sdk.core.entrypoints.cli.convert.convert_mpv3_from_mpv2"), \
         patch("mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2.load_mapping_package_v2_from_folder"):
        result = typer_cli_runner.invoke(
            mssdk_cli_convert_subcommand,
            ["--to-version", "v3", "--from-version", "v2", "--verbose", "from-package", str(dummy_mapping_package_v2_path)]
        )

        assert result.exit_code == 0


@patch("mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser.MappingPackageV3Serialiser")
@patch("mapping_suite_sdk.core.entrypoints.cli.convert.convert_mpv3_from_mpv2")
@patch("mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2.load_mapping_package_v2_from_folder")
def test_convert_from_folder_success(mock_load,
                                     mock_create,
                                     mock_serialiser,
                                     typer_cli_runner: CliRunner,
                                     dummy_mapping_package_v2_model,
                                     tmp_path: Path,
                                     caplog) -> None:
    mock_mpv3 = MagicMock()
    mock_load.return_value = dummy_mapping_package_v2_model
    mock_create.return_value = mock_mpv3

    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    package1 = folder_path / "package1"
    package2 = folder_path / "package2"
    package1.mkdir()
    package2.mkdir()

    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-folder", str(folder_path)]
    )

    assert result.exit_code == 0
    assert mock_load.call_count == 2
    assert mock_create.call_count == 2
    assert mock_serialiser.return_value.serialise.call_count == 2
    assert "✅ All converted" in caplog.text
    assert "(2 converted, 0 failed)" in caplog.text


@patch("mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser.MappingPackageV3Serialiser")
@patch("mapping_suite_sdk.core.entrypoints.cli.convert.convert_mpv3_from_mpv2")
@patch("mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2.load_mapping_package_v2_from_folder")
def test_convert_from_folder_with_failures(mock_load,
                                           mock_create,
                                           mock_serialiser,
                                           typer_cli_runner: CliRunner,
                                           dummy_mapping_package_v2_model,
                                           tmp_path: Path,
                                           caplog) -> None:
    mock_mpv3 = MagicMock()
    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    package1 = folder_path / "package1"
    package2 = folder_path / "package2"
    package1.mkdir()
    package2.mkdir()
    
    def load_side_effect(mapping_package_folder_path, **kwargs):
        if mapping_package_folder_path == package1:
            return dummy_mapping_package_v2_model
        else:
            raise ValueError("Failed to load package")

    mock_load.side_effect = load_side_effect
    mock_create.return_value = mock_mpv3

    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-folder", str(folder_path)]
    )

    assert result.exit_code == 1
    assert "❌ Some packages failed to convert" in caplog.text
    assert "(1 converted, 1 failed)" in caplog.text
    assert mock_serialiser.return_value.serialise.call_count == 1
    mock_serialiser.return_value.serialise.assert_called_once_with(package1, mock_mpv3)


def test_convert_from_folder_invalid_path(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    invalid_path = tmp_path / "nonexistent"
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-folder", str(invalid_path)]
    )

    assert result.exit_code != 0


def test_convert_from_folder_skips_files(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    package_dir = folder_path / "package1"
    package_dir.mkdir()
    file_path = folder_path / "file.txt"
    file_path.write_text("not a package")

    with patch("mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser.MappingPackageV3Serialiser"), \
         patch("mapping_suite_sdk.core.entrypoints.cli.convert.convert_mpv3_from_mpv2"), \
         patch("mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2.load_mapping_package_v2_from_folder"):
        result = typer_cli_runner.invoke(
            mssdk_cli_convert_subcommand,
            ["--to-version", "v3", "--from-version", "v2", "from-folder", str(folder_path)]
        )

        assert result.exit_code == 0


def test_convert_from_package_skips_already_converted(
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


def test_convert_from_folder_skips_already_converted(
    typer_cli_runner: CliRunner,
    tmp_path: Path,
    caplog
) -> None:
    """Test that from-folder command skips already converted V3 packages."""
    import json
    from datetime import datetime
    
    folder_path = tmp_path / "packages"
    folder_path.mkdir()
    
    # Create one V2 package (should convert)
    v2_package = folder_path / "v2_package"
    v2_package.mkdir()
    v2_metadata_path = v2_package / "metadata.json"
    v2_metadata = {
        "identifier": "v2_package",
        "title": "V2 Package",
        "created_at": "2024-01-01T00:00:00",
        "mapping_version": "1.0.0",
        "ontology_version": "1.0.0",
        "description": "V2 package",
        "type": "test",
        "metadata_constraints": {"constraints": {}},
        "mapping_suite_hash_digest": "test_hash"
    }
    v2_metadata_path.write_text(json.dumps(v2_metadata, indent=2))
    
    # Create one V3 package (should skip)
    v3_package = folder_path / "v3_package"
    v3_package.mkdir()
    v3_metadata_path = v3_package / "metadata.json"
    v3_metadata = {
        "path": "metadata.json",
        "id": "v3_package",
        "title": "V3 Package",
        "project_identifier": "test:project",
        "created_at": datetime.now().isoformat(),
        "mapping_version": "1.0.0",
        "model_version": "1.0.0",
        "description": "V3 package",
        "mapping_suite_hash_digest": "test_hash"
    }
    v3_metadata_path.write_text(json.dumps(v3_metadata, indent=2))
    
    with patch("mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser.MappingPackageV3Serialiser"), \
         patch("mapping_suite_sdk.core.entrypoints.cli.convert.convert_mpv3_from_mpv2") as mock_convert, \
         patch("mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2.load_mapping_package_v2_from_folder") as mock_load:
        from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
        mock_mpv2 = MagicMock(spec=MappingPackageV2)
        mock_load.return_value = mock_mpv2
        
        result = typer_cli_runner.invoke(
            mssdk_cli_convert_subcommand,
            ["--to-version", "v3", "--from-version", "v2", "from-folder", str(folder_path)]
        )
    
    assert result.exit_code == 0
    assert "Package is already v3, skipping conversion" in caplog.text
    # Should only convert the V2 package, not the V3 one
    assert mock_load.call_count == 1
    assert mock_convert.call_count == 1


def test_convert_from_folder_handles_nested_package_structure(
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

