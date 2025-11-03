from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from mapping_suite_sdk.core.entrypoints.cli.create import mssdk_cli_create_subcommand
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader


def test_create_cli_command_shows_help(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_create_subcommand, ["--help"])

    assert result.exit_code == 0
    assert "create" in result.stdout
    assert "New mapping package version (v3)" in result.stdout


def test_create_cli_command_invalid_new_version(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_create_subcommand, ["--version", "v2"])

    assert result.exit_code != 0


def test_create_cli_command_valid_version_shows_from_command(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_create_subcommand, ["--version", "v3", "--help"])

    assert result.exit_code == 0
    assert "from" in result.stdout


def test_create_cli_command_invalid_base_version(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_create_subcommand,
        ["--version", "v3", "from", "--version", "v1", "--input", str(tmp_path), "--output", str(tmp_path / "out")]
    )

    assert result.exit_code != 0


def test_create_cli_command_invalid_input_path(typer_cli_runner: CliRunner, tmp_path: Path) -> None:
    invalid_path = tmp_path / "nonexistent"
    result = typer_cli_runner.invoke(
        mssdk_cli_create_subcommand,
        ["--version", "v3", "from", "--version", "v2", "--input", str(invalid_path), "--output", str(tmp_path / "out")]
    )

    assert result.exit_code != 0


@patch("mapping_suite_sdk.core.entrypoints.cli.create.create_mpv3_from_mpv2")
@patch("mapping_suite_sdk.core.entrypoints.cli.create.load_mapping_package_v2_from_folder")
@patch("mapping_suite_sdk.core.entrypoints.cli.create.MappingPackageV3Serialiser")
def test_create_from_command_success(mock_serialiser,
                                     mock_load,
                                     mock_create,
                                     typer_cli_runner: CliRunner,
                                     dummy_mapping_package_v2_path: Path,
                                     tmp_path: Path) -> None:
    mock_mpv2 = MagicMock()
    mock_mpv3 = MagicMock()

    mock_load.return_value = mock_mpv2
    mock_create.return_value = mock_mpv3

    output_path = tmp_path / "output"
    result = typer_cli_runner.invoke(
        mssdk_cli_create_subcommand,
        ["--version", "v3", "from", "--version", "v2", "--input", str(dummy_mapping_package_v2_path), "--output", str(output_path)]
    )

    assert result.exit_code == 0
    mock_load.assert_called_once_with(
        mapping_package_folder_path=dummy_mapping_package_v2_path,
        mapping_package_loader=MappingPackageV2Loader()
    )
    mock_create.assert_called_once_with(mock_mpv2)
    mock_serialiser.return_value.serialise.assert_called_once_with(output_path, mock_mpv3)


@patch("mapping_suite_sdk.core.entrypoints.cli.create.create_mpv3_from_mpv2")
@patch("mapping_suite_sdk.core.entrypoints.cli.create.load_mapping_package_v2_from_folder")
@patch("mapping_suite_sdk.core.entrypoints.cli.create.MappingPackageV3Serialiser")
def test_create_from_command_creates_output_directory(mock_serialiser,
                                                       mock_load,
                                                       mock_create,
                                                       typer_cli_runner: CliRunner,
                                                       dummy_mapping_package_v2_path: Path,
                                                       tmp_path: Path,
                                                       caplog) -> None:
    mock_mpv2 = MagicMock()
    mock_mpv3 = MagicMock()

    mock_load.return_value = mock_mpv2
    mock_create.return_value = mock_mpv3

    output_path = tmp_path / "new" / "output" / "directory"
    result = typer_cli_runner.invoke(
        mssdk_cli_create_subcommand,
        ["--version", "v3", "from", "--version", "v2", "--input", str(dummy_mapping_package_v2_path), "--output", str(output_path)]
    )

    assert result.exit_code == 0
    assert output_path.exists()
    assert "✅ Created v3 package" in caplog.text


def test_create_verbose_option(typer_cli_runner: CliRunner,
                               dummy_mapping_package_v2_path: Path,
                               tmp_path: Path) -> None:
    with patch("mapping_suite_sdk.core.entrypoints.cli.create.create_mpv3_from_mpv2"), \
         patch("mapping_suite_sdk.core.entrypoints.cli.create.load_mapping_package_v2_from_folder"), \
         patch("mapping_suite_sdk.core.entrypoints.cli.create.MappingPackageV3Serialiser"):
        result = typer_cli_runner.invoke(
            mssdk_cli_create_subcommand,
            ["--version", "v3", "from", "--version", "v2", "--input", str(dummy_mapping_package_v2_path), "--output", str(tmp_path), "--verbose"]
        )

        assert result.exit_code == 0

