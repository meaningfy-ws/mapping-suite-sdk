from typer.testing import CliRunner

from mapping_suite_sdk.entrypoints.cli.validate import mssdk_cli_validate_subcommand


def test_validate_cli_command(typer_cli_runner: CliRunner) -> None:
    result = typer_cli_runner.invoke(mssdk_cli_validate_subcommand, [])

    assert result.exit_code == 0
    assert "validate" in result.stdout
