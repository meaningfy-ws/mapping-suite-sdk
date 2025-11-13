"""
Configuration module for Mapping Suite SDK.

This module provides centralized configuration resolution for all MSSDK components.
Kept separate from __init__.py to avoid circular dependencies with version detection.
"""

from mapping_suite_sdk.core.config import MSSDKCoreConfig
from mapping_suite_sdk.mapping_package_v1 import MPV1AssetsPathsConfig
from mapping_suite_sdk.mapping_package_v2 import MPV2AssetsPathsConfig
from mapping_suite_sdk.mapping_package_v3 import MPV3AssetsPathsConfig
from mapping_suite_sdk.mapping_suite import MappingSuiteAssetsPathsConfig


class MSSDKConfigResolver(
    MSSDKCoreConfig,
    MPV1AssetsPathsConfig,
    MPV2AssetsPathsConfig,
    MPV3AssetsPathsConfig,
    MappingSuiteAssetsPathsConfig,
):
    """
    This class resolves the configs of the MSSDK project.

    Aggregates configuration from all version packages and core config.
    """


mssdk_config = MSSDKConfigResolver()