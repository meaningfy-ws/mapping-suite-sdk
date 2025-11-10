from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from mapping_suite_sdk.core.entrypoints.cli.validate import mssdk_cli_validate_subcommand
from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_loader import MappingPackageV1Loader
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader
from mapping_suite_sdk.mapping_package_v3.adapters.package_loader import MappingPackageV3Loader
from mapping_suite_sdk.mapping_package_v3.adapters.package_loader_lightweight import MappingPackageV3LightweightLoader


def test_validate_cli_command_shows_help(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_validate_subcommand, ["--help"])

    assert result.exit_code == 0
    assert "validate" in result.stdout
    assert "Package version" in result.stdout


def test_validate_cli_command_invalid_version(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_validate_subcommand, ["--version", "v3"])

    assert result.exit_code != 0


def test_validate_cli_command_valid_version_v1(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_validate_subcommand, ["--version", "v1", "--help"])

    assert result.exit_code == 0
    assert "from-archive" in result.stdout
    assert "from-github" in result.stdout
    assert "from-folder" in result.stdout


def test_validate_cli_command_valid_version_v2(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_validate_subcommand, ["--version", "v2", "--help"])

    assert result.exit_code == 0
    assert "from-archive" in result.stdout
    assert "from-github" in result.stdout
    assert "from-folder" in result.stdout


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v1_from_archive")
def test_validate_from_archive_command_v1(mock_validate,
                                          typer_cli_runner: CliRunner,
                                          dummy_mapping_package_path: Path) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_package_archive_path=dummy_mapping_package_path,
        mapping_package_loader=MappingPackageV1Loader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v2_from_archive")
def test_validate_from_archive_command_v2(mock_validate,
                                          typer_cli_runner: CliRunner,
                                          dummy_mapping_package_path: Path) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v2", "from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_package_archive_path=dummy_mapping_package_path,
        mapping_package_loader=MappingPackageV2Loader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v1_from_archive")
def test_validate_from_archive_command_v1_with_options(mock_validate,
                                                       typer_cli_runner: CliRunner,
                                                       dummy_mapping_package_path: Path) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-archive", str(dummy_mapping_package_path),
         "--include-test-data", "--include-output"]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_package_archive_path=dummy_mapping_package_path,
        mapping_package_loader=MappingPackageV1Loader(include_test_data=True, include_output=True)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v2_from_archive")
def test_validate_from_archive_command_v2_with_options(mock_validate,
                                                       typer_cli_runner: CliRunner,
                                                       dummy_mapping_package_path: Path) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v2", "from-archive", str(dummy_mapping_package_path),
         "--include-test-data", "--include-output"]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_package_archive_path=dummy_mapping_package_path,
        mapping_package_loader=MappingPackageV2Loader(include_test_data=True, include_output=True)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v1_from_github")
def test_validate_from_github_command_v1(mock_validate,
                                         dummy_invalid_github_repo_url: str,
                                         dummy_get_all_packages_pattern: str,
                                         dummy_github_branch_name: str,
                                         typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-github", dummy_invalid_github_repo_url,
         dummy_get_all_packages_pattern, "--branch", dummy_github_branch_name]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=dummy_github_branch_name,
        mapping_package_loader=MappingPackageV1Loader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v2_from_github")
def test_validate_from_github_command_v2(mock_validate,
                                         dummy_invalid_github_repo_url: str,
                                         dummy_get_all_packages_pattern: str,
                                         dummy_github_branch_name: str,
                                         typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v2", "from-github", dummy_invalid_github_repo_url,
         dummy_get_all_packages_pattern, "--branch", dummy_github_branch_name]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=dummy_github_branch_name,
        mapping_package_loader=MappingPackageV2Loader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v1_from_github")
def test_validate_from_github_command_v1_with_options(mock_validate,
                                                      dummy_invalid_github_repo_url: str,
                                                      dummy_get_all_packages_pattern: str,
                                                      dummy_github_branch_name: str,
                                                      typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-github", dummy_invalid_github_repo_url,
         dummy_get_all_packages_pattern, "--branch", dummy_github_branch_name,
         "--include-test-data", "--include-output"]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=dummy_github_branch_name,
        mapping_package_loader=MappingPackageV1Loader(include_test_data=True, include_output=True)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v2_from_github")
