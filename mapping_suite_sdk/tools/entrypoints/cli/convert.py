import logging
from enum import Enum
from pathlib import Path

import typer
from pydantic import ValidationError

from mapping_suite_sdk import mssdk_config

from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader
from mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2 import load_mapping_package_v2_from_folder
from mapping_suite_sdk.mapping_package_v3.adapters.package_loader import MappingPackageV3Loader
from mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser import MappingPackageV3Serialiser
from mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser_lightweight import MappingPackageV3LightweightSerialiser
from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3 import load_mapping_package_v3_from_folder
from mapping_suite_sdk.tools.entrypoints.cli import typer_verbose_callback
from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import convert_mapping_package_v2_to_v3
from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3 import is_mapping_package_already_converted
from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import convert_mapping_package_v3_to_v3_lightweight

logger = logging.getLogger(__name__)


class Version(str, Enum):
    """Mapping package versions supported by the SDK."""
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"
    V3_LIGHTWEIGHT = "v3-lightweight"




def _load_mapping_package_from_folder(from_version: str, mapping_package_folder_path: Path):
    """Dynamically load a mapping package based on version."""
    if from_version == Version.V2:
        loader = MappingPackageV2Loader()
        return load_mapping_package_v2_from_folder(
            mapping_package_folder_path=mapping_package_folder_path,
            mapping_package_loader=loader
        )
    elif from_version == Version.V3:
        loader = MappingPackageV3Loader()
        return load_mapping_package_v3_from_folder(
            mapping_package_folder_path=mapping_package_folder_path,
            mapping_package_loader=loader
        )
    else:
        raise typer.BadParameter(f"Unsupported source version: {from_version}")


def _convert_mapping_package(from_version: str, to_version: str, source_package):
    """Convert mapping package using service layer."""
    if from_version == Version.V2 and to_version == Version.V3:
        return convert_mapping_package_v2_to_v3(source_package)
    elif from_version == Version.V3 and to_version == Version.V3_LIGHTWEIGHT:
        return convert_mapping_package_v3_to_v3_lightweight(source_package)
    else:
        raise typer.BadParameter(f"Unsupported conversion: {from_version} -> {to_version}")


def _serialise_mapping_package(to_version: str, mapping_package_folder_path: Path, converted_package):
    """Dynamically serialize a mapping package based on version."""
    if to_version == Version.V3:
        serialiser = MappingPackageV3Serialiser()
        serialiser.serialise(mapping_package_folder_path, converted_package)
    elif to_version == Version.V3_LIGHTWEIGHT:
        serialiser = MappingPackageV3LightweightSerialiser()
        serialiser.serialise(mapping_package_folder_path, converted_package)
    else:
        raise typer.BadParameter(f"Unsupported target version: {to_version}")


def _convert_package_from_folder(from_version: str, to_version: str, mapping_package_folder_path: Path):
    """Convert a mapping package using service layer functions."""
    source_package = _load_mapping_package_from_folder(from_version, mapping_package_folder_path)
    converted_package = _convert_mapping_package(from_version, to_version, source_package)
    _serialise_mapping_package(to_version, mapping_package_folder_path, converted_package)


mssdk_cli_convert_subcommand = typer.Typer(**mssdk_config.MSSDK_TYPER_DEFAULT_ARGS,
                                           name="convert",
                                           help="Mapping Package Conversion commands.")


@mssdk_cli_convert_subcommand.callback()
def convert_common(
        ctx: typer.Context,
        to_version: str = typer.Option(..., "--to-version", help=f"Target mapping package version ({Version.V3.value} or {Version.V3_LIGHTWEIGHT.value})"),
        from_version: str = typer.Option(..., "--from-version", help=f"Source mapping package version ({Version.V2.value} or {Version.V3.value})"),
        verbose: bool = typer.Option(False, "--verbose", "-v",
                                     is_eager=True,
                                     callback=typer_verbose_callback),
) -> None:
    """Set conversion version context."""
    if to_version not in [Version.V3, Version.V3_LIGHTWEIGHT]:
        raise typer.BadParameter(f"Target version must be {Version.V3} or {Version.V3_LIGHTWEIGHT}, got: {to_version}")

    if to_version == Version.V3 and from_version != Version.V2:
        raise typer.BadParameter(f"Source version must be {Version.V2} for target {Version.V3}, got: {from_version}")
    
    if to_version == Version.V3_LIGHTWEIGHT and from_version != Version.V3:
        raise typer.BadParameter(f"Source version must be {Version.V3} for target {Version.V3_LIGHTWEIGHT}, got: {from_version}")

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

    # Check if already converted
    if is_mapping_package_already_converted(mapping_package_path, to_version):
        logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
            package_source=mapping_package_path,
            message=f"Package is already {to_version}, skipping conversion"))
        return

    _convert_package_from_folder(from_version, to_version, mapping_package_path)

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
    to_version = ctx.obj['to_version']
    from_version = ctx.obj['from_version']

    logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=folder_path,
        message=f"Converting {from_version} packages to {to_version} packages from folder"))

    if not folder_path.exists():
        raise typer.BadParameter(f"Folder path does not exist: {folder_path}")
    if not folder_path.is_dir():
        raise typer.BadParameter(f"Folder path is not a directory: {folder_path}")

    # Get list of directories directly
    mp_folders = [d for d in folder_path.iterdir() if d.is_dir()]
    total_count = len(mp_folders)
    converted_count = 0
    skipped_count = 0

    for mp_folder in mp_folders:
        # Check if already converted
        if is_mapping_package_already_converted(mp_folder, to_version):
            skipped_count += 1
            logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
                package_source=mp_folder,
                message=f"Package is already {to_version}, skipping conversion"))
            continue

        # Convert package - hard fail
        _convert_package_from_folder(from_version, to_version, mp_folder)
        converted_count += 1
        logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
            package_source=mp_folder,
            message=f"✅ Converted {from_version} package to {to_version} package"))

    # Summary message with counts
    logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=folder_path,
        message=f"✅ Conversion complete: {converted_count} converted, {skipped_count} skipped (out of {total_count} total)"))

