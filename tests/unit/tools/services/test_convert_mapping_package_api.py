"""public-api: convert a loaded package to another version (convert_mapping_package)."""

import pytest

from mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2 import load_mapping_package_v2_from_folder
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.tools.services.convert_mapping_package import (
    UnsupportedConversionError,
    UnsupportedVersionError,
    VersionDetectionError,
    convert_mapping_package,
    convert_mapping_package_model,
)
from mapping_suite_sdk.tools.services.load_mapping_package import load_mapping_package
from tests import TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_FOLDER_PATH, TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH


def _v2_package():
    return load_mapping_package_v2_from_folder(TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_FOLDER_PATH)


def test_v2_to_v3():
    result = convert_mapping_package(_v2_package())

    assert isinstance(result, MappingPackageV3)
    assert result == convert_mapping_package_model("v2", "v3", _v2_package())


def test_same_version_returns_the_package_unchanged():
    package = convert_mapping_package(_v2_package(), "v3")

    assert convert_mapping_package(package, to_version="v3") is package


def test_lightweight_cannot_become_full():
    lightweight = load_mapping_package(TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH)

    with pytest.raises(UnsupportedConversionError):
        convert_mapping_package(lightweight, to_version="v3")


def test_not_a_mapping_package():
    with pytest.raises(VersionDetectionError):
        convert_mapping_package({"not": "a package"})


@pytest.mark.parametrize("to_version", ["v4", "v1", "v2"])
def test_unknown_target_version(to_version):
    with pytest.raises(UnsupportedVersionError):
        convert_mapping_package(_v2_package(), to_version=to_version)