def test_validate_from_github_command_v2_with_options(mock_validate,
                                                      dummy_invalid_github_repo_url: str,
                                                      dummy_get_all_packages_pattern: str,
                                                      dummy_github_branch_name: str,
                                                      typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v2", "from-github", dummy_invalid_github_repo_url,
         dummy_get_all_packages_pattern, "--branch", dummy_github_branch_name,
         "--include-test-data", "--include-output"]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=dummy_github_branch_name,
        mapping_package_loader=MappingPackageV2Loader(include_test_data=True, include_output=True)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v1_from_github")
def test_validate_from_github_command_v1_without_branch(mock_validate,
                                                        dummy_invalid_github_repo_url: str,
                                                        dummy_get_all_packages_pattern: str,
                                                        typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-github", dummy_invalid_github_repo_url,
         dummy_get_all_packages_pattern]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=None,
        mapping_package_loader=MappingPackageV1Loader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v2_from_github")
def test_validate_from_github_command_v2_without_branch(mock_validate,
                                                        dummy_invalid_github_repo_url: str,
                                                        dummy_get_all_packages_pattern: str,
                                                        typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v2", "from-github", dummy_invalid_github_repo_url,
         dummy_get_all_packages_pattern]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=None,
        mapping_package_loader=MappingPackageV2Loader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v1_from_folder")
def test_validate_from_folder_command_v1(mock_validate,
                                         typer_cli_runner: CliRunner,
                                         tmp_path: Path) -> None:
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-folder", str(tmp_path)]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_packages_folder_path=tmp_path,
        update_hash=False,
        mapping_package_loader=MappingPackageV1Loader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v2_from_folder")
def test_validate_from_folder_command_v2(mock_validate,
                                         typer_cli_runner: CliRunner,
                                         tmp_path: Path) -> None:
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v2", "from-folder", str(tmp_path)]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_packages_folder_path=tmp_path,
        update_hash=False,
        mapping_package_loader=MappingPackageV2Loader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v1_from_folder")
def test_validate_from_folder_command_v1_with_options(mock_validate,
                                                      typer_cli_runner: CliRunner,
                                                      tmp_path: Path) -> None:
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-folder", str(tmp_path),
         "--include-test-data", "--include-output", "--update-hash"]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_packages_folder_path=tmp_path,
        update_hash=True,
        mapping_package_loader=MappingPackageV1Loader(include_test_data=True, include_output=True)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v2_from_folder")
def test_validate_from_folder_command_v2_with_options(mock_validate,
                                                      typer_cli_runner: CliRunner,
                                                      tmp_path: Path) -> None:
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v2", "from-folder", str(tmp_path),
         "--include-test-data", "--include-output", "--update-hash"]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_packages_folder_path=tmp_path,
        update_hash=True,
        mapping_package_loader=MappingPackageV2Loader(include_test_data=True, include_output=True)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v1_from_folder")
