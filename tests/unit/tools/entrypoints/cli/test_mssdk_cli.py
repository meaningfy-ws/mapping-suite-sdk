from typer.testing import CliRunner

from mapping_suite_sdk import __version__
from mapping_suite_sdk.tools.entrypoints.cli.mssdk import mssdk_cli_command


def test_mssdk_cli_validate_command(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_command, [])

    # no_args_is_help: help is shown, and since Click 8.2 the exit code is 2 (usage error)
    assert result.exit_code == 2
    assert "validate" in result.output


def test_mssdk_cli_shows_correct_version(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_command, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_mssdk_root_callback_runs_before_a_subcommand(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_command, ["convert", "--help"])

    assert result.exit_code == 0
