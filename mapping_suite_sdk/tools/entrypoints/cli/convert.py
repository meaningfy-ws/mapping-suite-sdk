import logging
from enum import Enum
from pathlib import Path

import typer

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.tools.entrypoints.cli import typer_verbose_callback
from mapping_suite_sdk.tools.services.convert_mapping_package import (
    Version,
    convert_mapping_package_from_folder,
    convert_mapping_packages_from_folder,
    is_mapping_package_already_converted
)

logger = logging.getLogger(__name__)


# CLI context parameter keys
class ConvertContextKeys:
    """Constants for CLI context dictionary keys used in convert commands."""
    TO_VERSION = "to_version"
    FROM_VERSION = "from_version"


mssdk_cli_convert_subcommand = typer.Typer(**mssdk_config.MSSDK_TYPER_DEFAULT_ARGS,
                                           name="convert",
                                           help="Mapping Package Conversion commands.")


@mssdk_cli_convert_subcommand.callback()
def convert_common(
        ctx: typer.Context,
        to_version: str = typer.Option(..., "--to-version", help=f"Target mapping package version ({Version.V3.value} or {Version.V3L.value})"),
        from_version: str = typer.Option(..., "--from-version", help=f"Source mapping package version ({Version.V1.value}, {Version.V2.value} or {Version.V3.value})"),
        verbose: bool = typer.Option(False, "--verbose", "-v",
                                     is_eager=True,
                                     callback=typer_verbose_callback),
) -> None:
    """Set conversion version context."""
    if to_version not in [Version.V3, Version.V3L]:
        raise typer.BadParameter(f"Target version must be {Version.V3} or {Version.V3L}, got: {to_version}")

    if to_version == Version.V3 and from_version not in [Version.V1, Version.V2]:
        raise typer.BadParameter(
            f"Source version must be {Version.V1} or {Version.V2} for target {Version.V3}, got: {from_version}"
        )
    
    if to_version == Version.V3L and from_version not in [Version.V1, Version.V2, Version.V3]:
        raise typer.BadParameter(
            f"Source version must be {Version.V1}, {Version.V2} or {Version.V3} for target {Version.V3L}, got: {from_version}"
        )

    ctx.ensure_object(dict)
    ctx.obj[ConvertContextKeys.TO_VERSION] = to_version
    ctx.obj[ConvertContextKeys.FROM_VERSION] = from_version


@mssdk_cli_convert_subcommand.command(**mssdk_config.MSSDK_TYPER_COMMANDS_DEFAULT_ARGS,
                                      name="from-package",
                                      help="Convert mapping package from package directory.")
def mssdk_cli_convert_mapping_package_from_package(
        ctx: typer.Context,
        mapping_package_path: Path = typer.Argument(..., exists=True),
) -> None:
    """Convert mapping package from package directory."""
    to_version = ctx.obj[ConvertContextKeys.TO_VERSION]
    from_version = ctx.obj[ConvertContextKeys.FROM_VERSION]

    logger.debug(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=mapping_package_path,
        message=f"Converting {from_version} package to {to_version} package"))

    # Check if already converted
    if is_mapping_package_already_converted(mapping_package_path, to_version):
        logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
            package_source=mapping_package_path,
            message=f"Package is already {to_version}, skipping conversion"))
        return

    # Hard fail: let service exceptions propagate
    convert_mapping_package_from_folder(from_version, to_version, mapping_package_path)
    logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=mapping_package_path,
        message=f"✅ Converted {from_version} package to {to_version} package"))


@mssdk_cli_convert_subcommand.command(**mssdk_config.MSSDK_TYPER_COMMANDS_DEFAULT_ARGS,
                                      name="from-folder",
                                      help="Convert mapping packages from folder.")
def mssdk_cli_convert_mapping_packages_from_folder(
        ctx: typer.Context,
        folder_path: Path = typer.Argument(...),
) -> None:
    """Convert mapping packages from folder."""
    to_version = ctx.obj[ConvertContextKeys.TO_VERSION]
    from_version = ctx.obj[ConvertContextKeys.FROM_VERSION]

    logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=folder_path,
        message=f"Converting {from_version} packages to {to_version} packages from folder"))

    # Hard fail: let service exceptions propagate
    result = convert_mapping_packages_from_folder(from_version, to_version, folder_path)
    logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=folder_path,
        message=f"✅ Conversion complete: {result['converted']} converted, "
                f"{result['skipped']} skipped (out of {result['total']} total)"))

