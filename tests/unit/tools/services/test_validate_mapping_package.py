from pathlib import Path
from unittest.mock import patch

import pytest

from mapping_suite_sdk.core.adapters.validator import MPValidationException
from mapping_suite_sdk.tools.services.convert_mapping_package import Version
from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import (
    convert_mapping_package_v3_to_v3_lightweight,
)
from mapping_suite_sdk.tools.services.validate_mapping_package import (
    CrossVersionValidationError,
    _normalize_version,
    _validate_folder_from_path,
    _validate_model,
    _detect_version_from_model,
    validate_mapping_package,
)


def test_validate_mapping_package_auto_detects_version_for_folder_path(tmp_path: Path) -> None:
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version", return_value=Version.V2) as mock_detect,
        patch("mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2.validate_mapping_package_v2_from_folder", return_value=True) as mock_v2,
    ):
        assert validate_mapping_package(tmp_path) is True
        mock_detect.assert_called_once_with(tmp_path)
        mock_v2.assert_called_once_with(mapping_package_folder_path=tmp_path)


def test_validate_mapping_package_explicit_version_skips_detection_for_folder_path(tmp_path: Path) -> None:
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch("mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3_from_folder", return_value=True) as mock_v3,
    ):
        assert validate_mapping_package(tmp_path, version="v3") is True
        mock_detect.assert_not_called()
        mock_v3.assert_called_once_with(mapping_package_folder_path=tmp_path)


def test_validate_mapping_package_raises_clear_error_for_unknown_version(tmp_path: Path) -> None:
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version", return_value=None),
    ):
        with pytest.raises(CrossVersionValidationError, match="Unknown or unsupported mapping package version"):
            validate_mapping_package(tmp_path)


def test_validate_mapping_package_archive_does_not_wrap_validation_errors(tmp_path: Path) -> None:
    archive_path = tmp_path / "mp.zip"
    archive_path.write_text("dummy")  # just needs to exist as a file for this test

    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.ArchiveExtractor.extract", return_value=tmp_path / "extracted") as mock_extract,
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version", return_value=Version.V3L),
        patch(
            "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3_lightweight.validate_mapping_package_v3_lightweight_from_folder",
            side_effect=MPValidationException("Hash validation failed"),
        ),
    ):
        with pytest.raises(MPValidationException, match="Hash validation failed"):
            validate_mapping_package(archive_path)
        mock_extract.assert_called_once()


def test_validate_mapping_package_auto_detects_version_from_model_type(dummy_mapping_package_v1_model) -> None:
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch("mapping_suite_sdk.mapping_package_v1.services.validate_mapping_package_v1.validate_mapping_package_v1", return_value=True) as mock_v1,
    ):
        assert validate_mapping_package(dummy_mapping_package_v1_model) is True
        mock_detect.assert_not_called()
        mock_v1.assert_called_once()


def test_validate_mapping_package_explicit_version_skips_detection_for_model(fixture_mapping_package_v3_model) -> None:
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch("mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3", return_value=True) as mock_v3,
    ):
        assert validate_mapping_package(fixture_mapping_package_v3_model, version="v3") is True
        mock_detect.assert_not_called()
        mock_v3.assert_called_once()


# --- _normalize_version ---


def test_normalize_version_strips_whitespace() -> None:
    assert _normalize_version("  v1  ") == Version.V1


def test_normalize_version_lowercases() -> None:
    assert _normalize_version("V1") == Version.V1
    assert _normalize_version("V2") == Version.V2
    assert _normalize_version("V3") == Version.V3


def test_normalize_version_v3l_to_v3L() -> None:
    assert _normalize_version("v3l") == Version.V3L
    assert _normalize_version("V3L") == Version.V3L
    assert _normalize_version("  v3l  ") == Version.V3L


def test_normalize_version_raises_on_invalid_version() -> None:
    with pytest.raises(CrossVersionValidationError, match="Unsupported version: v99"):
        _normalize_version("v99")


# --- _validate_model ---


def test_validate_model_v1_calls_v1_validator(dummy_mapping_package_v1_model) -> None:
    with patch(
        "mapping_suite_sdk.mapping_package_v1.services.validate_mapping_package_v1.validate_mapping_package_v1",
        return_value=True,
    ) as mock_v1:
        assert _validate_model(dummy_mapping_package_v1_model, Version.V1) is True
        mock_v1.assert_called_once_with(mapping_package=dummy_mapping_package_v1_model)


def test_validate_model_v1_raises_on_wrong_type(fixture_mapping_package_v3_model) -> None:
    with pytest.raises(CrossVersionValidationError, match="Version 'v1' requires MappingPackageV1"):
        _validate_model(fixture_mapping_package_v3_model, Version.V1)


def test_validate_model_v2_calls_v2_validator(dummy_mapping_package_v2_model) -> None:
    with patch(
        "mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2.validate_mapping_package_v2",
        return_value=True,
    ) as mock_v2:
        assert _validate_model(dummy_mapping_package_v2_model, Version.V2) is True
        mock_v2.assert_called_once_with(mapping_package=dummy_mapping_package_v2_model)


def test_validate_model_v2_raises_on_wrong_type(dummy_mapping_package_v1_model) -> None:
    with pytest.raises(CrossVersionValidationError, match="Version 'v2' requires MappingPackageV2"):
        _validate_model(dummy_mapping_package_v1_model, Version.V2)


def test_validate_model_v3_calls_v3_validator(fixture_mapping_package_v3_model) -> None:
    with patch(
        "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3",
        return_value=True,
    ) as mock_v3:
        assert _validate_model(fixture_mapping_package_v3_model, Version.V3) is True
        mock_v3.assert_called_once_with(mapping_package=fixture_mapping_package_v3_model)


