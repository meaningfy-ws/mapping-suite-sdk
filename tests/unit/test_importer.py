import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path


from mssdk.adapters.loader import TechnicalMappingSuiteLoader, RELATIVE_TECHNICAL_MAPPING_SUITE_PATH, \
    VocabularyMappingSuiteLoader, RELATIVE_VALUE_MAPPING_SUITE_PATH, RELATIVE_TEST_DATA_PATH, TestDataSuitesLoader, \
    SPARQLTestSuitesLoader, RELATIVE_SPARQL_SUITE_PATH, SHACLTestSuitesLoader, RELATIVE_SHACL_SUITE_PATH, \
    MappingPackageMetadataLoader, RELATIVE_SUITE_METADATA_PATH, MappingPackageLoader, ConceptualMappingFileLoader, \
    RELATIVE_CONCEPTUAL_MAPPING_PATH
from mssdk.models.core import MSSDK_STR_MIN_LENGTH, MSSDK_STR_MAX_LENGTH, MSSDK_DEFAULT_STR_ENCODE
from mssdk.models.files import TechnicalMappingSuite, RMLMappingFile, YARRRMLMappingFile
from mssdk.models.mapping_package import MappingPackageMetadata, MappingPackageEligibilityConstraints, \
    MappingPackage


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

        mapping_suite = importer_class().load(temp_mp_path)

        assert mapping_suite is not None
        assert mapping_suite.path is not None
        assert mapping_suite.path == expected_relative_path
        assert (temp_mp_path / mapping_suite.path).exists()
        assert len(mapping_suite.files) > 0
        for file in mapping_suite.files:
            assert file is not None
            assert (temp_mp_path / file.path).exists()
            assert file.content is not None


def _test_mapping_suites_importer(dummy_mapping_package_path: Path,
                                  importer_class,
                                  expected_relative_path: str) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        mapping_suites = importer_class().load(temp_mp_path)

        for mapping_suite in mapping_suites:
            assert mapping_suite is not None
            assert mapping_suite.path is not None
            assert mapping_suite.path.is_relative_to(expected_relative_path)
            assert (temp_mp_path / mapping_suite.path).exists()
            assert len(mapping_suite.files) > 0
            for file in mapping_suite.files:
                assert file is not None
                assert (temp_mp_path / file.path).exists()
                assert file.content is not None


