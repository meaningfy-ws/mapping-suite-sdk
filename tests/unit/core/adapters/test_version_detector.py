"""
Unit tests for version detection system.

Tests the version detection registry, rules, and detection orchestration.
"""

import json
from pathlib import Path

import pytest

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core import VersionDetectionRegistry
from mapping_suite_sdk.core.adapters.version_detector import (
    VersionDetectionRule,
    VersionDetectionSpec,
    PathCondition,
    MetadataCondition,
    detect_mapping_package_version,
    _resolve_package_root,
    _try_load_json_metadata,
    _get_nested_value
)
from mapping_suite_sdk.mapping_package_v1.adapters.version_detection_rule import V1_SPEC
from mapping_suite_sdk.mapping_package_v2.adapters.version_detection_rule import V2_SPEC
from mapping_suite_sdk.mapping_package_v3.adapters.version_detection_rule import (
    V3_FULL_SPEC,
    V3_LIGHTWEIGHT_SPEC
)


# Registry tests

def test_all_version_rules_registered():
    """Verify all expected versions are in registry."""
    rules = VersionDetectionRegistry.get_rules()
    versions = {rule.version_id for rule in rules}
    assert versions == {"v1", "v2", "v3", "v3L"}


def test_registry_returns_rules_sorted_by_priority():
    """Verify registry returns rules in correct priority order."""
    rules = VersionDetectionRegistry.get_rules()
    version_ids = [rule.version_id for rule in rules]
    # Expected order: v3 (highest), v3L, v2, v1 (lowest)
    assert version_ids == ["v3", "v3L", "v2", "v1"]


# Helper utilities tests

def test_resolve_package_root_simple(tmp_path):
    """Test resolving package root for simple structure."""
    package_dir = tmp_path / "test_package"
    package_dir.mkdir()
    (package_dir / "metadata.json").write_text("{}")

    resolved = _resolve_package_root(package_dir)
    assert resolved == package_dir


def test_resolve_package_root_nested(tmp_path):
    """Test resolving package root for nested structure (folder/folder/metadata.json)."""
    outer_dir = tmp_path / "test_package"
    nested_dir = outer_dir / "test_package"
    nested_dir.mkdir(parents=True)
    (nested_dir / "metadata.json").write_text("{}")

    resolved = _resolve_package_root(outer_dir)
    assert resolved == nested_dir


def test_resolve_package_root_invalid_path(tmp_path):
    """Test resolving non-existent path returns None."""
    invalid_path = tmp_path / "does_not_exist"
    resolved = _resolve_package_root(invalid_path)
    assert resolved is None


def test_try_load_json_metadata_from_json(tmp_path):
    """Test loading metadata from metadata.json."""
    package_dir = tmp_path / "test_package"
    package_dir.mkdir()
    metadata = {"identifier": "test-id", "title": "Test"}
    (package_dir / "metadata.json").write_text(json.dumps(metadata))

    loaded = _try_load_json_metadata(package_dir)
    assert loaded == metadata


def test_try_load_json_metadata_from_jsonld(tmp_path):
    """Test loading metadata from metadata.jsonld."""
    package_dir = tmp_path / "test_package"
    package_dir.mkdir()
    metadata = {"@context": "http://example.org", "id": "test-id"}
    (package_dir / "metadata.jsonld").write_text(json.dumps(metadata))

    loaded = _try_load_json_metadata(package_dir)
    assert loaded == metadata


def test_try_load_json_metadata_prefers_jsonld(tmp_path):
    """Test that jsonld is preferred when both files exist."""
    package_dir = tmp_path / "test_package"
    package_dir.mkdir()
    json_metadata = {"format": "json"}
    jsonld_metadata = {"format": "jsonld"}
    (package_dir / "metadata.json").write_text(json.dumps(json_metadata))
    (package_dir / "metadata.jsonld").write_text(json.dumps(jsonld_metadata))

    loaded = _try_load_json_metadata(package_dir)
    assert loaded == jsonld_metadata


