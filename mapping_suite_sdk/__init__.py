import importlib.metadata
import logging

from mapping_suite_sdk.config import MSSDKConfigResolver, mssdk_config

__version__ = importlib.metadata.version('mapping-suite-sdk')

logging.basicConfig(level=logging.INFO,
                    format=mssdk_config.MSSDK_LOGGING_STRING_FORMAT,
                    datefmt=mssdk_config.MSSDK_DATE_FORMAT)


__all__ = [
    "mssdk_config",
    "MSSDKConfigResolver",
]
