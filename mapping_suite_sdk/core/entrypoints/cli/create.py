import logging
from enum import Enum
from pathlib import Path

import typer

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.entrypoints.cli import typer_verbose_callback
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader
from mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2 import load_mapping_package_v2_from_folder
from mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser import MappingPackageV3Serialiser
from mapping_suite_sdk.mapping_package_v3.services.create_mapping_package_v3 import create_mpv3_from_mpv2

logger = logging.getLogger(__name__)


class BaseVersion(str, Enum):
    V2 = "v2"


class NewVersion(str, Enum):
    V3 = "v3"


BASE_VERSIONS = [BaseVersion.V2]
NEW_VERSIONS = [NewVersion.V3]

BASE_VERSION_DEFAULT = BaseVersion.V2
NEW_VERSION_DEFAULT = NewVersion.V3

mssdk_cli_convert_subcommand = typer.Typer(**mssdk_config.MSSDK_TYPER_DEFAULT_ARGS,
                                          name="convert",
                                          help="Mapping Package Conversion commands.")


@mssdk_cli_convert_subcommand.callback()
def convert_common(
        ctx: typer.Context,
        to_version: str = typer.Option(..., "--to-version", help=f"Target mapping package version ({NEW_VERSION_DEFAULT.value})"),
        from_version: str = typer.Option(..., "--from-version", help=f"Source mapping package version ({BASE_VERSION_DEFAULT.value})"),
        verbose: bool = typer.Option(False, "--verbose", "-v",
                                     is_eager=True,
                                     callback=typer_verbose_callback),
) -> None:
    """Set conversion version context."""
    if to_version not in NEW_VERSIONS:
        raise typer.BadParameter(f"Target version must be one of {[v.value for v in NEW_VERSIONS]}, got: {to_version}")

    if from_version not in BASE_VERSIONS:
        raise typer.BadParameter(f"Source version must be one of {[v.value for v in BASE_VERSIONS]}, got: {from_version}")

    ctx.ensure_object(dict)
    ctx.obj['to_version'] = to_version
    ctx.obj['from_version'] = from_version


@mssdk_cli_convert_subcommand.command(**mssdk_config.MSSDK_TYPER_COMMANDS_DEFAULT_ARGS,
                                     name="from-package",
                                     help="Convert mapping package from package directory.")
def mssdk_cli_convert_mapping_package_from_package(
        ctx: typer.Context,
        mapping_package_path: Path = typer.Argument(..., exists=True),
) -> None:
    """Convert mapping package from package directory."""
    to_version = ctx.obj['to_version']
    from_version = ctx.obj['from_version']

    logger.debug(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=mapping_package_path,
        message=f"Converting {from_version} package to {to_version} package"))

    if not mapping_package_path.is_dir():
        raise typer.BadParameter(f"Package path is not a directory: {mapping_package_path}")

    loader = MappingPackageV2Loader()
    mpv2 = load_mapping_package_v2_from_folder(
        mapping_package_folder_path=mapping_package_path,
        mapping_package_loader=loader
    )

    mpv3 = create_mpv3_from_mpv2(mpv2)

    MappingPackageV3Serialiser().serialise(mapping_package_path, mpv3)

    logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=mapping_package_path,
        message=f"✅ Converted {from_version} package to {to_version} package"))

