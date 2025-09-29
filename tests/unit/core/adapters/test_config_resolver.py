import os
from unittest.mock import patch, MagicMock

import pytest

from mapping_suite_sdk.core.adapters.config_resolver import (
    ConfigResolverABC,
    EnvConfigResolver,
    DefaultValueConfigResolver,
    env_property
)


def test_config_resolver_abc_cannot_be_instantiated():
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        ConfigResolverABC()


def test_config_resolver_abc_enforces_abstract_method_implementation():
    class IncompleteResolver(ConfigResolverABC):
        pass

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteResolver()


def test_env_config_resolver_returns_existing_environment_variable():
    resolver = EnvConfigResolver()

    with patch.dict(os.environ, {'TEST_CONFIG': 'test_value'}):
        result = resolver.concrete_config_resolve('TEST_CONFIG', 'default')
        assert result == 'test_value'


def test_env_config_resolver_returns_default_when_env_var_missing():
    resolver = EnvConfigResolver()

    with patch.dict(os.environ, {}, clear=True):
        result = resolver.concrete_config_resolve('NONEXISTENT_CONFIG', 'default_value')
        assert result == 'default_value'


def test_env_config_resolver_returns_none_default():
    resolver = EnvConfigResolver()

    with patch.dict(os.environ, {}, clear=True):
        result = resolver.concrete_config_resolve('NONEXISTENT_CONFIG', None)
        assert result is None


def test_env_config_resolver_handles_empty_string_env_var():
    resolver = EnvConfigResolver()

    with patch.dict(os.environ, {'EMPTY_CONFIG': ''}):
        result = resolver.concrete_config_resolve('EMPTY_CONFIG', 'default')
        assert result == ''


def test_default_value_config_resolver_always_returns_default():
    resolver = DefaultValueConfigResolver()

    result = resolver.concrete_config_resolve('ANY_CONFIG_NAME', 'expected_default')
    assert result == 'expected_default'


def test_default_value_config_resolver_ignores_config_name():
    resolver = DefaultValueConfigResolver()

    result1 = resolver.concrete_config_resolve('CONFIG_1', 'same_default')
    result2 = resolver.concrete_config_resolve('CONFIG_2', 'same_default')
    result3 = resolver.concrete_config_resolve('COMPLETELY_DIFFERENT', 'same_default')

    assert result1 == result2 == result3 == 'same_default'


def test_default_value_config_resolver_with_none_default():
    resolver = DefaultValueConfigResolver()

    result = resolver.concrete_config_resolve('ANY_CONFIG', None)
    assert result is None


def test_env_property_decorator_creates_property():
    class TestClass:
        @env_property(DefaultValueConfigResolver, 'default_val')
        def test_config(self, config_value: str) -> str:
            return config_value.upper()

    # Check that it's actually a property
    assert isinstance(TestClass.__dict__['test_config'], property)


def test_env_property_decorator_uses_method_name_as_config_name():
    mock_resolver = MagicMock()
    mock_resolver.return_value.concrete_config_resolve.return_value = 'resolved_value'

    class TestClass:
        @env_property(mock_resolver, 'default_val')
        def my_config_property(self, config_value: str) -> str:
            return config_value

    instance = TestClass()
    result = instance.my_config_property

    # Verify the resolver was called with the method name as config_name
    mock_resolver.return_value.concrete_config_resolve.assert_called_once_with(
        config_name='my_config_property',
        default_value='default_val'
    )
    assert result == 'resolved_value'


def test_env_property_decorator_passes_resolved_value_to_method():
    class TestClass:
        @env_property(DefaultValueConfigResolver, 'test_default')
        def transform_config(self, config_value: str) -> str:
            return f"transformed_{config_value}"

    instance = TestClass()
    result = instance.transform_config

    assert result == "transformed_test_default"


def test_env_property_decorator_with_env_resolver():
    class TestClass:
        @env_property(EnvConfigResolver, 'fallback_value')
        def database_url(self, config_value: str) -> str:
            return f"Connecting to: {config_value}"

    instance = TestClass()

    # Test with environment variable set
    with patch.dict(os.environ, {'database_url': 'postgresql://localhost:5432/mydb'}):
        result = instance.database_url
        assert result == "Connecting to: postgresql://localhost:5432/mydb"

    # Test with environment variable not set (should use default)
    with patch.dict(os.environ, {}, clear=True):
        result = instance.database_url
        assert result == "Connecting to: fallback_value"


def test_env_property_decorator_with_none_default():
    class TestClass:
        @env_property(DefaultValueConfigResolver, None)
        def optional_config(self, config_value: str) -> str:
            return config_value if config_value is not None else "no_config"

    instance = TestClass()
    result = instance.optional_config

    assert result == "no_config"


def test_env_property_decorator_method_can_process_config_value():
    class TestClass:
        @env_property(DefaultValueConfigResolver, '42')
        def port_number(self, config_value: str) -> int:
            return int(config_value)

        @env_property(DefaultValueConfigResolver, 'true')
        def debug_mode(self, config_value: str) -> bool:
            return config_value.lower() == 'true'

        @env_property(DefaultValueConfigResolver, 'item1,item2,item3')
        def config_list(self, config_value: str) -> list:
            return config_value.split(',')

    instance = TestClass()

    assert instance.port_number == 42
    assert instance.debug_mode is True
    assert instance.config_list == ['item1', 'item2', 'item3']


def test_env_property_decorator_multiple_properties_same_class():
    class TestClass:
        @env_property(DefaultValueConfigResolver, 'value1')
        def config_one(self, config_value: str) -> str:
            return f"first_{config_value}"

        @env_property(DefaultValueConfigResolver, 'value2')
        def config_two(self, config_value: str) -> str:
            return f"second_{config_value}"

    instance = TestClass()

    assert instance.config_one == "first_value1"
    assert instance.config_two == "second_value2"


def test_custom_config_resolver_with_env_property():
    class UpperCaseConfigResolver(ConfigResolverABC):
        def concrete_config_resolve(self, config_name: str, default_value: str) -> str:
            return default_value.upper() if default_value else default_value

    class TestClass:
        @env_property(UpperCaseConfigResolver, 'lowercase_value')
        def uppercase_config(self, config_value: str) -> str:
            return config_value

    instance = TestClass()
    result = instance.uppercase_config

    assert result == "LOWERCASE_VALUE"
