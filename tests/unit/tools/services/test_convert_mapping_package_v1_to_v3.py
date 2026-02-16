from datetime import datetime

import pytest

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_hasher import MappingPackageV3Hasher
from mapping_suite_sdk.tools.services.convert_mapping_package_v1_to_v3 import convert_mapping_package_v1_to_v3


def test_convert_mapping_package_v1_to_v3_maps_metadata_constraints_and_assets(dummy_mapping_package_v1_model: MappingPackageV1):
    mpv1 = dummy_mapping_package_v1_model

    # Make the test deterministic by overriding key inputs.
    mpv1.metadata.identifier = "package_F22"
    mpv1.metadata.title = "Package F22"
    mpv1.metadata.issue_date = "2023-06-13T19:31:37.496360"
    mpv1.metadata.mapping_version = "2.1.1"
    mpv1.metadata.ontology_version = "3.1.0"
    mpv1.metadata.description = "This is the conceptual mapping for Standard Form F22, all directives."
    mpv1.metadata.signature = "deadbeef"

    mpv1.metadata.metadata_constraints.constraints.eforms_subtype = [5, 13]
    mpv1.metadata.metadata_constraints.constraints.start_date = ["2014-01-01"]
    mpv1.metadata.metadata_constraints.constraints.end_date = []
    mpv1.metadata.metadata_constraints.constraints.min_xsd_version = ["R2.0.9.S01.E01"]
    mpv1.metadata.metadata_constraints.constraints.max_xsd_version = ["R2.0.9.S05.E01"]

    result = convert_mapping_package_v1_to_v3(mpv1)

    assert isinstance(result, MappingPackageV3)

    # Metadata mapping
    assert result.metadata.path == mssdk_config.MPV3_METADATA_FILE_ASSET_PATH
    assert result.metadata.context == "context.jsonld"
    assert result.metadata.id == "package_F22"
    assert result.metadata.title == "Package F22"
    assert result.metadata.project_identifier == "standard_forms"
    assert result.metadata.mapping_version == "2.1.1"
    assert result.metadata.model_version == "3.1.0"
    # Hash should be recomputed for the converted V3 package (should not carry over the V1 signature).
    assert result.metadata.mapping_suite_hash_digest != "deadbeef"
    assert result.metadata.mapping_suite_hash_digest == MappingPackageV3Hasher(result).hash()

    # Constraints mapping
    assert result.metadata.applicability_constraints is not None
    assert result.metadata.applicability_constraints.document_type_list == ["5", "13"]
    assert result.metadata.applicability_constraints.document_schema_version_list is None

    assert result.metadata.applicability_constraints.document_time_interval is not None
    assert result.metadata.applicability_constraints.document_time_interval.start is not None
    assert result.metadata.applicability_constraints.document_time_interval.start.date() == datetime.fromisoformat("2014-01-01").date()

    assert result.metadata.applicability_constraints.document_version_range is not None
    assert result.metadata.applicability_constraints.document_version_range.min == "R2.0.9.S01.E01"
    assert result.metadata.applicability_constraints.document_version_range.max == "R2.0.9.S05.E01"

    # Asset mapping: ensure we carried everything over (copied, not referenced)
    assert result.conceptual_mapping_asset == mpv1.conceptual_mapping_asset
    assert result.conceptual_mapping_asset is not mpv1.conceptual_mapping_asset
    assert result.technical_mapping_suite == mpv1.technical_mapping_suite
    assert result.technical_mapping_suite is not mpv1.technical_mapping_suite
    assert result.vocabulary_mapping_suite == mpv1.vocabulary_mapping_suite
    assert result.vocabulary_mapping_suite is not mpv1.vocabulary_mapping_suite

    assert result.test_data_suites == mpv1.test_data_suites
    assert result.test_data_suites is not mpv1.test_data_suites
    assert result.test_suites_sparql == mpv1.test_suites_sparql
    assert result.test_suites_sparql is not mpv1.test_suites_sparql

    assert result.test_suites_shacl == mpv1.test_suites_shacl
    assert result.test_suites_shacl is not mpv1.test_suites_shacl
    assert result.test_results == mpv1.test_results
    assert result.test_results is not mpv1.test_results


def test_convert_mapping_package_v1_to_v3_fails_with_invalid_input() -> None:
    with pytest.raises((TypeError, AttributeError, ValueError)):
        convert_mapping_package_v1_to_v3(None)  # type: ignore[arg-type]


