import shutil
import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk.core.adapters.loader import (
    TechnicalMappingSuiteLoader,
    VocabularyMappingSuiteLoader,
    TestDataSuitesLoader,
    SPARQLTestSuitesLoader,
    SHACLTestSuitesLoader,
    TestResultSuiteLoader,
    ConceptualMappingFileLoader, load_file_by_extensions
)
from mapping_suite_sdk.core.models.collection_asset import (
    TechnicalMappingCollectionAsset,
    VocabularyMappingCollectionAsset,
    TestDataCollectionAsset,
    SPARQLTestCollectionAsset,
    SHACLTestCollectionAsset,
    TestResultCollectionAsset
)
from mapping_suite_sdk.core.models.file_asset import (
    RMLMappingFileAsset,
    VocabularyMappingFileAsset,
    TestDataFileAsset,
    SPARQLQueryFileAsset,
    SHACLShapesFileAsset,
    ConceptualMappingFileAsset
)


def test_load_file_by_extensions(tmp_path: Path):
    """Test the load_file_by_extensions function with various file types."""

    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    text_file = test_dir / "test.txt"
    text_file.write_text("This is a text file")

    binary_file = test_dir / "test.bin"
    binary_file.write_bytes(b'\x00\x01\x02\x03')

    unsupported_file = test_dir / "test.unknown"
    unsupported_file.write_text("This has an unsupported extension")

    str_extensions = (".txt", ".html", ".json")
    bytes_extensions = (".bin", ".zip")

    text_content = load_file_by_extensions(text_file, str_extensions, bytes_extensions)
    assert isinstance(text_content, str)
    assert text_content == "This is a text file"

    binary_content = load_file_by_extensions(binary_file, str_extensions, bytes_extensions)
    assert isinstance(binary_content, bytes)
    assert binary_content == b'\x00\x01\x02\x03'

    unsupported_content = load_file_by_extensions(unsupported_file, str_extensions, bytes_extensions)
    assert unsupported_content is None

    non_existent_file = test_dir / "non_existent.txt"
    non_existent_content = load_file_by_extensions(non_existent_file, str_extensions, bytes_extensions)
    assert non_existent_content is None


def test_technical_mapping_suite_loader(dummy_mapping_package_path: Path,
                                        dummy_mapping_package_technical_collection_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)
        temp_mp_path = temp_mp_path / dummy_mapping_package_path.stem

        loader = TechnicalMappingSuiteLoader()
        mapping_suite = loader.load(temp_mp_path, dummy_mapping_package_technical_collection_path)

        assert isinstance(mapping_suite, TechnicalMappingCollectionAsset)
        assert any(isinstance(file, RMLMappingFileAsset) for file in mapping_suite.files)
        assert mapping_suite.path is not None
        assert (temp_mp_path / mapping_suite.path).exists()
        assert len(mapping_suite.files) > 0

        for file in mapping_suite.files:
            assert file is not None
            assert isinstance(file, RMLMappingFileAsset)
            assert (temp_mp_path / file.path).exists()
            assert file.content is not None


