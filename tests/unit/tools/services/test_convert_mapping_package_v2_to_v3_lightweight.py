from unittest.mock import Mock, patch

from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3_lightweight import (
    convert_mapping_package_v2_to_v3_lightweight,
)


@patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3_lightweight.convert_mapping_package_v3_to_v3_lightweight")
@patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3_lightweight.convert_mapping_package_v2_to_v3")
def test_convert_mapping_package_v2_to_v3_lightweight_composes_converters(
    mock_convert_v2_to_v3,
    mock_convert_v3_to_v3l,
):
    mpv2 = Mock(spec=MappingPackageV2)
    mpv3 = Mock(spec=MappingPackageV3)
    mpv3l = Mock(spec=MappingPackageV3Lightweight)

    mock_convert_v2_to_v3.return_value = mpv3
    mock_convert_v3_to_v3l.return_value = mpv3l

    result = convert_mapping_package_v2_to_v3_lightweight(mpv2)

    assert result is mpv3l
    mock_convert_v2_to_v3.assert_called_once_with(mpv2)
    mock_convert_v3_to_v3l.assert_called_once_with(mpv3)

