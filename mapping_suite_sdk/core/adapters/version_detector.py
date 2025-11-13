"""
Version detection for mapping packages.

This module provides abstractions and utilities for detecting mapping package versions
based on file structure and metadata content.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, List, Optional


@dataclass(frozen=True)
class VersionDetectionRule:
    """
    Immutable rule defining version detection criteria.

    A rule consists of:
    - version_id: The version string to return if matched (e.g., "v2", "v3")
    - matcher: Callable that inspects a package root and returns True if it matches

    Priority is assigned at registry level, not here.
    """
    version_id: str
    matcher: Callable[[Path], bool]

    def matches(self, package_root: Path) -> bool:
        """
        Execute matcher with error handling.

        Args:
            package_root: Root path of the package to inspect

        Returns:
            True if this rule matches the package, False otherwise
        """
        try:
            return self.matcher(package_root)
        except Exception:
            # If matcher fails (file errors, parsing errors, etc.), it's not this version
            return False


# Helper utilities for matchers

def _resolve_package_root(package_path: Path) -> Optional[Path]:
    """
    Resolve the actual package root path.

    Handles nested package structure where packages may be stored as:
    - folder_name/metadata.json
    - folder_name/folder_name/metadata.json

    Args:
        package_path: Path provided by user

    Returns:
        Resolved package root or None if path invalid
    """
    if not package_path.exists() or not package_path.is_dir():
        return None

    # Check for nested structure (folder_name/folder_name/...)
    nested_root = package_path / package_path.name

    # Prefer nested root if it exists and has metadata
    if nested_root.exists() and nested_root.is_dir():
        if (nested_root / "metadata.json").exists() or (nested_root / "metadata.jsonld").exists():
            return nested_root

    # Otherwise use provided path
    return package_path


def _try_load_json_metadata(package_root: Path) -> Optional[dict]:
    """
    Try loading metadata from metadata.json or metadata.jsonld.

    Attempts to load JSON metadata from the package root, trying both
    possible metadata file names.

    Args:
        package_root: Root path of the package

    Returns:
        Parsed metadata dict or None if not found/invalid
    """
    for filename in ["metadata.jsonld", "metadata.json"]:
        metadata_file = package_root / filename
        if metadata_file.exists():
            try:
                with metadata_file.open(encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
    return None


def _get_nested_value(obj: dict, path: str) -> Optional[Any]:
    """
    Get nested value using dot notation.

    Args:
        obj: Dictionary to search
        path: Dot-separated path (e.g., "key1.key2.key3")

    Returns:
        Value at path, or None if not found

    Example:
        >>> data = {"a": {"b": {"c": 42}}}
        >>> _get_nested_value(data, "a.b.c")
        42
        >>> _get_nested_value(data, "a.b.missing")
        None
    """
    parts = path.split('.')
    current = obj

    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None

    return current


@dataclass
class PathCondition:
    """
    Path pattern that must or must not exist.

    Supports both simple file paths and glob patterns.
    """
    pattern: str  # e.g., "metadata.json", "test_data/*/*.xml"
    must_exist: bool = True

    def matches(self, package_root: Path) -> bool:
        """
        Check if this path condition is satisfied.

        Args:
            package_root: Root path of the package

        Returns:
            True if condition is met, False otherwise
        """
        # Strip leading slash for consistency
        pattern = self.pattern.lstrip('/')

        if '*' in pattern or '?' in pattern:
            # Glob pattern
            matches = list(package_root.glob(pattern))
            return (len(matches) > 0) == self.must_exist
        else:
            # Simple file/folder check
            exists = (package_root / pattern).exists()
            return exists == self.must_exist


@dataclass
class MetadataCondition:
    """
    JSONPath/dot-notation key that must or must not exist in metadata.

    Supports nested paths like "eligibility_constraints.constraints.min_xsd_version"
    and optional value matching.
    """
    path: str  # e.g., "eligibility_constraints.constraints.min_xsd_version"
    must_exist: bool = True
    expected_value: Optional[Any] = None  # Optional value check

    def matches(self, metadata: dict) -> bool:
        """
        Check if this metadata condition is satisfied.

        Args:
            metadata: Loaded metadata dictionary

        Returns:
            True if condition is met, False otherwise
        """
        value = _get_nested_value(metadata, self.path)
        exists = value is not None

        if not exists:
            return not self.must_exist

        # If we're here, the key exists
        if not self.must_exist:
            return False

        # Check value if specified
        if self.expected_value is not None:
            return value == self.expected_value

        return True


@dataclass
class VersionDetectionSpec:
    """
    Declarative specification for version detection.

    Generates a matcher function from declarative rules based on:
    - Path patterns (files/folders that must/must not exist)
    - Metadata conditions (keys that must/must not exist, with optional value checks)
    """
    version_id: str
    priority: int
    path_conditions: List[PathCondition] = field(default_factory=list)
    metadata_conditions: List[MetadataCondition] = field(default_factory=list)

    def build_matcher(self) -> Callable[[Path], bool]:
        """
        Generate a matcher function from this spec.

        Returns:
            Matcher function that can be used in VersionDetectionRule
        """
        def matcher(package_root: Path) -> bool:
            # Check all path conditions
            for condition in self.path_conditions:
                if not condition.matches(package_root):
                    return False

            # Load and check metadata conditions
            if self.metadata_conditions:
                metadata = _try_load_json_metadata(package_root)
                if not metadata:
                    return False

                for condition in self.metadata_conditions:
                    if not condition.matches(metadata):
                        return False

            return True

        return matcher

    def to_rule(self) -> VersionDetectionRule:
        """
        Convert this spec to a VersionDetectionRule.

        Returns:
            VersionDetectionRule with generated matcher
        """
        return VersionDetectionRule(
            version_id=self.version_id,
            matcher=self.build_matcher()
        )


def _ensure_version_detection_initialized():
    """
    Lazily initialize version detection rules.

    Import and register all version detection rules on first use.
    This avoids circular dependencies when models import from mapping_suite_sdk.
    """
    from mapping_suite_sdk.core import VersionDetectionRegistry

    # Check if already initialized
    if len(VersionDetectionRegistry._rules) > 0:
        return

    # Import version detection rules to trigger self-registration
    from mapping_suite_sdk.mapping_package_v1.adapters import version_detection_rule as _  # noqa: F401
    from mapping_suite_sdk.mapping_package_v2.adapters import version_detection_rule as _  # noqa: F401, F811
    from mapping_suite_sdk.mapping_package_v3.adapters import version_detection_rule as _  # noqa: F401, F811


def detect_mapping_package_version(
    package_path: Path,
    rules: Optional[list[VersionDetectionRule]] = None
) -> Optional[str]:
    """
    Detect mapping package version using registered detection rules.

    Tries each rule in priority order (highest first) until one matches.
    Rules are typically loaded from the registry, but can be overridden for testing.

    Args:
        package_path: Path to the mapping package folder
        rules: Detection rules sorted by priority (defaults to registry)

    Returns:
        Version string (e.g., "v2", "v3", "v3L") or None if not recognized

    Example:
        >>> from pathlib import Path
        >>> version = detect_mapping_package_version(Path("./my_package"))
        >>> print(version)  # "v3"
    """
    if rules is None:
        # Lazy initialization: ensure version detection rules are registered
        _ensure_version_detection_initialized()

        from mapping_suite_sdk.core import VersionDetectionRegistry
        rules = VersionDetectionRegistry.get_rules()

    package_root = _resolve_package_root(package_path)
    if not package_root:
        return None

    # Rules are already sorted by priority in registry
    for rule in rules:
        if rule.matches(package_root):
            return rule.version_id

    return None