def test_technical_mapping_suite_loader_with_root_folder(dummy_mapping_package_path: Path,
                                                         dummy_mapping_package_technical_collection_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        # Create root folder structure
        root_folder = temp_mp_path / temp_mp_path.name
        if root_folder.exists():
            loader = TechnicalMappingSuiteLoader()
            mapping_suite = loader.load(package_folder_path=temp_mp_path,
                                        relative_asset_path=dummy_mapping_package_technical_collection_path)

            assert isinstance(mapping_suite, TechnicalMappingCollectionAsset)
            assert mapping_suite.path is not None


def test_vocabulary_mapping_suite_loader(dummy_mapping_package_path: Path,
                                         dummy_mapping_package_vocabulary_collection_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)
        temp_mp_path = temp_mp_path / dummy_mapping_package_path.stem

        loader = VocabularyMappingSuiteLoader()
        mapping_suite = loader.load(package_folder_path=temp_mp_path,
                                    relative_asset_path=dummy_mapping_package_vocabulary_collection_path)

        assert isinstance(mapping_suite, VocabularyMappingCollectionAsset)
        assert mapping_suite.path is not None
        assert (temp_mp_path / mapping_suite.path).exists()
        assert len(mapping_suite.files) > 0

        for file in mapping_suite.files:
            assert file is not None
            assert isinstance(file, VocabularyMappingFileAsset)
            assert (temp_mp_path / file.path).exists()
            assert file.content is not None


def test_test_data_suites_loader(dummy_mapping_package_path: Path,
                                 dummy_mapping_package_test_data_collection_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)
        temp_mp_path = temp_mp_path / dummy_mapping_package_path.stem

        loader = TestDataSuitesLoader()
        test_data_suites = loader.load(package_folder_path=temp_mp_path,
                                       relative_asset_path=dummy_mapping_package_test_data_collection_path)

        assert isinstance(test_data_suites, list)
        assert len(test_data_suites) > 0

        for suite in test_data_suites:
            assert isinstance(suite, TestDataCollectionAsset)
            assert suite.path is not None
            assert (temp_mp_path / suite.path).exists()
            assert len(suite.files) > 0

            for file in suite.files:
                assert isinstance(file, TestDataFileAsset)
                assert (temp_mp_path / file.path).exists()
                assert file.content is not None


def test_sparql_test_suites_loader(dummy_mapping_package_path: Path,
                                   dummy_mapping_package_sparql_collection_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)
        temp_mp_path = temp_mp_path / dummy_mapping_package_path.stem

        loader = SPARQLTestSuitesLoader()
        sparql_suites = loader.load(package_folder_path=temp_mp_path,
                                    relative_asset_path=dummy_mapping_package_sparql_collection_path)

        assert isinstance(sparql_suites, list)
        assert len(sparql_suites) > 0

        for suite in sparql_suites:
            assert isinstance(suite, SPARQLTestCollectionAsset)
            assert suite.path is not None
            assert (temp_mp_path / suite.path).exists()
            assert len(suite.files) > 0

            for file in suite.files:
                assert isinstance(file, SPARQLQueryFileAsset)
                assert (temp_mp_path / file.path).exists()
                assert file.content is not None


def test_shacl_test_suites_loader(dummy_mapping_package_path: Path,
                                  dummy_mapping_package_shacl_collection_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        loader = SHACLTestSuitesLoader()
        shacl_suite = loader.load(package_folder_path=temp_mp_path,
                                  relative_asset_path=dummy_mapping_package_shacl_collection_path)

        assert isinstance(shacl_suite, SHACLTestCollectionAsset)
        assert shacl_suite.shacl_result_query is not None
        assert shacl_suite.shacl_collections is not None
        assert len(shacl_suite.shacl_collections) > 0

        for collection in shacl_suite.shacl_collections:
            assert collection.path is not None
            assert (temp_mp_path / collection.path).exists()
            assert len(collection.files) > 0

            for file in collection.files:
                assert isinstance(file, SHACLShapesFileAsset)
                assert (temp_mp_path / file.path).exists()
                assert file.content is not None


def test_conceptual_mapping_file_loader(dummy_mapping_package_path: Path,
                                        dummy_mapping_package_conceptual_mapping_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)
        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)
        temp_mp_path = temp_mp_path / dummy_mapping_package_path.stem

        loader = ConceptualMappingFileLoader()
        cm_file = loader.load(package_folder_path=temp_mp_path,
                              relative_asset_path=dummy_mapping_package_conceptual_mapping_path)

        assert isinstance(cm_file, ConceptualMappingFileAsset)
        assert cm_file.path is not None
        assert (temp_mp_path / cm_file.path).exists()
        assert cm_file.content is not None
        assert len(cm_file.content) > 0


def test_test_result_suite_loader_with_valid_structure(dummy_mapping_test_result_collection_path: Path):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Create test structure
        output_dir = temp_dir_path / "output"
        output_dir.mkdir()

        # Create some test files
        (output_dir / "test_report.html").write_text("test report content")

        # Create test suite directory
        suite_dir = output_dir / "test_suite"
        suite_dir.mkdir()
        (suite_dir / "suite_report.json").write_text('{"test": "data"}')

        # Create test data result directory
        test_data_dir = suite_dir / "test_data_result"
        test_data_dir.mkdir()
        (test_data_dir / "result.ttl").write_text("test ttl content")

        test_report_dir = test_data_dir / "test_suite_report"
        test_report_dir.mkdir()
        (test_report_dir / "report.html").write_text("test report")

        loader = TestResultSuiteLoader()
        result = loader.load(temp_dir_path, dummy_mapping_test_result_collection_path)

        assert isinstance(result, TestResultCollectionAsset)


def test_loader_with_nonexistent_path():
    loader = TechnicalMappingSuiteLoader()

    with pytest.raises(FileNotFoundError):
        loader.load(Path("/nonexistent/path"), Path("/nonexistent/path"))


def test_loader_with_empty_directory(dummy_mapping_package_technical_collection_path: Path):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Create empty mapping directory structure
        mapping_dir = temp_dir_path / "transformation" / "mappings"
        mapping_dir.mkdir(parents=True)

        loader = TechnicalMappingSuiteLoader()
        result = loader.load(temp_dir_path, dummy_mapping_package_technical_collection_path)

        assert isinstance(result, TechnicalMappingCollectionAsset)
        assert len(result.files) == 0


def test_vocabulary_mapping_suite_loader_with_root_folder(dummy_mapping_package_path: Path,
                                                          dummy_mapping_package_vocabulary_collection_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        # Test with root folder structure
        root_folder = temp_mp_path / temp_mp_path.name
        if root_folder.exists():
            loader = VocabularyMappingSuiteLoader()
            mapping_suite = loader.load(temp_mp_path, dummy_mapping_package_vocabulary_collection_path)

            assert isinstance(mapping_suite, VocabularyMappingCollectionAsset)


def test_test_data_suites_loader_with_root_folder(dummy_mapping_package_path: Path,
                                                  dummy_mapping_package_test_data_collection_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        # Test with root folder structure
        root_folder = temp_mp_path / temp_mp_path.name
        if root_folder.exists():
            loader = TestDataSuitesLoader()
            test_data_suites = loader.load(temp_mp_path, dummy_mapping_package_test_data_collection_path)

            assert isinstance(test_data_suites, list)


def test_sparql_test_suites_loader_with_root_folder(dummy_mapping_package_path: Path,
                                                    dummy_mapping_package_sparql_collection_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        # Test with root folder structure
        root_folder = temp_mp_path / temp_mp_path.name
        if root_folder.exists():
            loader = SPARQLTestSuitesLoader()
            sparql_suites = loader.load(temp_mp_path, dummy_mapping_package_sparql_collection_path)

            assert isinstance(sparql_suites, list)


def test_shacl_test_suites_loader_with_root_folder(dummy_mapping_package_path: Path,
                                                   dummy_mapping_package_shacl_collection_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        # Test with root folder structure
        root_folder = temp_mp_path / temp_mp_path.name
        if root_folder.exists():
            loader = SHACLTestSuitesLoader()
            shacl_suite = loader.load(temp_mp_path, dummy_mapping_package_shacl_collection_path)

            assert isinstance(shacl_suite, SHACLTestCollectionAsset)


def test_conceptual_mapping_file_loader_with_root_folder(dummy_mapping_package_path: Path,
                                                         dummy_mapping_package_conceptual_mapping_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        # Test with root folder structure
        root_folder = temp_mp_path / temp_mp_path.name
        if root_folder.exists():
            loader = ConceptualMappingFileLoader()
            cm_file = loader.load(temp_mp_path, dummy_mapping_package_conceptual_mapping_path)

            assert isinstance(cm_file, ConceptualMappingFileAsset)
