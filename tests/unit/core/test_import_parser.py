# test_parsers.py
import io

import pandas as pd
import pytest

from mssdk.core.adapters.package_importer import FileParser, FileParsingError


def test_xml_parser():
    """Test XML parsing"""
    parser = FileParser()
    valid_xml = b'<?xml version="1.0"?><root><data>Test</data></root>'
    invalid_xml = b'<invalid xml>'

    # Test valid XML
    result = parser.parse_xml(valid_xml)
    assert isinstance(result, str)
    assert '<root>' in result

    # Test invalid XML
    with pytest.raises(FileParsingError):
        parser.parse_xml(invalid_xml)


def test_excel_parser():
    """Test Excel parsing"""
    parser = FileParser()

    # Create test Excel content
    df = pd.DataFrame({
        'source': ['field1', 'field2'],
        'target': ['concept1', 'concept2']
    })
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    excel_content = buffer.getvalue()

    # Test parsing
    result = parser.parse_excel(excel_content)
    assert isinstance(result, dict)
    assert 'Sheet1' in result
    assert len(result['Sheet1']) == 2
    assert result['Sheet1'][0]['source'] == 'field1'

    # Test invalid Excel
    with pytest.raises(FileParsingError):
        parser.parse_excel(b'invalid excel content')


def test_ttl_parser():
    """Test TTL parsing"""
    parser = FileParser()
    ttl_content = b'@prefix ex: <http://example.org/> .\nex:Resource1 a ex:Type1 .'

    result = parser.parse_ttl(ttl_content)
    assert isinstance(result, str)
    assert '@prefix' in result


def test_sparql_parser():
    """Test SPARQL parsing"""
    parser = FileParser()
    sparql_content = b'SELECT ?s WHERE { ?s a ?type }'

    result = parser.parse_sparql(sparql_content)
    assert isinstance(result, str)
    assert 'SELECT' in result