import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class ConfigResolverABC(ABC):
    """
    This class defines a configuration resolution abstraction.
    """

    @abstractmethod
    def concrete_config_resolve(self, config_name: str, default_value: str | None) -> str:
        """
            This abstract method is used to be able to define the configuration search in different environments.
        :param config_name: The name of the configuration
        :param default_value: The default return value if the configuration is not found.
        :return: The value of the search configuration if found, otherwise default_value returns
        """
        raise NotImplementedError


class EnvConfigResolver(ConfigResolverABC):
    """
    This class aims to search for configurations in environment variables.
    """

    def concrete_config_resolve(self, config_name: str, default_value: str | None) -> str:
        value = os.environ.get(config_name, default=default_value)
        return value


class DefaultValueConfigResolver(ConfigResolverABC):
    """
    This class aims to return a default value for any configuration.
    """

    def concrete_config_resolve(self, config_name: str, default_value: str) -> str:
        return default_value


def env_property(
    config_resolver_class: type[ConfigResolverABC], default_value: str | None
) -> Callable[[Callable[..., str]], property]:
    """
    Decorator for config properties. Converts a method (self, config_value: str) -> Any
    into a property returning Any.
    """

    def wrap(func: Callable[..., Any]) -> property:
        def wrapped_function(self) -> Any:
            config_value = config_resolver_class().concrete_config_resolve(
                config_name=func.__name__, default_value=default_value
            )
            return func(self, config_value)

        return property(wrapped_function)

    return wrap