def test_validate_model_v3_raises_on_wrong_type(dummy_mapping_package_v1_model) -> None:
    with pytest.raises(CrossVersionValidationError, match="Version 'v3' requires MappingPackageV3"):
        _validate_model(dummy_mapping_package_v1_model, Version.V3)


def test_validate_model_v3L_calls_v3_lightweight_validator(
    fixture_mapping_package_v3_model,
) -> None:
    v3l_model = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    with patch(
        "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3_lightweight.validate_mapping_package_v3_lightweight",
        return_value=True,
    ) as mock_v3l:
        assert _validate_model(v3l_model, Version.V3L) is True
        mock_v3l.assert_called_once_with(mapping_package=v3l_model)


def test_validate_model_v3L_raises_on_wrong_type(fixture_mapping_package_v3_model) -> None:
    with pytest.raises(
        CrossVersionValidationError,
        match="Version 'v3L' requires MappingPackageV3Lightweight",
    ):
        _validate_model(fixture_mapping_package_v3_model, Version.V3L)


# --- _validate_folder_from_path ---


def test_validate_folder_from_path_v1_calls_v1_from_folder(tmp_path: Path) -> None:
    with patch(
        "mapping_suite_sdk.mapping_package_v1.services.validate_mapping_package_v1.validate_mapping_package_v1_from_folder",
        return_value=True,
    ) as mock_v1:
        assert _validate_folder_from_path(tmp_path, Version.V1) is True
        mock_v1.assert_called_once_with(mapping_package_folder_path=tmp_path)


def test_validate_folder_from_path_v2_calls_v2_from_folder(tmp_path: Path) -> None:
    with patch(
        "mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2.validate_mapping_package_v2_from_folder",
        return_value=True,
    ) as mock_v2:
        assert _validate_folder_from_path(tmp_path, Version.V2) is True
        mock_v2.assert_called_once_with(mapping_package_folder_path=tmp_path)


def test_validate_folder_from_path_v3_calls_v3_from_folder(tmp_path: Path) -> None:
    with patch(
        "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3_from_folder",
        return_value=True,
    ) as mock_v3:
        assert _validate_folder_from_path(tmp_path, Version.V3) is True
        mock_v3.assert_called_once_with(mapping_package_folder_path=tmp_path)


def test_validate_folder_from_path_v3L_calls_v3_lightweight_from_folder(tmp_path: Path) -> None:
    with patch(
        "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3_lightweight.validate_mapping_package_v3_lightweight_from_folder",
        return_value=True,
    ) as mock_v3l:
        assert _validate_folder_from_path(tmp_path, Version.V3L) is True
        mock_v3l.assert_called_once_with(mapping_package_folder_path=tmp_path)


# --- _detect_version_from_model ---


def test_detect_version_from_model_v1(dummy_mapping_package_v1_model) -> None:
    assert _detect_version_from_model(dummy_mapping_package_v1_model) == Version.V1


def test_detect_version_from_model_v2(dummy_mapping_package_v2_model) -> None:
    assert _detect_version_from_model(dummy_mapping_package_v2_model) == Version.V2


def test_detect_version_from_model_v3(fixture_mapping_package_v3_model) -> None:
    assert _detect_version_from_model(fixture_mapping_package_v3_model) == Version.V3


def test_detect_version_from_model_v3L(fixture_mapping_package_v3_model) -> None:
    v3l_model = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    assert _detect_version_from_model(v3l_model) == Version.V3L


def test_detect_version_from_model_raises_for_unknown_type() -> None:
    with pytest.raises(CrossVersionValidationError, match="Cannot auto-detect version"):
        _detect_version_from_model("not a package")


# --- validate_mapping_package: archive + unknown version ---


def test_validate_mapping_package_archive_raises_clear_error_for_unknown_version(tmp_path: Path) -> None:
    archive_path = tmp_path / "mp.zip"
    archive_path.write_text("dummy")

    with (
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.ArchiveExtractor.extract",
            return_value=tmp_path / "extracted",
        ),
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version",
            return_value=None,
        ),
    ):
        with pytest.raises(CrossVersionValidationError, match="Unknown or unsupported mapping package version"):
            validate_mapping_package(archive_path)


# --- validate_mapping_package: auto-detect from model type ---


def test_validate_mapping_package_auto_detects_v2_from_model_type(dummy_mapping_package_v2_model) -> None:
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch(
            "mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2.validate_mapping_package_v2",
            return_value=True,
        ) as mock_v2,
    ):
        assert validate_mapping_package(dummy_mapping_package_v2_model) is True
        mock_detect.assert_not_called()
        mock_v2.assert_called_once_with(mapping_package=dummy_mapping_package_v2_model)


def test_validate_mapping_package_auto_detects_v3L_from_model_type(
    fixture_mapping_package_v3_model,
) -> None:
    v3l_model = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch(
            "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3_lightweight.validate_mapping_package_v3_lightweight",
            return_value=True,
        ) as mock_v3l,
    ):
        assert validate_mapping_package(v3l_model) is True
        mock_detect.assert_not_called()
        mock_v3l.assert_called_once_with(mapping_package=v3l_model)


def test_validate_mapping_package_auto_detects_v3_from_model_type(fixture_mapping_package_v3_model) -> None:
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch(
            "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3",
            return_value=True,
        ) as mock_v3,
    ):
        assert validate_mapping_package(fixture_mapping_package_v3_model) is True
        mock_detect.assert_not_called()
        mock_v3.assert_called_once_with(mapping_package=fixture_mapping_package_v3_model)


def test_validate_mapping_package_raises_when_model_type_unknown() -> None:
    with pytest.raises(
        CrossVersionValidationError,
        match="Cannot auto-detect version from mapping package type",
    ):
        validate_mapping_package("not a package")
