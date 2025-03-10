import os

import pytest
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from mapping_suite_sdk.adapters.tracer import (
    set_mssdk_tracing,
    get_mssdk_tracing,
    is_mssdk_tracing_enabled,
    traced_routine,
    traced_class,
    _MSSDK_TRACE_VAR_NAME,
    _MSSDK_TRACER_PROVIDER,
    add_span_processor_to_mssdk_tracer_provider,
)

# Set up a memory exporter to capture spans for testing
memory_exporter = InMemorySpanExporter()
span_processor = SimpleSpanProcessor(memory_exporter)
_MSSDK_TRACER_PROVIDER.add_span_processor(span_processor)

def test_set_mssdk_tracing():
    """Test setting the trace state via environment variable."""
    # Test setting to ON
    set_mssdk_tracing(True)
    assert os.environ[_MSSDK_TRACE_VAR_NAME] == "true"

    # Test setting to OFF
    set_mssdk_tracing(False)
    assert os.environ[_MSSDK_TRACE_VAR_NAME] == "false"


def test_get_mssdk_tracing():
    """Test getting the trace state."""
    # Test with ON state
    os.environ[_MSSDK_TRACE_VAR_NAME] = "true"
    assert get_mssdk_tracing() == True

    # Test with OFF state
    os.environ[_MSSDK_TRACE_VAR_NAME] = "false"
    assert get_mssdk_tracing() == False

    # Test default state (when environment variable isn't set)
    if _MSSDK_TRACE_VAR_NAME in os.environ:
        del os.environ[_MSSDK_TRACE_VAR_NAME]
    assert get_mssdk_tracing() == False


def test_add_span_processor_to_mssdk_tracer_provider_gets_invalid_value():
    current_len = len(_MSSDK_TRACER_PROVIDER._active_span_processor._span_processors)
    add_span_processor_to_mssdk_tracer_provider(None)
    assert len(_MSSDK_TRACER_PROVIDER._active_span_processor._span_processors) == current_len


def test_add_span_processor_to_mssdk_tracer_provider_gets_valid_value():
    current_len = len(_MSSDK_TRACER_PROVIDER._active_span_processor._span_processors)
    _memory_exporter = InMemorySpanExporter()
    add_span_processor_to_mssdk_tracer_provider(SimpleSpanProcessor(_memory_exporter))
    assert len(_MSSDK_TRACER_PROVIDER._active_span_processor._span_processors) == current_len + 1


def test_is_mssdk_tracing_enabled():
    """Test checking if tracing is enabled."""
    # Test with ON state
    os.environ[_MSSDK_TRACE_VAR_NAME] = "true"
    assert is_mssdk_tracing_enabled() is True

    # Test with OFF state
    os.environ[_MSSDK_TRACE_VAR_NAME] = "false"
    assert is_mssdk_tracing_enabled() is False


def test_traced_routine_with_tracing_enabled():
    """Test traced_routine decorator when tracing is enabled."""
    # Set tracing to enabled
    os.environ[_MSSDK_TRACE_VAR_NAME] = "true"
    memory_exporter.clear()

    # Define a test function
    @traced_routine
    def test_func(arg1, arg2):
        return arg1 + arg2

    # Call the function
    result = test_func(1, 2)

    # Verify the result
    assert result == 3

    # Verify span was created by checking the memory exporter
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]

    # Check that span has the expected attributes
    assert span.name.endswith(".test_func")  # Check that span name includes the function name
    assert span.attributes.get("function.name") == "test_func"
    assert span.attributes.get("function.status") == "success"
    assert span.attributes.get("function.args_count") == 2


def test_traced_routine_with_tracing_disabled():
    """Test traced_routine decorator when tracing is disabled."""
    # Set tracing to disabled
    os.environ[_MSSDK_TRACE_VAR_NAME] = "false"
    memory_exporter.clear()

    # Define a test function
    @traced_routine
    def test_func(arg1, arg2):
        return arg1 + arg2

    # Call the function
    result = test_func(1, 2)

    # Verify the result
    assert result == 3

    # Verify no span was created
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 0


def test_traced_routine_with_exception():
    """Test traced_routine decorator when function raises an exception."""
    # Set tracing to enabled
    os.environ[_MSSDK_TRACE_VAR_NAME] = "true"
    memory_exporter.clear()

    # Define a test function that raises an exception
    @traced_routine
    def test_func_with_error():
        raise ValueError("Test error")

    # Call the function and expect exception
    with pytest.raises(ValueError) as exc_info:
        test_func_with_error()

    assert "Test error" in str(exc_info.value)

    # Verify error was captured in span
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]

    # Check that span has the expected error attributes
    assert span.attributes.get("function.status") == "error"
    assert span.attributes.get("error.type") == "ValueError"
    assert "Test error" in span.attributes.get("error.message", "")
    assert len(span.events) > 0  # There should be an exception event


def test_traced_class_decorator():
    """Test traced_class decorator."""
    # Set tracing to enabled
    os.environ[_MSSDK_TRACE_VAR_NAME] = "true"
    memory_exporter.clear()

    # Define a test class
    @traced_class
    class TestClass:
        def method1(self, arg):
            return arg * 2

        def method2(self):
            raise ValueError("Test class error")

    # Test normal method
    test_obj = TestClass()
    result = test_obj.method1(5)

    assert result == 10

    # Verify span for method1
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]

    assert "TestClass.method1" in span.name
    assert span.attributes.get("class.name") == "TestClass"
    assert span.attributes.get("function.name") == "method1"

    # Clear spans for next test
    memory_exporter.clear()

    # Test method with exception
    with pytest.raises(ValueError) as exc_info:
        test_obj.method2()

    assert "Test class error" in str(exc_info.value)

    # Verify span for method2
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]

    assert span.attributes.get("function.status") == "error"
    assert span.attributes.get("error.type") == "ValueError"
    assert "Test class error" in span.attributes.get("error.message", "")


def test_traced_class_with_tracing_disabled():
    """Test traced_class decorator when tracing is disabled."""
    # Set tracing to disabled
    os.environ[_MSSDK_TRACE_VAR_NAME] = "false"
    memory_exporter.clear()

    # Define a test class
    @traced_class
    class TestClass:
        def method1(self, arg):
            return arg * 2

    # Test method execution without tracing
    test_obj = TestClass()
    result = test_obj.method1(5)

    assert result == 10

    # Verify no span was created
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 0
