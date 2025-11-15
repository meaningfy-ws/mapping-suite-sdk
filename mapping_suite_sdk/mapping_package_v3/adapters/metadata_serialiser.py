from pathlib import Path

from mapping_suite_sdk.core.adapters.serialiser import MappingPackageAssetSerialiser
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata_jsonld import \
    MappingPackageV3MetadataJSONLD
from mapping_suite_sdk.core.models.pydantic import fields


class MappingPackageV3MetadataSerialiser(MappingPackageAssetSerialiser):
    """
    Serialiser for mapping package metadata.

    Always writes JSON-LD format with @context referencing sibling context.jsonld file.
    """

    def serialise(self, package_folder_path: Path, asset: MappingPackageV3MetadataJSONLD) -> None:
        metadata_path = package_folder_path / asset.path
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure @context references sibling context.jsonld
        if not asset.context:
            asset.context = "context.jsonld"

        # Serialize as JSON-LD (with @context) using the JSONLD model directly
        # Exclude 'path' field: it's an internal SDK concern for tracking file location
        # within the package structure, not part of the serialized metadata content.
        # This is consistent with V1 and V2 serializers.
        # TODO: Consider refactoring to handle path separately from the domain model
        # if this pattern becomes problematic (e.g., via a separate metadata wrapper
        # or computed property approach).
        metadata_path.write_text(asset.model_dump_json(
            by_alias=True,  # Use @context instead of context
            exclude_none=True,
            exclude={fields(MappingPackageV3MetadataJSONLD).path},
            indent=4
        ))