def test_try_load_json_metadata_no_file(tmp_path):
    """Test loading metadata when no file exists returns None."""
    package_dir = tmp_path / "test_package"
    package_dir.mkdir()

    loaded = _try_load_json_metadata(package_dir)
    assert loaded is None


def test_try_load_json_metadata_invalid_json(tmp_path):
    """Test loading invalid JSON returns None."""
    package_dir = tmp_path / "test_package"
    package_dir.mkdir()
    (package_dir / "metadata.json").write_text("not valid json {")

    loaded = _try_load_json_metadata(package_dir)
    assert loaded is None


# Declarative spec component tests

def test_get_nested_value():
    """Test _get_nested_value helper."""
    data = {
        "a": {
            "b": {
                "c": 42
            }
        },
        "x": "value"
    }

    assert _get_nested_value(data, "a.b.c") == 42
    assert _get_nested_value(data, "x") == "value"
    assert _get_nested_value(data, "a.b") == {"c": 42}
    assert _get_nested_value(data, "a.b.missing") is None
    assert _get_nested_value(data, "missing") is None


def test_path_condition_simple_file(tmp_path):
    """Test PathCondition with simple file."""
    package_dir = tmp_path / "test"
    package_dir.mkdir()
    (package_dir / "metadata.json").write_text("{}")

    condition = PathCondition("metadata.json", must_exist=True)
    assert condition.matches(package_dir) is True

    condition = PathCondition("missing.json", must_exist=True)
    assert condition.matches(package_dir) is False

    condition = PathCondition("missing.json", must_exist=False)
    assert condition.matches(package_dir) is True


def test_path_condition_glob_pattern(tmp_path):
    """Test PathCondition with glob pattern."""
    package_dir = tmp_path / "test"
    (package_dir / "test_data").mkdir(parents=True)
    (package_dir / "test_data" / "test.xml").write_text("<xml/>")

    condition = PathCondition("test_data/*.xml", must_exist=True)
    assert condition.matches(package_dir) is True

    condition = PathCondition("test_data/*.json", must_exist=True)
    assert condition.matches(package_dir) is False


def test_metadata_condition(tmp_path):
    """Test MetadataCondition."""
    metadata = {
        "identifier": "test-id",
        "eligibility_constraints": {
            "constraints": {
                "min_xsd_version": "1.0"
            }
        }
    }

    condition = MetadataCondition("identifier", must_exist=True)
    assert condition.matches(metadata) is True

    condition = MetadataCondition("missing_key", must_exist=True)
    assert condition.matches(metadata) is False

    condition = MetadataCondition("missing_key", must_exist=False)
    assert condition.matches(metadata) is True

    condition = MetadataCondition("eligibility_constraints.constraints.min_xsd_version", must_exist=True)
    assert condition.matches(metadata) is True

    condition = MetadataCondition("identifier", must_exist=True, expected_value="test-id")
    assert condition.matches(metadata) is True

    condition = MetadataCondition("identifier", must_exist=True, expected_value="wrong")
    assert condition.matches(metadata) is False


def test_version_detection_spec_to_rule(tmp_path):
    """Test VersionDetectionSpec converts to VersionDetectionRule."""
    spec = VersionDetectionSpec(
        version_id="test",
        priority=10,
        path_conditions=[PathCondition("metadata.json", must_exist=True)],
        metadata_conditions=[MetadataCondition("identifier", must_exist=True)]
    )

    rule = spec.to_rule()
    assert rule.version_id == "test"

    # Test matcher works
    package_dir = tmp_path / "test_package"
    package_dir.mkdir()
    (package_dir / "metadata.json").write_text(json.dumps({"identifier": "test"}))

    assert rule.matches(package_dir) is True


# Integration tests for detect_mapping_package_version

