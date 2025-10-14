import importlib.metadata
import logging

from mapping_suite_sdk.core import MSSDKCoreConfig
from mapping_suite_sdk.mapping_package_v1 import MPV1AssetsPathsConfig
from mapping_suite_sdk.mapping_package_v2 import MPV2AssetsPathsConfig

__version__ = importlib.metadata.version('mapping-suite-sdk')

from mapping_suite_sdk.mapping_package_v3 import MPV3AssetsPathsConfig


class MSSDKConfigResolver(MSSDKCoreConfig, MPV1AssetsPathsConfig, MPV2AssetsPathsConfig, MPV3AssetsPathsConfig):
    """
        This class resolve the configs of MSSDK project.
    """


mssdk_config = MSSDKConfigResolver()

logging.basicConfig(level=logging.INFO,
                    format=mssdk_config.MSSDK_LOGGING_STRING_FORMAT,
                    datefmt=mssdk_config.MSSDK_DATE_FORMAT)
