from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import MappingPackageV2Metadata
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import MappingPackageV3Metadata


def create_mpv3_from_mpv2(mpv2: MappingPackageV2) -> MappingPackageV3:
    """
    Convert a MappingPackageV2 to MappingPackageV3.
    """
    mpv2_metadata: MappingPackageV2Metadata = mpv2.metadata
    return MappingPackageV3(

        #TODO: Fulfill remaining fields
        metadata=MappingPackageV3Metadata(
            path=mpv2_metadata.path,

            id=mpv2_metadata.identifier,
            title=mpv2_metadata.title,
            project_identifier=mpv2_metadata.mapping_type,
            created_at=mpv2_metadata.issue_date,
            mapping_version=mpv2_metadata.mapping_version,
            model_version=mpv2_metadata.ontology_version,
            description=mpv2_metadata.description,
            applicability_constraints=mpv2_metadata.metadata_constraints.constraints,
            mapping_suite_hash_digest=mpv2_metadata.signature,
        ),

        #TODO: Look if the structure of this assets are the same
        conceptual_mapping_asset=mpv2.conceptual_mapping_asset.model_copy(),
        technical_mapping_suite=mpv2.technical_mapping_suite.model_copy(),
        vocabulary_mapping_suite=mpv2.vocabulary_mapping_suite.model_copy(),
        test_data_suites=mpv2.test_data_suites.copy(),
        test_suites_sparql=mpv2.test_suites_sparql.copy(),
        test_suites_shacl=mpv2.test_suites_shacl.model_copy(),
        test_results=mpv2.test_results.model_copy()
    )