def test_validate_from_folder_v1_success_output(mock_validate,
                                                typer_cli_runner: CliRunner,
                                                tmp_path: Path,
                                                caplog) -> None:
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-folder", str(tmp_path)]
    )

    assert result.exit_code == 0, "Unexpected exit code"
    assert "✅ All valid v1 packages" in caplog.text


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v2_from_folder")
def test_validate_from_folder_v2_success_output(mock_validate,
                                                typer_cli_runner: CliRunner,
                                                tmp_path: Path,
                                                caplog) -> None:
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v2", "from-folder", str(tmp_path)]
    )

    assert result.exit_code == 0
    assert "✅ All valid v2 packages" in caplog.text


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v1_from_folder")
def test_validate_from_folder_v1_failure_output(mock_validate,
                                                typer_cli_runner: CliRunner,
                                                tmp_path: Path,
                                                caplog) -> None:
    folder_path = tmp_path / "mappings"
    folder_path.mkdir()

    mock_validate.return_value = False

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-folder", str(folder_path)]
    )

    assert result.exit_code == 1
    assert "❌ Invalid packages found v1 packages" in caplog.text


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v2_from_folder")
def test_validate_from_folder_v2_failure_output(mock_validate,
                                                typer_cli_runner: CliRunner,
                                                tmp_path: Path,
                                                caplog) -> None:
    folder_path = tmp_path / "mappings"
    folder_path.mkdir()

    mock_validate.return_value = False

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v2", "from-folder", str(folder_path)]
    )

    assert result.exit_code == 1
    assert "❌ Invalid packages found v2 packages" in caplog.text


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v1_from_archive")
def test_validate_from_archive_v1_valid_package_output(mock_validate,
                                                       typer_cli_runner: CliRunner,
                                                       dummy_mapping_package_path: Path,
                                                       caplog) -> None:
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code == 0
    assert "✅ Valid v1 package" in caplog.text


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v2_from_archive")
def test_validate_from_archive_v2_valid_package_output(mock_validate,
                                                       typer_cli_runner: CliRunner,
                                                       dummy_mapping_package_path: Path,
                                                       caplog) -> None:
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v2", "from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code == 0
    assert "✅ Valid v2 package" in caplog.text


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v1_from_archive")
def test_validate_from_archive_v1_invalid_package_output(mock_validate,
                                                         typer_cli_runner: CliRunner,
                                                         dummy_mapping_package_path: Path,
                                                         caplog) -> None:
    mock_validate.return_value = False

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code == 1
    assert "❌ Invalid v1 package" in caplog.text


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v2_from_archive")
def test_validate_from_archive_v2_invalid_package_output(mock_validate,
                                                         typer_cli_runner: CliRunner,
                                                         dummy_mapping_package_path: Path,
                                                         caplog) -> None:
    mock_validate.return_value = False

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v2", "from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code == 1
    assert "❌ Invalid v2 package" in caplog.text


def test_validate_verbose_option(typer_cli_runner: CliRunner,
                                 dummy_mapping_package_path: Path) -> None:
    with patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v1_from_archive"):
        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v1", "from-archive", str(dummy_mapping_package_path), "--verbose"]
        )

        assert result.exit_code == 0

@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v3_from_archive")
def test_validate_from_archive_command_v3(mock_validate,
                                          typer_cli_runner: CliRunner,
                                          dummy_mapping_package_path: Path) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3", "from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_package_archive_path=dummy_mapping_package_path,
        mapping_package_loader=MappingPackageV3Loader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v3_from_archive")
def test_validate_from_archive_command_v3_with_options(mock_validate,
                                                       typer_cli_runner: CliRunner,
                                                       dummy_mapping_package_path: Path) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3", "from-archive", str(dummy_mapping_package_path),
         "--include-test-data", "--include-output"]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_package_archive_path=dummy_mapping_package_path,
        mapping_package_loader=MappingPackageV3Loader(include_test_data=True, include_output=True)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_from_github")
def test_validate_from_github_command_v3(mock_validate,
                                         dummy_invalid_github_repo_url: str,
                                         dummy_get_all_packages_pattern: str,
                                         dummy_github_branch_name: str,
                                         typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3", "from-github", dummy_invalid_github_repo_url,
         dummy_get_all_packages_pattern, "--branch", dummy_github_branch_name]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=dummy_github_branch_name,
        mapping_package_loader=MappingPackageV3Loader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_from_github")
def test_validate_from_github_command_v3_with_options(mock_validate,
                                                      dummy_invalid_github_repo_url: str,
                                                      dummy_get_all_packages_pattern: str,
                                                      dummy_github_branch_name: str,
                                                      typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3", "from-github", dummy_invalid_github_repo_url,
         dummy_get_all_packages_pattern, "--branch", dummy_github_branch_name,
         "--include-test-data", "--include-output"]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=dummy_github_branch_name,
        mapping_package_loader=MappingPackageV3Loader(include_test_data=True, include_output=True)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_from_github")
def test_validate_from_github_command_v3_without_branch(mock_validate,
                                                        dummy_invalid_github_repo_url: str,
                                                        dummy_get_all_packages_pattern: str,
                                                        typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3", "from-github", dummy_invalid_github_repo_url,
         dummy_get_all_packages_pattern]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=None,
        mapping_package_loader=MappingPackageV3Loader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_from_folder")
