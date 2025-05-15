import logging

import typer

from mapping_suite_sdk import __version__
from mapping_suite_sdk.entrypoints.cli import validate
from mapping_suite_sdk.vars import MSSDK_TYPER_DEFAULT_ARGS, MSSDK_LOGGING_MESSAGE_FORMAT

logger = logging.getLogger(__name__)


def typer_version_callback(show_version: bool) -> None:
    if show_version:
        typer.echo(f"MSSDK Version: {__version__}")
        raise typer.Exit()


mssdk_cli_command = typer.Typer(
    **MSSDK_TYPER_DEFAULT_ARGS,
    name="mssdk",
    help="Mapping suite SDK CLI"
)
mssdk_cli_command.add_typer(validate.mssdk_cli_validate_subcommand)


@mssdk_cli_command.callback()
def common(
        ctx: typer.Context,
        version: bool = typer.Option(None, "--version", is_eager=True, callback=typer_version_callback),
):
    logger.debug(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=None,
                                                     message=f"Running MSSDK CLI with version: {__version__}"))


if __name__ == "__main__":
    mssdk_cli_command()