def test_technical_mapping_suite_importer(dummy_mapping_package_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        mapping_suite: TechnicalMappingSuite = TechnicalMappingSuiteLoader().load(temp_mp_path)

        assert any(isinstance(file, RMLMappingFile) for file in mapping_suite.files)
        assert any(isinstance(file, YARRRMLMappingFile) for file in mapping_suite.files)

        assert mapping_suite is not None
        assert mapping_suite.path is not None
        assert mapping_suite.path == RELATIVE_TECHNICAL_MAPPING_SUITE_PATH
        assert (temp_mp_path / mapping_suite.path).exists()
        assert len(mapping_suite.files) > 0
        for file in mapping_suite.files:
            assert file is not None
            assert (temp_mp_path / file.path).exists()
            assert file.content is not None


def test_value_mapping_suite_importer(dummy_mapping_package_path: Path) -> None:
    _test_mapping_suite_importer(
        dummy_mapping_package_path,
        VocabularyMappingSuiteLoader,
        RELATIVE_VALUE_MAPPING_SUITE_PATH
    )


def test_test_data_suites_importer(dummy_mapping_package_path: Path) -> None:
    _test_mapping_suites_importer(
        dummy_mapping_package_path,
        TestDataSuitesLoader,
        RELATIVE_TEST_DATA_PATH
    )


def test_sparql_validation_suites_importer(dummy_mapping_package_path: Path) -> None:
    _test_mapping_suites_importer(
        dummy_mapping_package_path,
        SPARQLTestSuitesLoader,
        RELATIVE_SPARQL_SUITE_PATH
    )


def test_shacl_validation_suites_importer(dummy_mapping_package_path: Path) -> None:
    _test_mapping_suites_importer(
        dummy_mapping_package_path,
        SHACLTestSuitesLoader,
        RELATIVE_SHACL_SUITE_PATH
    )


def test_suite_metadata_importer(dummy_mapping_package_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        # Execute
        metadata = MappingPackageMetadataLoader().load(package_path=temp_mp_path)

        # Verify
        assert metadata is not None
        assert isinstance(metadata, MappingPackageMetadata)

        # Verify required fields
        assert metadata.identifier and isinstance(metadata.identifier, str)
        assert len(metadata.identifier) >= MSSDK_STR_MIN_LENGTH
        assert len(metadata.identifier) <= MSSDK_STR_MAX_LENGTH

        assert metadata.title and isinstance(metadata.title, str)
        assert len(metadata.title) >= MSSDK_STR_MIN_LENGTH
        assert len(metadata.title) <= MSSDK_STR_MAX_LENGTH

        assert metadata.issue_date and isinstance(metadata.issue_date, str)
        assert len(metadata.issue_date) >= MSSDK_STR_MIN_LENGTH
        assert len(metadata.issue_date) <= MSSDK_STR_MAX_LENGTH
        # Optionally verify if issue_date is in correct format
        try:
            datetime.fromisoformat(metadata.issue_date)
        except ValueError:
            assert False, "issue_date is not in valid ISO format"

        assert metadata.type and isinstance(metadata.type, str)
        assert len(metadata.type) >= MSSDK_STR_MIN_LENGTH
        assert len(metadata.type) <= MSSDK_STR_MAX_LENGTH

        assert metadata.mapping_version and isinstance(metadata.mapping_version, str)
        assert metadata.ontology_version and isinstance(metadata.ontology_version, str)

        # Verify eligibility constraints
        assert metadata.eligibility_constraints is not None
        assert isinstance(metadata.eligibility_constraints, MappingPackageEligibilityConstraints)

        # Verify signature
        assert metadata.signature is not None
        assert isinstance(metadata.signature, bytes)

        # Verify field aliases
        # Read the original JSON to verify the aliases are working correctly
        metadata_file_path = temp_mp_path / RELATIVE_SUITE_METADATA_PATH
        original_data = json.loads(metadata_file_path.read_text())

        assert metadata.issue_date == original_data["created_at"]
        assert metadata.type == original_data["mapping_type"]
        assert metadata.eligibility_constraints == MappingPackageEligibilityConstraints(
            **original_data["metadata_constraints"]
        )
        assert metadata.signature == bytearray(original_data["mapping_suite_hash_digest"], MSSDK_DEFAULT_STR_ENCODE)


def test_conceptual_mapping_importer(dummy_mapping_package_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        cm_file = ConceptualMappingFileLoader().load(temp_mp_path)

        assert cm_file is not None
        assert cm_file.path is not None
        assert cm_file.path == RELATIVE_CONCEPTUAL_MAPPING_PATH
        assert (temp_mp_path / cm_file.path).exists()
        assert cm_file.content is not None
        assert len(cm_file.content) > 0


def test_mapping_package_importer(dummy_mapping_package_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        mapping_package: MappingPackage = MappingPackageLoader().load(temp_mp_path)

        assert mapping_package.test_suites_shacl is not None
        assert len(mapping_package.test_suites_shacl) > 0
        assert mapping_package.test_suites_sparql is not None
        assert len(mapping_package.test_suites_sparql) > 0
        assert mapping_package.test_data_suites is not None
        assert len(mapping_package.test_data_suites) > 0

        assert mapping_package.metadata is not None
        assert mapping_package.conceptual_mapping_file is not None
        assert mapping_package.technical_mapping_suite is not None
        assert mapping_package.vocabulary_mapping_suite is not None