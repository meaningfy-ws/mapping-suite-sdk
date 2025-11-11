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


def test_convert_from_folder_invalid_path(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    invalid_path = tmp_path / "nonexistent"
    result = typer_cli_runner.invoke(
        mssdk_cli_convert_subcommand,
        ["--to-version", "v3", "--from-version", "v2", "from-folder", str(invalid_path)]
    )

    assert result.exit_code != 0


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

