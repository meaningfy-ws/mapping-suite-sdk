from typer.testing import CliRunner

from mapping_suite_sdk import __version__
from mapping_suite_sdk.entrypoints.cli.mssdk import mssdk_cli_command


def test_mssdk_cli_validate_command(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_command, [])

    assert result.exit_code == 0
    assert "validate" in result.stdout


def test_mssdk_cli_shows_correct_version(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_command, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout
