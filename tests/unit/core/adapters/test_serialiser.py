import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk.core.adapters.serialiser import (
    MappingPackageAssetSerialiser,
    TechnicalMappingCollectionAssetSerialiser,
    VocabularyMappingCollectionAssetSerialiser,
    TestDataCollectionAssetSerialiser,
    SAPRQLTestCollectionAssetSerialiser,
    SHACLTestCollectionAssetSerialiser,
    ConceptualMappingFileAssetSerialiser,
    TestResultCollectionAssetSerialiser, write_file_by_content_type
)
from mapping_suite_sdk.core.models.collection_asset import (
    TechnicalMappingCollectionAsset,
    VocabularyMappingCollectionAsset,
    TestDataCollectionAsset,
    SAPRQLTestCollectionAsset,
    SHACLTestCollectionAsset,
    TestResultCollectionAsset, TestDataResultCollectionAsset
)
from mapping_suite_sdk.core.models.file_asset import (
    RMLMappingFileAsset,
    VocabularyMappingFileAsset,
    TestDataFileAsset,
    SPARQLQueryFileAsset,
    SHACLShapesFileAsset,
    ConceptualMappingFileAsset, ReportFileAsset, TestDataResultFileAsset
)


def test_write_file_by_content_type(tmp_path):
    """Test the write_file_by_content_type function with different content types."""

    test_dir = tmp_path / "test_files"

    text_file = test_dir / "test.txt"
    binary_file = test_dir / "test.bin"

    text_content = "This is a test text file"
    write_file_by_content_type(text_file, text_content)
    assert text_file.exists()
    assert text_file.read_text() == text_content

    binary_content = b'\x00\x01\x02\x03'
    write_file_by_content_type(binary_file, binary_content)
    assert binary_file.exists()
    assert binary_file.read_bytes() == binary_content

    invalid_file = test_dir / "invalid.txt"
    with pytest.raises(TypeError) as excinfo:
        write_file_by_content_type(invalid_file, 123)  # Integer should not a valid content type
    assert "Content must be str or bytes" in str(excinfo.value)
    assert not invalid_file.exists()

    nested_file = test_dir / "nested" / "directory" / "test.txt"
    write_file_by_content_type(nested_file, "Nested file content")
    assert nested_file.exists()
    assert nested_file.read_text() == "Nested file content"

    # Test writing to a location with insufficient permissions
    def mock_write_text(*args, **kwargs):
        raise PermissionError("Permission denied")

    original_write_text = Path.write_text
    try:
        Path.write_text = mock_write_text
        permission_file = test_dir / "permission.txt"
        with pytest.raises(PermissionError) as excinfo:
            write_file_by_content_type(permission_file, "Permission test")
        assert "Permission denied" in str(excinfo.value)
    finally:
        Path.write_text = original_write_text


def test_mapping_package_asset_serialiser_protocol():
    class TestSerialiser:
        def serialise(self, package_folder_path: Path, asset) -> None:
            ...

    serialiser = TestSerialiser()
    with tempfile.TemporaryDirectory() as temp_dir:
        serialiser.serialise(Path(temp_dir), "test_asset")


def test_mapping_package_asset_serialiser_not_implemented():
    class TestSerialiser(MappingPackageAssetSerialiser):
        ...

    serialiser = TestSerialiser()
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(NotImplementedError):
            serialiser.serialise(Path(temp_dir), "test_asset")


def test_technical_mapping_collection_asset_serialiser():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        test_files = [
            RMLMappingFileAsset(
                path=Path("test_mapping.rml.ttl"),
                content="@prefix rr: <http://www.w3.org/ns/r2rml#> ."
            ),
            RMLMappingFileAsset(
                path=Path("another_mapping.rml.ttl"),
                content="@prefix rml: <http://semweb.mmlab.be/ns/rml#> ."
            )
        ]

        technical_mapping = TechnicalMappingCollectionAsset(
            path=Path("transformation/mappings"),
            files=test_files
        )

        serialiser = TechnicalMappingCollectionAssetSerialiser()
        serialiser.serialise(temp_path, technical_mapping)

        # Verify suite directory is created
        suite_path = temp_path / technical_mapping.path
        assert suite_path.exists()
        assert suite_path.is_dir()

        # Verify files are written
        for file in test_files:
            file_path = temp_path / file.path
            assert file_path.exists()
            assert file_path.read_text() == file.content


def test_vocabulary_mapping_collection_asset_serialiser():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        test_files = [
            VocabularyMappingFileAsset(
                path=Path("vocab1.json"),
                content='{"key": "value1"}'
            ),
            VocabularyMappingFileAsset(
                path=Path("vocab2.csv"),
                content="header1,header2\nvalue1,value2"
            )
        ]

        vocabulary_mapping = VocabularyMappingCollectionAsset(
            path=Path("transformation/resources"),
            files=test_files
        )

        serialiser = VocabularyMappingCollectionAssetSerialiser()
        serialiser.serialise(temp_path, vocabulary_mapping)

        # Verify suite directory is created
        suite_path = temp_path / vocabulary_mapping.path
        assert suite_path.exists()
        assert suite_path.is_dir()

        # Verify files are written
        for file in test_files:
            file_path = temp_path / file.path
            assert file_path.exists()
            assert file_path.read_text() == file.content


def test_test_data_collection_asset_serialiser():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test data suites
        test_suites = [
            TestDataCollectionAsset(
                path=Path("test_data/suite1"),
                files=[
                    TestDataFileAsset(
                        path=Path("test1.xml"),
                        content="<test>data1</test>"
                    ),
                    TestDataFileAsset(
                        path=Path("test2.xml"),
                        content="<test>data2</test>"
                    )
                ]
            ),
            TestDataCollectionAsset(
                path=Path("test_data/suite2"),
                files=[
                    TestDataFileAsset(
                        path=Path("test3.xml"),
                        content="<test>data3</test>"
                    )
                ]
            )
        ]

        serialiser = TestDataCollectionAssetSerialiser()
        serialiser.serialise(temp_path, test_suites)

        # Verify all suites and files are created
        for suite in test_suites:
            suite_path = temp_path / suite.path
            assert suite_path.exists()
            assert suite_path.is_dir()

            for file in suite.files:
                file_path = temp_path / file.path
                assert file_path.exists()
                assert file_path.read_text() == file.content


def test_sparql_test_collection_asset_serialiser():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create SPARQL test suites
        sparql_suites = [
            SAPRQLTestCollectionAsset(
                path=Path("validation/sparql/cm_assertions"),
                files=[
                    SPARQLQueryFileAsset(
                        path=Path("query1.rq"),
                        content="SELECT * WHERE { ?s ?p ?o }"
                    ),
                    SPARQLQueryFileAsset(
                        path=Path("query2.rq"),
                        content="ASK WHERE { ?s a ?type }"
                    )
                ]
            )
        ]

        serialiser = SAPRQLTestCollectionAssetSerialiser()
        serialiser.serialise(temp_path, sparql_suites)

        # Verify suite and files are created
        for suite in sparql_suites:
            suite_path = temp_path / suite.path
            assert suite_path.exists()
            assert suite_path.is_dir()

            for file in suite.files:
                file_path = temp_path / file.path
                assert file_path.exists()
                assert file_path.read_text() == file.content


def test_shacl_test_collection_asset_serialiser():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create SHACL collection with nested structure
        from mapping_suite_sdk.core.models.collection_asset import SHACLShapesCollectionAsset
        from mapping_suite_sdk.core.models.file_asset import SHACLShapesResultQueryFileAsset

        shacl_collection = SHACLShapesCollectionAsset(
            path=Path("validation/shacl/epo"),
            files=[
                SHACLShapesFileAsset(
                    path=Path("shapes1.ttl"),
                    content="@prefix sh: <http://www.w3.org/ns/shacl#> ."
                )
            ]
        )

        shacl_asset = SHACLTestCollectionAsset(
            path=Path("validation/shacl"),
            shacl_collections=[shacl_collection],
            shacl_result_query=SHACLShapesResultQueryFileAsset(
                path=Path("shacl_result_query.rq"),
                content="SELECT * WHERE { ?s ?p ?o }"
            )
        )

        serialiser = SHACLTestCollectionAssetSerialiser()
        serialiser.serialise(temp_path, shacl_asset)

        # Verify main path is created
        main_path = temp_path / shacl_asset.path
        assert main_path.exists()

        # Verify collection directory and files
        collection_path = temp_path / shacl_collection.path
        assert collection_path.exists()
        assert collection_path.is_dir()

        for shape_file in shacl_collection.files:
            file_path = temp_path / shape_file.path
            assert file_path.exists()
            assert file_path.read_text() == shape_file.content

        # Verify result query file
        query_path = temp_path / shacl_asset.shacl_result_query.path
        assert query_path.exists()
        assert query_path.read_text() == shacl_asset.shacl_result_query.content


