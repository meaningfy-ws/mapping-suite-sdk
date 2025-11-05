import logging
from enum import Enum
from pathlib import Path

import typer

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.entrypoints.cli import typer_verbose_callback
from mapping_suite_sdk.mapping_package_v3.services.convert_mapping_package_v3 import convert_mpv3_from_mpv2

logger = logging.getLogger(__name__)


class BaseVersion(str, Enum):
    V2 = "v2"


class NewVersion(str, Enum):
    V3 = "v3"


BASE_VERSIONS = [BaseVersion.V2]
NEW_VERSIONS = [NewVersion.V3]

BASE_VERSION_DEFAULT = BaseVersion.V2
NEW_VERSION_DEFAULT = NewVersion.V3


def _load_mapping_package_from_folder(from_version: str, mapping_package_folder_path: Path):
    """Dynamically load a mapping package based on version."""
    if from_version == BaseVersion.V2.value:
        from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader
        from mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2 import load_mapping_package_v2_from_folder
        
        loader = MappingPackageV2Loader()
        return load_mapping_package_v2_from_folder(
            mapping_package_folder_path=mapping_package_folder_path,
            mapping_package_loader=loader
        )
    else:
        raise typer.BadParameter(f"Unsupported source version: {from_version}")


def _convert_mapping_package(from_version: str, to_version: str, source_package):
    """Convert mapping package using service layer."""
    if from_version == BaseVersion.V2.value and to_version == NewVersion.V3.value:
        return convert_mpv3_from_mpv2(source_package)
    else:
        raise typer.BadParameter(f"Unsupported conversion: {from_version} -> {to_version}")


def _serialise_mapping_package(to_version: str, mapping_package_folder_path: Path, converted_package):
    """Dynamically serialize a mapping package based on version."""
    if to_version == NewVersion.V3.value:
        from mapping_suite_sdk.mapping_package_v3.adapters.package_serialiser import MappingPackageV3Serialiser
        
        serialiser = MappingPackageV3Serialiser()
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

    all_converted = True
    converted_count = 0
    failed_count = 0

    for mp_folder in folder_path.iterdir():
        if not mp_folder.is_dir():
            continue

        try:
            _convert_package_from_folder(from_version, to_version, mp_folder)

            converted_count += 1
            logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
                package_source=mp_folder,
                message=f"✅ Converted {from_version} package to {to_version} package"))
        except Exception as conversion_exception:
            failed_count += 1
            all_converted = False
            logger.error(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
                package_source=mp_folder,
                message=f"Cannot convert mapping package: {conversion_exception}"))

    status = "✅ All converted" if all_converted else "❌ Some packages failed to convert"
    logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=folder_path,
        message=f"{status} ({converted_count} converted, {failed_count} failed)"))

    if not all_converted:
        raise typer.Exit(code=1)