def test_convert_mapping_package_v1_to_v3_fails_with_invalid_issue_date(dummy_mapping_package_v1_model: MappingPackageV1) -> None:
    dummy_mapping_package_v1_model.metadata.issue_date = "invalid-date-format"
    with pytest.raises((ValueError, TypeError)):
        convert_mapping_package_v1_to_v3(dummy_mapping_package_v1_model)


def test_convert_mapping_package_v1_to_v3_fails_with_invalid_start_date(dummy_mapping_package_v1_model: MappingPackageV1) -> None:
    dummy_mapping_package_v1_model.metadata.metadata_constraints.constraints.start_date = ["invalid-date-format"]
    dummy_mapping_package_v1_model.metadata.metadata_constraints.constraints.end_date = []
    with pytest.raises((ValueError, TypeError)):
        convert_mapping_package_v1_to_v3(dummy_mapping_package_v1_model)


def test_convert_mapping_package_v1_to_v3_fails_with_invalid_end_date(dummy_mapping_package_v1_model: MappingPackageV1) -> None:
    dummy_mapping_package_v1_model.metadata.metadata_constraints.constraints.start_date = []
    dummy_mapping_package_v1_model.metadata.metadata_constraints.constraints.end_date = ["invalid-date-format"]
    with pytest.raises((ValueError, TypeError)):
        convert_mapping_package_v1_to_v3(dummy_mapping_package_v1_model)


def test_convert_mapping_package_v1_to_v3_empty_date_lists_result_in_no_interval(dummy_mapping_package_v1_model: MappingPackageV1) -> None:
    dummy_mapping_package_v1_model.metadata.metadata_constraints.constraints.start_date = []
    dummy_mapping_package_v1_model.metadata.metadata_constraints.constraints.end_date = []

    result = convert_mapping_package_v1_to_v3(dummy_mapping_package_v1_model)

    assert isinstance(result, MappingPackageV3)
    assert result.metadata.applicability_constraints is not None
    assert result.metadata.applicability_constraints.document_time_interval is None


def test_convert_mapping_package_v1_to_v3_only_start_date_creates_open_interval(dummy_mapping_package_v1_model: MappingPackageV1) -> None:
    dummy_mapping_package_v1_model.metadata.metadata_constraints.constraints.start_date = ["2014-01-01"]
    dummy_mapping_package_v1_model.metadata.metadata_constraints.constraints.end_date = []

    result = convert_mapping_package_v1_to_v3(dummy_mapping_package_v1_model)

    assert isinstance(result, MappingPackageV3)
    assert result.metadata.applicability_constraints is not None
    assert result.metadata.applicability_constraints.document_time_interval is not None
    assert result.metadata.applicability_constraints.document_time_interval.start is not None
    assert result.metadata.applicability_constraints.document_time_interval.end is None


def test_convert_mapping_package_v1_to_v3_only_end_date_creates_open_interval(dummy_mapping_package_v1_model: MappingPackageV1) -> None:
    dummy_mapping_package_v1_model.metadata.metadata_constraints.constraints.start_date = []
    dummy_mapping_package_v1_model.metadata.metadata_constraints.constraints.end_date = ["2014-12-31"]

    result = convert_mapping_package_v1_to_v3(dummy_mapping_package_v1_model)

    assert isinstance(result, MappingPackageV3)
    assert result.metadata.applicability_constraints is not None
    assert result.metadata.applicability_constraints.document_time_interval is not None
    assert result.metadata.applicability_constraints.document_time_interval.start is None
    assert result.metadata.applicability_constraints.document_time_interval.end is not None


def test_convert_mapping_package_v1_to_v3_empty_subtypes_kept_as_empty_list(dummy_mapping_package_v1_model: MappingPackageV1) -> None:
    dummy_mapping_package_v1_model.metadata.metadata_constraints.constraints.eforms_subtype = []

    result = convert_mapping_package_v1_to_v3(dummy_mapping_package_v1_model)

    assert isinstance(result, MappingPackageV3)
    assert result.metadata.applicability_constraints is not None
    assert result.metadata.applicability_constraints.document_type_list == []


def test_convert_mapping_package_v1_to_v3_empty_xsd_versions_result_in_no_version_range(dummy_mapping_package_v1_model: MappingPackageV1) -> None:
    dummy_mapping_package_v1_model.metadata.metadata_constraints.constraints.min_xsd_version = []
    dummy_mapping_package_v1_model.metadata.metadata_constraints.constraints.max_xsd_version = []

    result = convert_mapping_package_v1_to_v3(dummy_mapping_package_v1_model)

    assert isinstance(result, MappingPackageV3)
    assert result.metadata.applicability_constraints is not None
    assert result.metadata.applicability_constraints.document_version_range is None
