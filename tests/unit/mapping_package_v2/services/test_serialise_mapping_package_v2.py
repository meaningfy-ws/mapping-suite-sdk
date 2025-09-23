import filecmp
import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk import MappingPackageV2, serialise_mapping_package_v2


# def test_serialise_mapping_package_successful_serialisation(dummy_mapping_package_v1_model: MappingPackageV1,
#                                                             dummy_mapping_package_v1_path: Path):
#     with tempfile.TemporaryDirectory() as temp_directory:
#         temp_directory_path = Path(temp_directory)
#         temp_archive_path = temp_directory_path / "serialised.zip"
#         serialise_mapping_package_v1(
#             mapping_package=dummy_mapping_package_v1_model,
#             serialisation_folder_path=temp_archive_path,
#         )
#
#         assert temp_archive_path.exists()
#
#         extracted_path: Path = temp_directory_path / temp_archive_path.stem
#         shutil.unpack_archive(temp_archive_path, extracted_path)
#
#         is_equal, error_message = _compare_directories(dummy_mapping_package_v1_path, extracted_path)
#         assert is_equal, f"Directory comparison failed:\n{error_message}"


def test_serialise_mapping_package_v2_service_failure_leaves_output_untouched(
        dummy_mapping_package_v2_model: MappingPackageV2,
        dummy_mapping_package_v2_path: Path):
    with tempfile.TemporaryDirectory() as temp_directory:
        temp_directory_path = Path(temp_directory)
        temp_archive_path = temp_directory_path / "serialised.zip"
        temp_archive_path.touch()
        temp_archive_copy_path = temp_directory_path / "serialised_copy.zip"
        temp_archive_copy_path.touch()
        with pytest.raises(AttributeError):
            serialise_mapping_package_v2(
                mapping_package=None,
                serialisation_folder_path=temp_archive_path,
            )
        assert filecmp.cmp(temp_archive_path, temp_archive_copy_path)