def test_validate_from_folder_command_v3(mock_validate,
                                         typer_cli_runner: CliRunner,
                                         tmp_path: Path) -> None:
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3", "from-folder", str(tmp_path)]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_packages_folder_path=tmp_path,
        update_hash=False,
        mapping_package_loader=MappingPackageV3Loader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_from_folder")
def test_validate_from_folder_command_v3_with_options(mock_validate,
                                                      typer_cli_runner: CliRunner,
                                                      tmp_path: Path) -> None:
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3", "from-folder", str(tmp_path),
         "--include-test-data", "--include-output", "--update-hash"]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_packages_folder_path=tmp_path,
        update_hash=True,
        mapping_package_loader=MappingPackageV3Loader(include_test_data=True, include_output=True)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_from_folder")
def test_validate_from_folder_v3_success_output(mock_validate,
                                                typer_cli_runner: CliRunner,
                                                tmp_path: Path,
                                                caplog) -> None:
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3", "from-folder", str(tmp_path)]
    )

    assert result.exit_code == 0
    assert "✅ All valid v3 packages" in caplog.text


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_from_folder")
def test_validate_from_folder_v3_failure_output(mock_validate,
                                                typer_cli_runner: CliRunner,
                                                tmp_path: Path,
                                                caplog) -> None:
    folder_path = tmp_path / "mappings"
    folder_path.mkdir()

    mock_validate.return_value = False

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3", "from-folder", str(folder_path)]
    )

    assert result.exit_code == 1
    assert "❌ Invalid packages found v3 packages" in caplog.text


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v3_from_archive")
def test_validate_from_archive_v3_valid_package_output(mock_validate,
                                                       typer_cli_runner: CliRunner,
                                                       dummy_mapping_package_path: Path,
                                                       caplog) -> None:
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3", "from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code == 0
    assert "✅ Valid v3 package" in caplog.text


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v3_from_archive")
def test_validate_from_archive_v3_invalid_package_output(mock_validate,
                                                         typer_cli_runner: CliRunner,
                                                         dummy_mapping_package_path: Path,
                                                         caplog) -> None:
    mock_validate.return_value = False

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3", "from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code == 1
    assert "❌ Invalid v3 package" in caplog.text


def test_validate_cli_command_valid_version_v3(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_validate_subcommand, ["--version", "v3", "--help"])

    assert result.exit_code == 0
    assert "from-archive" in result.stdout
    assert "from-github" in result.stdout
    assert "from-folder" in result.stdout


def test_validate_common_callback_sets_context(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "--help"]
    )

    assert result.exit_code == 0


def test_validate_common_callback_invalid_version_error_message(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v99"]
    )

    assert result.exit_code != 0


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v1_from_archive")
def test_validate_from_archive_handles_exception(mock_validate,
                                                 typer_cli_runner: CliRunner,
                                                 dummy_mapping_package_path: Path) -> None:
    mock_validate.side_effect = Exception("Unexpected error")

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code != 0


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v1_from_folder")
def test_validate_from_folder_handles_exception(mock_validate,
                                                typer_cli_runner: CliRunner,
                                                tmp_path: Path) -> None:
    mock_validate.side_effect = Exception("Unexpected error")

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-folder", str(tmp_path)]
    )

    assert result.exit_code != 0


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v1_from_github")
def test_validate_from_github_handles_exception(mock_validate,
                                                dummy_invalid_github_repo_url: str,
                                                dummy_get_all_packages_pattern: str,
                                                typer_cli_runner: CliRunner) -> None:
    mock_validate.side_effect = Exception("Unexpected error")

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v1", "from-github", dummy_invalid_github_repo_url,
         dummy_get_all_packages_pattern]
    )

    assert result.exit_code != 0


def test_validate_common_callback_invalid_version_raises_bad_parameter(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v99", "from-folder", "/tmp"]
    )

    assert result.exit_code != 0
    assert "Version must be" in result.stdout or "Invalid value" in result.stdout