def test_conceptual_mapping_file_asset_serialiser():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test conceptual mapping file (binary content)
        test_content = b"test binary content for conceptual mapping"
        conceptual_mapping = ConceptualMappingFileAsset(
            path=Path("transformation/conceptual_mappings.xlsx"),
            content=test_content
        )

        serialiser = ConceptualMappingFileAssetSerialiser()
        serialiser.serialise(temp_path, conceptual_mapping)

        # Verify file is created with correct content
        file_path = temp_path / conceptual_mapping.path
        assert file_path.exists()
        assert file_path.read_bytes() == test_content

        # Verify parent directory is created
        assert file_path.parent.exists()


def test_test_result_collection_asset_serialiser():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        test_result_collection = TestResultCollectionAsset(
            files=[
                ReportFileAsset(
                    path=Path("output/validation_summary_report.html"),
                    content="<html>Summary Report</html>"
                )
            ],
            result_suites=[
                TestResultCollectionAsset(
                    path=Path("output/test_suite"),
                    files=[
                        ReportFileAsset(
                            path=Path("output/test_suite/suite_report.json"),
                            content='{"status": "passed"}'
                        )
                    ],
                    result_suites=[
                        TestDataResultCollectionAsset(
                            path=Path("output/test_suite"),
                            test_data_output=TestDataResultFileAsset(
                                path=Path("output/test_suite/result.ttl"),
                                content="@prefix : <http://example.org/> ."
                            ),
                            files=[
                                ReportFileAsset(
                                    path=Path("output/test_suite/test_suite_report/report.html"),
                                    content="<html>Test Report</html>"
                                )
                            ]
                        )
                    ]
                )
            ],
            path=Path("output")
        )

        serialiser = TestResultCollectionAssetSerialiser()
        serialiser.serialise(temp_path, test_result_collection)

        # Verify main files
        for report in test_result_collection.files:
            file_path = temp_path / report.path
            assert file_path.exists()
            assert file_path.read_text() == report.content

        # Verify nested structure
        for test_data_suite in test_result_collection.result_suites:
            for suite_report in test_data_suite.files:
                file_path = temp_path / suite_report.path
                assert file_path.exists()
                assert file_path.read_text() == suite_report.content

            for result_collection in test_data_suite.result_suites:
                # Verify output file
                output_path = temp_path / result_collection.test_data_output.path
                assert output_path.exists()
                assert output_path.read_text() == result_collection.test_data_output.content

                # Verify report files
                for report in result_collection.files:
                    report_path = temp_path / report.path
                    assert report_path.exists()
                    assert report_path.read_text() == report.content


def test_serialiser_creates_parent_directories():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create asset with nested path that doesn't exist
        technical_mapping = TechnicalMappingCollectionAsset(
            path=Path("deep/nested/transformation/mappings"),
            files=[
                RMLMappingFileAsset(
                    path=Path("deep/nested/test.rml.ttl"),
                    content="test content"
                )
            ]
        )

        serialiser = TechnicalMappingCollectionAssetSerialiser()
        serialiser.serialise(temp_path, technical_mapping)

        # Verify nested directories are created
        suite_path = temp_path / technical_mapping.path
        assert suite_path.exists()
        assert suite_path.is_dir()

        file_path = temp_path / technical_mapping.files[0].path
        assert file_path.exists()
        assert file_path.parent.exists()


def test_empty_collections_serialisation():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Test with empty files list
        empty_technical_mapping = TechnicalMappingCollectionAsset(
            path=Path("transformation/mappings"),
            files=[]
        )

        serialiser = TechnicalMappingCollectionAssetSerialiser()
        serialiser.serialise(temp_path, empty_technical_mapping)

        # Verify directory is still created
        suite_path = temp_path / empty_technical_mapping.path
        assert suite_path.exists()
        assert suite_path.is_dir()


def test_test_data_collection_empty_list_serialisation():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Test with empty list
        empty_suites = []

        serialiser = TestDataCollectionAssetSerialiser()
        serialiser.serialise(temp_path, empty_suites)

        # Should not create any directories or files
        assert len(list(temp_path.iterdir())) == 0
