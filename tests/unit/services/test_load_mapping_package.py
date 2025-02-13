import shutil
import tempfile
from pathlib import Path

import pytest

from mssdk.adapters.loader import MappingPackageLoader
from mssdk.models.mapping_package import MappingPackage
from mssdk.services.load_mapping_package import load_mapping_package_from_folder, load_mapping_package_from_zip_file
from tests.conftest import assert_valid_mapping_package


def test_load_mapping_package_from_folder(dummy_mapping_package_path: Path):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path: Path = Path(temp_dir)

        random_file: Path = (temp_dir_path / "tmp_file.txt")
        random_file.touch()

        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        with pytest.raises(FileNotFoundError):
            load_mapping_package_from_folder(mapping_package_folder_path=Path("/non/existing/path"))
        with pytest.raises(ValueError):
            load_mapping_package_from_folder(mapping_package_folder_path=random_file)

        mapping_package: MappingPackage = load_mapping_package_from_folder(mapping_package_folder_path=temp_mp_path)

        assert_valid_mapping_package(mapping_package=mapping_package)

        mapping_package: MappingPackage = load_mapping_package_from_folder(mapping_package_folder_path=temp_mp_path,
                                                                           mapping_package_loader=MappingPackageLoader())

        assert_valid_mapping_package(mapping_package=mapping_package)


def test_load_mapping_package_from_zip_file(dummy_mapping_package_path: Path):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path: Path = Path(temp_dir)

        random_folder: Path = (temp_dir_path / "tmp_folder")
        random_folder.mkdir(exist_ok=True)

        with pytest.raises(ValueError):
            load_mapping_package_from_zip_file(mapping_package_zip_path=random_folder)

    with pytest.raises(FileNotFoundError):
        load_mapping_package_from_zip_file(mapping_package_zip_path=Path("/non/existing/path"))

    mapping_package: MappingPackage = load_mapping_package_from_zip_file(
        mapping_package_zip_path=dummy_mapping_package_path)

    assert_valid_mapping_package(mapping_package=mapping_package)

    mapping_package: MappingPackage = load_mapping_package_from_zip_file(
        mapping_package_zip_path=dummy_mapping_package_path,
        mapping_package_loader=MappingPackageLoader())

    assert_valid_mapping_package(mapping_package=mapping_package)
