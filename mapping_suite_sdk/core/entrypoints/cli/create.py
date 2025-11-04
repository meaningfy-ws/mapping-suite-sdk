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
                                          help="Mapping Package Conversion commands.",
                                          invoke_without_command=True)


@mssdk_cli_convert_subcommand.callback(invoke_without_command=True)
def mssdk_cli_convert_mapping_package(
        version: str = typer.Option(..., "--version", help=f"New mapping package version ({NEW_VERSION_DEFAULT.value})"),
        from_version: str = typer.Option(..., "--from-version", help=f"Base mapping package version ({BASE_VERSION_DEFAULT.value})"),
        input_path: Path = typer.Option(..., "--input", help="Path to input mapping package directory"),
        output_path: Path = typer.Option(..., "--output", help="Path to output directory for new mapping package"),
        verbose: bool = typer.Option(False, "--verbose", "-v",
                                     is_eager=True,
                                     callback=typer_verbose_callback),
) -> None:
    """Convert mapping package from base version to new version."""
    if version not in NEW_VERSIONS:
        raise typer.BadParameter(f"New version must be one of {[v.value for v in NEW_VERSIONS]}, got: {version}")

    if from_version not in BASE_VERSIONS:
        raise typer.BadParameter(f"Base version must be one of {[v.value for v in BASE_VERSIONS]}, got: {from_version}")

    logger.debug(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=input_path,
        message=f"Converting {from_version} package to {version} package"))

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
        message=f"✅ Converted {from_version} package to {version} package"))

