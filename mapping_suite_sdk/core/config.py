"""
Core configuration for Mapping Suite SDK.

This module provides base configuration classes that are aggregated
by the main MSSDKConfigResolver.
"""

import json
from typing import Tuple, Dict

from mapping_suite_sdk.core.adapters.config_resolver import env_property, DefaultValueConfigResolver


class MSSDKCoreConfig:
    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="1")
    def MSSDK_MIN_STR_LENGTH(self, config_value: str) -> int:
        return int(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="256")
    def MSSDK_MAX_STR_LENGTH(self, config_value: str) -> int:
        return int(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="utf-8")
    def MSSDK_DEFAULT_STR_ENCODE(self, config_value: str) -> str:
        return config_value

    @env_property(config_resolver_class=DefaultValueConfigResolver,
                  default_value="%(asctime)s | %(levelname)s | %(filename)s | Line: %(lineno)d | %(message)s")
    def MSSDK_LOGGING_STRING_FORMAT(self, config_value: str) -> str:
        return config_value

    @env_property(config_resolver_class=DefaultValueConfigResolver,
                  default_value="%(asctime)s | %(levelname)s | %(name)s | %(filename)s | %(funcName)s | Line: %(lineno)d | %(message)s")
    def MSSDK_LOGGING_EXTENDED_STRING_FORMAT(self, config_value: str) -> str:
        return config_value

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="[{package_source}] - {message}")
    def MSSDK_LOGGING_MESSAGE_FORMAT(self, config_value: str) -> str:
        return config_value

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="%Y-%m-%dT%H:%M:%S%z")
    def MSSDK_DATE_FORMAT(self, config_value: str) -> str:
        return config_value

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value=".html .json .csv .ttl")
    def MSSDK_SUPPORTED_TEXT_FILE_EXTENSIONS(self, config_value: str) -> Tuple:
        return tuple(config_value.split(" "))

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value=".zip")
    def MSSDK_SUPPORTED_BYTES_FILE_EXTENSIONS(self, config_value: str) -> Tuple:
        return tuple(config_value.split(" "))

    @env_property(config_resolver_class=DefaultValueConfigResolver,
                  default_value='{"no_args_is_help": true, "pretty_exceptions_enable": true, "pretty_exceptions_show_locals": false, "pretty_exceptions_short": true, "add_completion": false}')
    def MSSDK_TYPER_DEFAULT_ARGS(self, config_value: str) -> Dict:
        return json.loads(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver,
                  default_value='{"no_args_is_help": true}')
    def MSSDK_TYPER_COMMANDS_DEFAULT_ARGS(self, config_value: str) -> Dict:
        return json.loads(config_value)