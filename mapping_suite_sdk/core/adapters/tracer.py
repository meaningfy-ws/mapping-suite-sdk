"""
Tracing module for the Mapping Suite SDK.

This module provides functionality to add OpenTelemetry tracing to the SDK,
allowing users to monitor and debug performance and execution flow.
"""

import functools
import os

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor

# Environment variable to control tracing state
_MSSDK_TRACE_VAR_NAME = "MSSDK_TRACE"
# Set up the OpenTelemetry tracer provider
_MSSDK_TRACER_PROVIDER = TracerProvider(resource=Resource(attributes={SERVICE_NAME: "mapping-suite-sdk"}))
trace.set_tracer_provider(_MSSDK_TRACER_PROVIDER)


def add_span_processor_to_mssdk_tracer_provider(sp: SpanProcessor) -> None:
    """
    Set span processor to mssdk tracer provider.

    Args:
        sp: OpenTelemetry SpanProcessor

    Returns:
        None
    """
    if isinstance(sp, SpanProcessor):
        _MSSDK_TRACER_PROVIDER.add_span_processor(sp)


def set_mssdk_tracing(state: bool) -> None:
    """
    Set the tracing state for the SDK.

    Args:
        state: The desired tracing state (ON or OFF)

    Returns:
        None
    """
    os.environ[_MSSDK_TRACE_VAR_NAME] = str(state).casefold().strip()


def get_mssdk_tracing() -> bool:
    """
    Get the current tracing state.

    Returns:
        The current tracing state (true or false)
    """
    return os.getenv(_MSSDK_TRACE_VAR_NAME, 'false').casefold().strip() == 'true'


def is_mssdk_tracing_enabled() -> bool:
    """
    Check if tracing is currently enabled.

    Returns:
        True if tracing is enabled, False otherwise
    """
    return bool(get_mssdk_tracing())


def traced_routine(func):
    """
    Decorator to add tracing to a function.

    Creates a span for the decorated function, capturing function details,
    arguments, and any errors that occur during execution.

    Args:
        func: The function to trace

    Returns:
        The wrapped function with tracing capabilities
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if is_mssdk_tracing_enabled():
            with trace.get_tracer(__name__).start_as_current_span(f"{func.__module__}.{func.__name__}") as span:

                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                span.set_attribute("function.args", args)
                span.set_attribute("function.args_count", len(args))

                try:
                    func_result = func(*args, **kwargs)

                    span.set_attribute("function.status", "success")
                    return func_result

                except Exception as e:
                    span.set_attribute("function.status", "error")
                    span.set_attribute("error.type", e.__class__.__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)

                    raise
        else:
            return func(*args, **kwargs)

    return wrapper


def traced_class(cls):
    """
    Class decorator that applies tracing to all methods of a class.

    Similar to traced_routine but works on all methods of a class.
    Note: Currently does not work with static methods.

    Args:
        cls: The class to apply tracing to

    Returns:
        The class with tracing applied to its methods
    """
    class_name = cls.__name__

    def class_traced_routine(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if is_mssdk_tracing_enabled():
                with trace.get_tracer(__name__).start_as_current_span(f"{class_name}.{func.__name__}") as span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("class.name", class_name)
                    span.set_attribute("function.args_count", len(args))

                    try:
                        func_result = func(*args, **kwargs)
                        span.set_attribute("function.status", "success")
                        return func_result
                    except Exception as e:
                        span.set_attribute("function.status", "error")
                        span.set_attribute("error.type", e.__class__.__name__)
                        span.set_attribute("error.message", str(e))
                        span.record_exception(e)
                        raise
            else:
                return func(*args, **kwargs)

        return wrapper

    for attr_name, attr_value in cls.__dict__.items():
        # Skip special methods and non-callable attributes
        if callable(attr_value) and not attr_name.startswith('__'):
            setattr(cls, attr_name, class_traced_routine(attr_value))

    return cls
