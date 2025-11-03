import logging
from pathlib import Path

import typer

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.entrypoints.cli import typer_verbose_callback
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader
from mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2 import load_mapping_package_v2_from_folder
from mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser import MappingPackageV3Serialiser
from mapping_suite_sdk.mapping_package_v3.services.create_mapping_package_v3 import create_mpv3_from_mpv2

logger = logging.getLogger(__name__)

mssdk_cli_create_subcommand = typer.Typer(**mssdk_config.MSSDK_TYPER_DEFAULT_ARGS,
                                          name="create",
                                          help="Mapping Package Creation commands.")


@mssdk_cli_create_subcommand.callback()
def create_common(
        ctx: typer.Context,
        version: str = typer.Option(..., "--version", help="New mapping package version (v3)")
):
    """Set creation version context."""
    if version != "v3":
        raise typer.BadParameter(f"New version must be v3, got: {version}")

    ctx.ensure_object(dict)
    ctx.obj['new_version'] = version


@mssdk_cli_create_subcommand.command(**mssdk_config.MSSDK_TYPER_COMMANDS_DEFAULT_ARGS,
                                     name="from",
                                     help="Create new package from base version.")
def mssdk_cli_create_mapping_package_from(
        ctx: typer.Context,
        base_version: str = typer.Option(..., "--version", help="Base mapping package version (v2)"),
        input_path: Path = typer.Option(..., "--input", help="Path to input mapping package directory"),
        output_path: Path = typer.Option(..., "--output", help="Path to output directory for new mapping package"),
        verbose: bool = typer.Option(False, "--verbose", "-v",
                                     is_eager=True,
                                     callback=typer_verbose_callback),
) -> None:
    """Create new mapping package from base version."""
    new_version = ctx.obj['new_version']

    if base_version != "v2":
        raise typer.BadParameter(f"Base version must be v2, got: {base_version}")

    logger.debug(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=input_path,
        message=f"Creating {new_version} package from {base_version} package"))

    if not input_path.exists():
        raise typer.BadParameter(f"Input path does not exist: {input_path}")
    if not input_path.is_dir():
        raise typer.BadParameter(f"Input path is not a directory: {input_path}")

    output_path.mkdir(parents=True, exist_ok=True)

    loader = MappingPackageV2Loader()
    mpv2 = load_mapping_package_v2_from_folder(
        mapping_package_folder_path=input_path,
        mapping_package_loader=loader
    )

    mpv3 = create_mpv3_from_mpv2(mpv2)

    MappingPackageV3Serialiser().serialise(output_path, mpv3)

    logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=output_path,
        message=f"✅ Created {new_version} package"))