def test_detect_v2_package(tmp_path):
    """Test end-to-end detection of V2 package."""
    package_dir = tmp_path / "v2_package"
    package_dir.mkdir()

    v2_metadata = {
        "identifier": "test-v2",
        "mapping_version": "1.0",
        "ontology_version": "2.0",
        "eligibility_constraints": {
            "constraints": {
                "eforms_sdk_versions": ["1.0", "2.0"]
            }
        }
    }
    (package_dir / "metadata.json").write_text(json.dumps(v2_metadata))

    detected = detect_mapping_package_version(package_dir)
    assert detected == "v2"


def test_detect_v3_full_package(tmp_path):
    """Test end-to-end detection of V3 full package."""
    package_dir = tmp_path / "v3_full_package"
    package_dir.mkdir()

    v3_metadata = {
        "@context": "http://example.org",
        "id": "test-v3",
        "applicability_constraints": {}
    }
    (package_dir / "metadata.jsonld").write_text(json.dumps(v3_metadata))

    conceptual_mapping_path = package_dir / mssdk_config.MPV3_CONCEPTUAL_MAPPING_FILE_ASSET_PATH
    conceptual_mapping_path.parent.mkdir(parents=True, exist_ok=True)
    conceptual_mapping_path.write_text("dummy")

    detected = detect_mapping_package_version(package_dir)
    assert detected == "v3"


def test_detect_v3_lightweight_package(tmp_path):
    """Test end-to-end detection of V3 lightweight package."""
    package_dir = tmp_path / "v3_lightweight_package"
    package_dir.mkdir()

    v3_metadata = {
        "@context": "http://example.org",
        "id": "test-v3-light",
        "created_at": "2023-01-01T00:00:00Z"
    }
    (package_dir / "metadata.jsonld").write_text(json.dumps(v3_metadata))

    detected = detect_mapping_package_version(package_dir)
    assert detected == "v3L"


def test_detect_unrecognized_package(tmp_path):
    """Test detection returns None for unrecognized package format."""
    package_dir = tmp_path / "unknown_package"
    package_dir.mkdir()

    # Package with unknown structure
    (package_dir / "some_file.txt").write_text("not a package")

    detected = detect_mapping_package_version(package_dir)
    assert detected is None


def test_detect_with_nested_structure(tmp_path):
    """Test detection handles nested package structure."""
    outer_dir = tmp_path / "test_package"
    nested_dir = outer_dir / "test_package"
    nested_dir.mkdir(parents=True)

    v2_metadata = {
        "identifier": "test-v2",
        "mapping_version": "1.0",
        "ontology_version": "2.0",
        "eligibility_constraints": {
            "constraints": {
                "eforms_sdk_versions": ["1.0", "2.0"]
            }
        }
    }
    (nested_dir / "metadata.json").write_text(json.dumps(v2_metadata))

    detected = detect_mapping_package_version(outer_dir)
    assert detected == "v2"


def test_detect_with_custom_rules(tmp_path):
    """Test detection with custom rules (for testing/extension)."""
    package_dir = tmp_path / "custom_package"
    package_dir.mkdir()
    (package_dir / "custom.json").write_text("{}")

    def custom_matcher(path: Path) -> bool:
        return (path / "custom.json").exists()

    custom_rule = VersionDetectionRule(
        version_id="custom",
        matcher=custom_matcher
    )

    detected = detect_mapping_package_version(package_dir, rules=[custom_rule])
    assert detected == "custom"


# Error handling tests

def test_version_detection_rule_handles_matcher_exception(tmp_path):
    """Test that rule handles exceptions in matcher gracefully."""
    package_dir = tmp_path / "test"
    package_dir.mkdir()

    def failing_matcher(path: Path) -> bool:
        raise RuntimeError("Matcher failed")

    rule = VersionDetectionRule(version_id="fail", matcher=failing_matcher)

    # Should not raise, returns False
    assert rule.matches(package_dir) is False


def test_detect_invalid_path(tmp_path):
    """Test detection with invalid path returns None."""
    invalid_path = tmp_path / "does_not_exist"
    detected = detect_mapping_package_version(invalid_path)
    assert detected is None