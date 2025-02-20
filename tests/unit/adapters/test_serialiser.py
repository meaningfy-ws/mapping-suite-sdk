import shutil
import tempfile
from pathlib import Path

from mapping_suite_sdk.adapters.serialiser import MappingPackageSerialiser
from mapping_suite_sdk.models.mapping_package import MappingPackage
from tests.conftest import _compare_directories


def test_serialiser_generates_same_output(dummy_mapping_package_model: MappingPackage,
                                          dummy_mapping_package_path: Path):
    with tempfile.TemporaryDirectory() as temp_directory:
        temp_directory_path = Path(temp_directory)

        serialised_folder_path: Path = temp_directory_path / "serialised_path"
        serialised_folder_path.mkdir(parents=False, exist_ok=True)

        temp_mp_path = temp_directory_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir(parents=False, exist_ok=True)

        shutil.unpack_archive(dummy_mapping_package_path, temp_mp_path)

        MappingPackageSerialiser().serialize(serialised_folder_path, dummy_mapping_package_model)

        is_equal, error_message = _compare_directories(serialised_folder_path, temp_mp_path)
        assert is_equal, f"Directory comparison failed:\n{error_message}"