def test_validate_from_folder_exits_with_code_1_on_validation_failure(
        typer_cli_runner: CliRunner,
        tmp_path: Path) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v1_from_folder") as mock_validate:
        mock_validate.return_value = False

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v1", "from-folder", str(tmp_path)]
        )

        assert result.exit_code == 1


def test_validate_from_folder_exits_with_code_1_on_validation_failure_v2(
        typer_cli_runner: CliRunner,
        tmp_path: Path) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v2_from_folder") as mock_validate:
        mock_validate.return_value = False

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v2", "from-folder", str(tmp_path)]
        )

        assert result.exit_code == 1


def test_validate_from_folder_exits_with_code_1_on_validation_failure_v3(
        typer_cli_runner: CliRunner,
        tmp_path: Path) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_from_folder") as mock_validate:
        mock_validate.return_value = False

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v3", "from-folder", str(tmp_path)]
        )

        assert result.exit_code == 1


def test_validate_from_archive_exits_with_code_1_on_validation_failure_v1(
        typer_cli_runner: CliRunner,
        dummy_mapping_package_path: Path) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v1_from_archive") as mock_validate:
        mock_validate.return_value = False

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v1", "from-archive", str(dummy_mapping_package_path)]
        )

        assert result.exit_code == 1


def test_validate_from_archive_exits_with_code_1_on_validation_failure_v2(
        typer_cli_runner: CliRunner,
        dummy_mapping_package_path: Path) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v2_from_archive") as mock_validate:
        mock_validate.return_value = False

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v2", "from-archive", str(dummy_mapping_package_path)]
        )

        assert result.exit_code == 1


def test_validate_from_archive_exits_with_code_1_on_validation_failure_v3(
        typer_cli_runner: CliRunner,
        dummy_mapping_package_path: Path) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v3_from_archive") as mock_validate:
        mock_validate.return_value = False

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v3", "from-archive", str(dummy_mapping_package_path)]
        )

        assert result.exit_code == 1


def test_validate_from_github_exits_with_code_1_on_validation_failure_v1(
        typer_cli_runner: CliRunner,
        dummy_invalid_github_repo_url: str,
        dummy_get_all_packages_pattern: str) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v1_from_github") as mock_validate:
        mock_validate.return_value = False

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v1", "from-github", dummy_invalid_github_repo_url, dummy_get_all_packages_pattern]
        )

        assert result.exit_code == 1


def test_validate_from_github_exits_with_code_1_on_validation_failure_v2(
        typer_cli_runner: CliRunner,
        dummy_invalid_github_repo_url: str,
        dummy_get_all_packages_pattern: str) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v2_from_github") as mock_validate:
        mock_validate.return_value = False

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v2", "from-github", dummy_invalid_github_repo_url, dummy_get_all_packages_pattern]
        )

        assert result.exit_code == 1


def test_validate_from_github_exits_with_code_1_on_validation_failure_v3(
        typer_cli_runner: CliRunner,
        dummy_invalid_github_repo_url: str,
        dummy_get_all_packages_pattern: str) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_from_github") as mock_validate:
        mock_validate.return_value = False

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v3", "from-github", dummy_invalid_github_repo_url, dummy_get_all_packages_pattern]
        )

        assert result.exit_code == 1


def test_validate_common_callback_with_invalid_version_in_context(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "invalid_version"]
    )

    assert result.exit_code != 0


def test_validate_cli_help_shows_all_commands(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_validate_subcommand, ["--help"])

    assert result.exit_code == 0
    assert "validate" in result.stdout.lower()
    assert "version" in result.stdout.lower()


def test_validate_from_folder_success_exits_with_code_0_v1(
        typer_cli_runner: CliRunner,
        tmp_path: Path) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v1_from_folder") as mock_validate:
        mock_validate.return_value = True

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v1", "from-folder", str(tmp_path)]
        )

        assert result.exit_code == 0


def test_validate_from_folder_success_exits_with_code_0_v2(
        typer_cli_runner: CliRunner,
        tmp_path: Path) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v2_from_folder") as mock_validate:
        mock_validate.return_value = True

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v2", "from-folder", str(tmp_path)]
        )

        assert result.exit_code == 0


