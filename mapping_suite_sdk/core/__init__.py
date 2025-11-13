from __future__ import annotations

from typing import Dict, TYPE_CHECKING

# Import config for backward compatibility
from mapping_suite_sdk.core.config import MSSDKCoreConfig

if TYPE_CHECKING:
    from mapping_suite_sdk.core.adapters.version_detector import VersionDetectionRule


class VersionDetectionRegistry:
    """
    Registry for version detection rules with self-registration support.

    Version packages self-register their detection rules during initialization.
    Rules are stored with priorities and retrieved sorted by priority (highest first).
    """

    _rules: Dict[str, tuple[VersionDetectionRule, int]] = {}

    @classmethod
    def register(cls, rule: VersionDetectionRule, priority: int) -> None:
        """
        Register a version detection rule.

        Version packages call this during initialization to self-register their detection rules.
        Rules with higher priority are tried first during version detection.

        Args:
            rule: The detection rule to register
            priority: Priority for detection order (higher = tried first)

        Example:
            >>> from mapping_suite_sdk.core import VersionDetectionRegistry
            >>> from mapping_suite_sdk.mapping_package_v3.adapters.version_detection_rule import v3_full_detection_rule
            >>> VersionDetectionRegistry.register(v3_full_detection_rule, priority=2)
        """
        cls._rules[rule.version_id] = (rule, priority)

    @classmethod
    def get_rules(cls) -> list[VersionDetectionRule]:
        """
        Get all registered version detection rules, sorted by priority.

        Rules are sorted in descending priority order (highest priority first).
        This ordering determines which version detection is attempted first.

        Returns:
            List of rules sorted by priority (highest to lowest)

        Example:
            >>> rules = VersionDetectionRegistry.get_rules()
            >>> for rule in rules:
            ...     print(f"{rule.version_id} will be tried")
            v3 will be tried
            v3L will be tried
            v2 will be tried
        """
        return [
            rule for rule, priority in sorted(
                cls._rules.values(),
                key=lambda x: x[1],
                reverse=True
            )
        ]
