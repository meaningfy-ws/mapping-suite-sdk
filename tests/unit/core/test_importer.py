import shutil
import tempfile
from pathlib import Path

from mssdk.core.adapters.importer import TechnicalMappingSuiteImporter, RELATIVE_TECHNICAL_MAPPING_SUITE_PATH, \
    ValueMappingSuiteImporter, RELATIVE_VALUE_MAPPING_SUITE_PATH


def _test_mapping_suite_importer(dummy_mapping_package_path: Path,
                                 importer_class,
                                 expected_relative_path: str) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        mapping_suite = importer_class().extract(temp_mp_path)

        assert mapping_suite is not None
        assert mapping_suite.path is not None
        assert mapping_suite.path == expected_relative_path
        assert (temp_mp_path / mapping_suite.path).exists()
        assert len(mapping_suite.files) > 0
        for file in mapping_suite.files:
            assert file is not None
            assert (temp_mp_path / file.path).exists()
            assert file.content is not None


def test_technical_mapping_suite_importer(dummy_mapping_package_path: Path) -> None:
    _test_mapping_suite_importer(
        dummy_mapping_package_path,
        TechnicalMappingSuiteImporter,
        RELATIVE_TECHNICAL_MAPPING_SUITE_PATH
    )


def test_value_mapping_suite_importer(dummy_mapping_package_path: Path) -> None:
    _test_mapping_suite_importer(
        dummy_mapping_package_path,
        ValueMappingSuiteImporter,
        RELATIVE_VALUE_MAPPING_SUITE_PATH
    )
