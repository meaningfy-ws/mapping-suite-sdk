import shutil
import tempfile
from pathlib import Path

from mssdk.core.adapters.importer import TechnicalMappingSuiteImporter, RELATIVE_TECHNICAL_MAPPING_PATH
from mssdk.core.models.files import TechnicalMappingSuite


def test_technical_mapping_suite_importer(dummy_mapping_package_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        tm_importer = TechnicalMappingSuiteImporter()
        tm: TechnicalMappingSuite = tm_importer.extract(temp_mp_path)

        assert tm is not None
        assert tm.path is not None
        assert tm.path == RELATIVE_TECHNICAL_MAPPING_PATH
        assert (temp_mp_path / tm.path).exists()
        assert len(tm.files) > 0
        for file in tm.files:
            assert file is not None
            assert (temp_mp_path / file.path).exists()

            assert file.content is not None