def test_validate_from_folder_success_exits_with_code_0_v3(
        typer_cli_runner: CliRunner,
        tmp_path: Path) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_from_folder") as mock_validate:
        mock_validate.return_value = True

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v3", "from-folder", str(tmp_path)]
        )

        assert result.exit_code == 0


def test_validate_from_archive_success_exits_with_code_0_v1(
        typer_cli_runner: CliRunner,
        dummy_mapping_package_path: Path) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v1_from_archive") as mock_validate:
        mock_validate.return_value = True

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v1", "from-archive", str(dummy_mapping_package_path)]
        )

        assert result.exit_code == 0


def test_validate_from_archive_success_exits_with_code_0_v2(
        typer_cli_runner: CliRunner,
        dummy_mapping_package_path: Path) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v2_from_archive") as mock_validate:
        mock_validate.return_value = True

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v2", "from-archive", str(dummy_mapping_package_path)]
        )

        assert result.exit_code == 0


def test_validate_from_archive_success_exits_with_code_0_v3(
        typer_cli_runner: CliRunner,
        dummy_mapping_package_path: Path) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v3_from_archive") as mock_validate:
        mock_validate.return_value = True

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v3", "from-archive", str(dummy_mapping_package_path)]
        )

        assert result.exit_code == 0


def test_validate_from_github_success_exits_with_code_0_v1(
        typer_cli_runner: CliRunner,
        dummy_invalid_github_repo_url: str,
        dummy_get_all_packages_pattern: str) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v1_from_github") as mock_validate:
        mock_validate.return_value = True

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v1", "from-github", dummy_invalid_github_repo_url, dummy_get_all_packages_pattern]
        )

        assert result.exit_code == 0


def test_validate_from_github_success_exits_with_code_0_v2(
        typer_cli_runner: CliRunner,
        dummy_invalid_github_repo_url: str,
        dummy_get_all_packages_pattern: str) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v2_from_github") as mock_validate:
        mock_validate.return_value = True

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v2", "from-github", dummy_invalid_github_repo_url, dummy_get_all_packages_pattern]
        )

        assert result.exit_code == 0


def test_validate_from_github_success_exits_with_code_0_v3(
        typer_cli_runner: CliRunner,
        dummy_invalid_github_repo_url: str,
        dummy_get_all_packages_pattern: str) -> None:
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_from_github") as mock_validate:
        mock_validate.return_value = True

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v3", "from-github", dummy_invalid_github_repo_url, dummy_get_all_packages_pattern]
        )

        assert result.exit_code == 0


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v3_lightweight_from_archive")
def test_validate_from_archive_command_v3_lightweight(mock_validate,
                                                      typer_cli_runner: CliRunner,
                                                      dummy_mapping_package_path: Path) -> None:
    """Test v3-lightweight validation from archive."""
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3-lightweight", "from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_package_archive_path=dummy_mapping_package_path,
        mapping_package_loader=MappingPackageV3LightweightLoader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v3_lightweight_from_archive")
def test_validate_from_archive_command_v3_lightweight_with_options(mock_validate,
                                                                    typer_cli_runner: CliRunner,
                                                                    dummy_mapping_package_path: Path) -> None:
    """Test v3-lightweight validation from archive with options."""
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3-lightweight", "from-archive", str(dummy_mapping_package_path),
         "--include-test-data", "--include-output"]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_package_archive_path=dummy_mapping_package_path,
        mapping_package_loader=MappingPackageV3LightweightLoader(include_test_data=True, include_output=True)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_lightweight_from_github")
def test_validate_from_github_command_v3_lightweight(mock_validate,
                                                     dummy_invalid_github_repo_url: str,
                                                     dummy_get_all_packages_pattern: str,
                                                     dummy_github_branch_name: str,
                                                     typer_cli_runner: CliRunner) -> None:
    """Test v3-lightweight validation from GitHub."""
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3-lightweight", "from-github", dummy_invalid_github_repo_url,
         dummy_get_all_packages_pattern, "--branch", dummy_github_branch_name]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=dummy_github_branch_name,
        mapping_package_loader=MappingPackageV3LightweightLoader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_lightweight_from_github")
