import json
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
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata_jsonld import \
    MappingPackageV3MetadataJSONLD
from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3 import load_mapping_package_v3_from_folder
from mapping_suite_sdk.tools.entrypoints.cli import typer_verbose_callback
from mapping_suite_sdk.tools.services.convert_mapping_package_v3 import convert_mpv3_from_mpv2
from mapping_suite_sdk.tools.services.convert_mapping_package_v3_lightweight import convert_mpv3_lightweight_from_mpv3

logger = logging.getLogger(__name__)

Version = Enum('Version', [('V2', 'v2'), ('V3', 'v3'), ('V3_LIGHTWEIGHT', 'v3-lightweight')])

V2 = Version.V2.value
V3 = Version.V3.value
V3_LIGHTWEIGHT = Version.V3_LIGHTWEIGHT.value


def _is_already_converted(mapping_package_folder_path: Path, to_version: str) -> bool:
    """Check if package is already in the target version by attempting to validate metadata."""
    # Handle nested package structure (folder_name/folder_name/metadata.json)
    # Check both direct path and nested path
    root_folder = mapping_package_folder_path / mapping_package_folder_path.name
    possible_paths = [mapping_package_folder_path]
    if root_folder.exists():
        possible_paths.append(root_folder)

    metadata_file = None
    for path in possible_paths:
        # Check for metadata.json or metadata.jsonld
        test_file = path / "metadata.json"
        if test_file.exists():
            metadata_file = test_file
            break
        test_file = path / "metadata.jsonld"
        if test_file.exists():
            metadata_file = test_file
            break

    if not metadata_file:
        return False

    if to_version == V3:
        # Try to validate as V3 - if it works, it's already converted
        metadata_dict = json.loads(metadata_file.read_text())
        # Add path field if missing (serialiser excludes it, but model requires it)
        if 'path' not in metadata_dict:
            # Calculate relative path from the package folder to the metadata file
            # Handle both direct and nested structures
            relative_path = metadata_file.relative_to(mapping_package_folder_path)
            metadata_dict['path'] = relative_path.as_posix()
        # Validate by attempting to create the model
        # If ValidationError: package is not in target version (not converted) - return False
        # Other exceptions hard fail
        try:
            MappingPackageV3MetadataJSONLD.model_validate(metadata_dict)
            # Check if it's full v3 by trying to load it (full v3 has more components)
            from mapping_suite_sdk.mapping_package_v3.adapters.package_loader import MappingPackageV3Loader
            loader = MappingPackageV3Loader()
            package = loader.load(mapping_package_folder_path)
            # If we can load it as full v3 and it has conceptual_mapping, it's full v3
            if hasattr(package, 'conceptual_mapping_asset') and package.conceptual_mapping_asset:
                return True
            return True
        except ValidationError:
            # Package is not in V3 format, so it's not converted
            return False
    elif to_version == V3_LIGHTWEIGHT:
        # For lightweight, check if it can be loaded as lightweight
        # First check if it has full v3 components (conceptual mapping file)
        # Check both direct path and nested path
        for path in possible_paths:
            conceptual_mapping_path = path / mssdk_config.MPV3_CONCEPTUAL_MAPPING_FILE_ASSET_PATH
            if conceptual_mapping_path.exists():
                # Has conceptual mapping, so it's full v3, not lightweight
                return False
        
        # Try to load as lightweight - if it succeeds, it's lightweight
        # If loading fails, hard fail (let exception propagate)
        from mapping_suite_sdk.mapping_package_v3.adapters.package_loader_lightweight import MappingPackageV3LightweightLoader
        loader = MappingPackageV3LightweightLoader()
        loader.load(mapping_package_folder_path)
        return True
    return False


def _load_mapping_package_from_folder(from_version: str, mapping_package_folder_path: Path):
    """Dynamically load a mapping package based on version."""
    if from_version == V2:
        loader = MappingPackageV2Loader()
        return load_mapping_package_v2_from_folder(
            mapping_package_folder_path=mapping_package_folder_path,
            mapping_package_loader=loader
        )
    elif from_version == V3:
        loader = MappingPackageV3Loader()
        return load_mapping_package_v3_from_folder(
            mapping_package_folder_path=mapping_package_folder_path,
            mapping_package_loader=loader
        )
    else:
        raise typer.BadParameter(f"Unsupported source version: {from_version}")


def _convert_mapping_package(from_version: str, to_version: str, source_package):
    """Convert mapping package using service layer."""
    if from_version == V2 and to_version == V3:
        return convert_mpv3_from_mpv2(source_package)
    elif from_version == V3 and to_version == V3_LIGHTWEIGHT:
        return convert_mpv3_lightweight_from_mpv3(source_package)
    else:
        raise typer.BadParameter(f"Unsupported conversion: {from_version} -> {to_version}")


def _serialise_mapping_package(to_version: str, mapping_package_folder_path: Path, converted_package):
    """Dynamically serialize a mapping package based on version."""
    if to_version == V3:
        serialiser = MappingPackageV3Serialiser()
        serialiser.serialise(mapping_package_folder_path, converted_package)
    elif to_version == V3_LIGHTWEIGHT:
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
        to_version: str = typer.Option(..., "--to-version", help=f"Target mapping package version ({V3} or {V3_LIGHTWEIGHT})"),
        from_version: str = typer.Option(..., "--from-version", help=f"Source mapping package version ({V2} or {V3})"),
        verbose: bool = typer.Option(False, "--verbose", "-v",
                                     is_eager=True,
                                     callback=typer_verbose_callback),
) -> None:
    """Set conversion version context."""
    if to_version not in [V3, V3_LIGHTWEIGHT]:
        raise typer.BadParameter(f"Target version must be {V3} or {V3_LIGHTWEIGHT}, got: {to_version}")

    if to_version == V3 and from_version != V2:
        raise typer.BadParameter(f"Source version must be {V2} for target {V3}, got: {from_version}")
    
    if to_version == V3_LIGHTWEIGHT and from_version != V3:
        raise typer.BadParameter(f"Source version must be {V3} for target {V3_LIGHTWEIGHT}, got: {from_version}")

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
    if _is_already_converted(mapping_package_path, to_version):
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

    converted_count = 0

    for mp_folder in folder_path.iterdir():
        if not mp_folder.is_dir():
            continue

        # Check if already converted
        if _is_already_converted(mp_folder, to_version):
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

    logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=folder_path,
        message=f"✅ All converted ({converted_count} converted)"))

