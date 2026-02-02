from unittest.mock import Mock, patch

from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3_lightweight import (
    convert_mapping_package_v2_to_v3_lightweight,
)


@patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3_lightweight.convert_mapping_package_v3_to_v3_lightweight")
@patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3_lightweight.convert_mapping_package_v2_to_v3")
@patch("mapping_suite_sdk.tools.services.convert_mapping_package_v2_to_v3_lightweight.MappingPackageV3Hasher")
def test_convert_mapping_package_v2_to_v3_lightweight_composes_converters(
    mock_hasher_cls,
    mock_convert_v2_to_v3,
    mock_convert_v3_to_v3l,
):
    """Test that V2 to V3L conversion composes the V2->V3 and V3->V3L converters and recomputes the hash."""
    mpv2 = Mock(spec=MappingPackageV2)
    mpv3 = Mock(spec=MappingPackageV3)
    mpv3l = Mock(spec=MappingPackageV3Lightweight)
    mpv3l.metadata = Mock()

    mock_convert_v2_to_v3.return_value = mpv3
    mock_convert_v3_to_v3l.return_value = mpv3l
    mock_hasher_cls.return_value.hash.return_value = "new_hash"

    result = convert_mapping_package_v2_to_v3_lightweight(mpv2)

    assert result is mpv3l
    mock_convert_v2_to_v3.assert_called_once_with(mpv2)
    mock_convert_v3_to_v3l.assert_called_once_with(mpv3)
    mock_hasher_cls.assert_called_once_with(mpv3l)
    mock_hasher_cls.return_value.hash.assert_called_once_with()
    assert mpv3l.metadata.mapping_suite_hash_digest == "new_hash"