def test_validate_from_github_command_v3_lightweight_with_options(mock_validate,
                                                                  dummy_invalid_github_repo_url: str,
                                                                  dummy_get_all_packages_pattern: str,
                                                                  dummy_github_branch_name: str,
                                                                  typer_cli_runner: CliRunner) -> None:
    """Test v3-lightweight validation from GitHub with options."""
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3-lightweight", "from-github", dummy_invalid_github_repo_url,
         dummy_get_all_packages_pattern, "--branch", dummy_github_branch_name,
         "--include-test-data", "--include-output"]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=dummy_github_branch_name,
        mapping_package_loader=MappingPackageV3LightweightLoader(include_test_data=True, include_output=True)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_lightweight_from_github")
def test_validate_from_github_command_v3_lightweight_without_branch(mock_validate,
                                                                     dummy_invalid_github_repo_url: str,
                                                                     dummy_get_all_packages_pattern: str,
                                                                     typer_cli_runner: CliRunner) -> None:
    """Test v3-lightweight validation from GitHub without branch."""
    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3-lightweight", "from-github", dummy_invalid_github_repo_url,
         dummy_get_all_packages_pattern]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        github_repository_url=dummy_invalid_github_repo_url,
        packages_path_pattern=dummy_get_all_packages_pattern,
        branch_or_tag_name=None,
        mapping_package_loader=MappingPackageV3LightweightLoader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_lightweight_from_folder")
def test_validate_from_folder_command_v3_lightweight(mock_validate,
                                                     typer_cli_runner: CliRunner,
                                                     tmp_path: Path) -> None:
    """Test v3-lightweight validation from folder."""
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3-lightweight", "from-folder", str(tmp_path)]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_packages_folder_path=tmp_path,
        update_hash=False,
        mapping_package_loader=MappingPackageV3LightweightLoader(include_test_data=False, include_output=False)
    )


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_lightweight_from_folder")
def test_validate_from_folder_command_v3_lightweight_with_options(mock_validate,
                                                                  typer_cli_runner: CliRunner,
                                                                  tmp_path: Path) -> None:
    """Test v3-lightweight validation from folder with options."""
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3-lightweight", "from-folder", str(tmp_path),
         "--include-test-data", "--include-output", "--update-hash"]
    )

    assert result.exit_code == 0

    mock_validate.assert_called_once_with(
        mapping_packages_folder_path=tmp_path,
        update_hash=True,
        mapping_package_loader=MappingPackageV3LightweightLoader(include_test_data=True, include_output=True)
    )


def test_validate_cli_command_valid_version_v3_lightweight(typer_cli_runner: CliRunner) -> None:
    """Test that v3-lightweight version is accepted in the callback."""
    result = typer_cli_runner.invoke(mssdk_cli_validate_subcommand, ["--version", "v3-lightweight", "--help"])

    assert result.exit_code == 0
    assert "from-archive" in result.stdout
    assert "from-github" in result.stdout
    assert "from-folder" in result.stdout


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_lightweight_from_folder")
def test_validate_from_folder_v3_lightweight_success_output(mock_validate,
                                                            typer_cli_runner: CliRunner,
                                                            tmp_path: Path,
                                                            caplog) -> None:
    """Test v3-lightweight validation from folder success output."""
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3-lightweight", "from-folder", str(tmp_path)]
    )

    assert result.exit_code == 0
    assert "✅ All valid v3-lightweight packages" in caplog.text


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_lightweight_from_folder")
def test_validate_from_folder_v3_lightweight_failure_output(mock_validate,
                                                              typer_cli_runner: CliRunner,
                                                              tmp_path: Path,
                                                              caplog) -> None:
    """Test v3-lightweight validation from folder failure output."""
    folder_path = tmp_path / "mappings"
    folder_path.mkdir()

    mock_validate.return_value = False

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3-lightweight", "from-folder", str(folder_path)]
    )

    assert result.exit_code == 1
    assert "❌ Invalid packages found v3-lightweight packages" in caplog.text


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v3_lightweight_from_archive")
def test_validate_from_archive_v3_lightweight_valid_package_output(mock_validate,
                                                                     typer_cli_runner: CliRunner,
                                                                     dummy_mapping_package_path: Path,
                                                                     caplog) -> None:
    """Test v3-lightweight validation from archive valid package output."""
    mock_validate.return_value = True

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3-lightweight", "from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code == 0
    assert "✅ Valid v3-lightweight package" in caplog.text


