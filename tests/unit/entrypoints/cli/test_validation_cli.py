from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from mapping_suite_sdk.entrypoints.cli.validate import (
    mssdk_cli_validate_subcommand
)


def test_validate_cli_command(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_validate_subcommand, [])

    assert result.exit_code == 0
    assert "validate" in result.stdout


@patch("mapping_suite_sdk.entrypoints.cli.validate.validate_mapping_package_from_archive")
def test_validate_from_archive_command(mock_validate,
                                       typer_cli_runner: CliRunner,
                                       dummy_mapping_package_path: Path) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(mapping_package_archive_path=dummy_mapping_package_path)


@patch("mapping_suite_sdk.entrypoints.cli.validate.validate_bulk_mapping_packages_from_github")
def test_validate_from_github_command(mock_validate,
                                      dummy_invalid_github_repo_url: str,
                                      dummy_get_all_packages_pattern: str,
                                      dummy_github_branch_name: str,
                                      typer_cli_runner: CliRunner) -> None:

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["from-github", dummy_invalid_github_repo_url, dummy_get_all_packages_pattern, "--branch", dummy_github_branch_name]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=dummy_github_branch_name
    )


@patch("mapping_suite_sdk.entrypoints.cli.validate.validate_bulk_mapping_packages_from_github")
def test_validate_from_github_command_without_branch(mock_validate,
                                                     dummy_invalid_github_repo_url: str,
                                                     dummy_get_all_packages_pattern: str,
                                                     typer_cli_runner: CliRunner) -> None:

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["from-github", dummy_invalid_github_repo_url, dummy_get_all_packages_pattern]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=None
    )


@patch("mapping_suite_sdk.entrypoints.cli.validate.validate_bulk_mapping_packages_from_folder")
def test_validate_from_folder_command(mock_validate,
                                      typer_cli_runner: CliRunner,
                                      tmp_path: Path) -> None:

    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["from-folder", str(tmp_path)]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_packages_folder_path=tmp_path,
        update_hash=False
    )


@patch("mapping_suite_sdk.entrypoints.cli.validate.validate_bulk_mapping_packages_from_folder")
def test_validate_from_folder_command_with_update_hash(mock_validate,
                                                       typer_cli_runner: CliRunner,
                                                       tmp_path: Path) -> None:

    mock_validate.return_value = False

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["from-folder", str(tmp_path), "--update-hash"]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_packages_folder_path=tmp_path,
        update_hash=True
    )


@patch("mapping_suite_sdk.entrypoints.cli.validate.validate_bulk_mapping_packages_from_folder")
def test_validate_from_folder_success_output(mock_validate,
                                             typer_cli_runner: CliRunner,
                                             tmp_path: Path,
                                             caplog) -> None:

    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["from-folder", str(tmp_path)]
    )

    assert result.exit_code == 0

    assert "✅ All packages are valid!" in caplog.text


@patch("mapping_suite_sdk.entrypoints.cli.validate.validate_bulk_mapping_packages_from_folder")
def test_validate_from_folder_failure_output(mock_validate,
                                             typer_cli_runner: CliRunner,
                                             tmp_path: Path,
                                             caplog) -> None:
    folder_path = tmp_path / "mappings"
    folder_path.mkdir()

    mock_validate.return_value = False

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["from-folder", str(folder_path)]
    )

    assert result.exit_code == 0

    assert "❌ There are invalid packages!" in caplog.text