@patch("mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v3_lightweight_from_archive")
def test_validate_from_archive_v3_lightweight_invalid_package_output(mock_validate,
                                                                      typer_cli_runner: CliRunner,
                                                                      dummy_mapping_package_path: Path,
                                                                      caplog) -> None:
    """Test v3-lightweight validation from archive invalid package output."""
    mock_validate.return_value = False

    result = typer_cli_runner.invoke(
        mssdk_cli_validate_subcommand,
        ["--version", "v3-lightweight", "from-archive", str(dummy_mapping_package_path)]
    )

    assert result.exit_code == 1
    assert "❌ Invalid v3-lightweight package" in caplog.text


def test_validate_from_folder_exits_with_code_1_on_validation_failure_v3_lightweight(
        typer_cli_runner: CliRunner,
        tmp_path: Path) -> None:
    """Test v3-lightweight validation from folder exits with code 1 on failure."""
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_lightweight_from_folder") as mock_validate:
        mock_validate.return_value = False

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v3-lightweight", "from-folder", str(tmp_path)]
        )

        assert result.exit_code == 1


def test_validate_from_archive_exits_with_code_1_on_validation_failure_v3_lightweight(
        typer_cli_runner: CliRunner,
        dummy_mapping_package_path: Path) -> None:
    """Test v3-lightweight validation from archive exits with code 1 on failure."""
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v3_lightweight_from_archive") as mock_validate:
        mock_validate.return_value = False

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v3-lightweight", "from-archive", str(dummy_mapping_package_path)]
        )

        assert result.exit_code == 1


def test_validate_from_github_exits_with_code_1_on_validation_failure_v3_lightweight(
        typer_cli_runner: CliRunner,
        dummy_invalid_github_repo_url: str,
        dummy_get_all_packages_pattern: str) -> None:
    """Test v3-lightweight validation from GitHub exits with code 1 on failure."""
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_lightweight_from_github") as mock_validate:
        mock_validate.return_value = False

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v3-lightweight", "from-github", dummy_invalid_github_repo_url, dummy_get_all_packages_pattern]
        )

        assert result.exit_code == 1


def test_validate_from_folder_success_exits_with_code_0_v3_lightweight(
        typer_cli_runner: CliRunner,
        tmp_path: Path) -> None:
    """Test v3-lightweight validation from folder success exits with code 0."""
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_lightweight_from_folder") as mock_validate:
        mock_validate.return_value = True

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v3-lightweight", "from-folder", str(tmp_path)]
        )

        assert result.exit_code == 0


def test_validate_from_archive_success_exits_with_code_0_v3_lightweight(
        typer_cli_runner: CliRunner,
        dummy_mapping_package_path: Path) -> None:
    """Test v3-lightweight validation from archive success exits with code 0."""
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_mapping_package_v3_lightweight_from_archive") as mock_validate:
        mock_validate.return_value = True

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v3-lightweight", "from-archive", str(dummy_mapping_package_path)]
        )

        assert result.exit_code == 0


def test_validate_from_github_success_exits_with_code_0_v3_lightweight(
        typer_cli_runner: CliRunner,
        dummy_invalid_github_repo_url: str,
        dummy_get_all_packages_pattern: str) -> None:
    """Test v3-lightweight validation from GitHub success exits with code 0."""
    with patch(
            "mapping_suite_sdk.core.entrypoints.cli.validate.validate_bulk_mapping_packages_v3_lightweight_from_github") as mock_validate:
        mock_validate.return_value = True

        result = typer_cli_runner.invoke(
            mssdk_cli_validate_subcommand,
            ["--version", "v3-lightweight", "from-github", dummy_invalid_github_repo_url, dummy_get_all_packages_pattern]
        )

        assert result.exit_code == 0