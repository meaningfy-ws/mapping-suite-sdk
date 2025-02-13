import atexit
from functools import wraps
from typing import Any, Callable, Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode


class Tracer:
    """
    Singleton tracer class for OpenTelemetry integration with optional console output.
    """
    _instance = None
    _initialized = False
    _tracer = None
    _provider = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def _ensure_initialized(cls, print_on_console: bool = False) -> None:
        """
        Initialize the tracer with basic configuration.
        """
        if not cls._initialized:
            # Create a resource with service info
            resource = Resource.create({
                "service.name": "mapping-suite-sdk",
            })

            # Set up the tracer provider with the resource
            cls._provider = TracerProvider(resource=resource)

            # Add console processor if requested
            if print_on_console:
                console_exporter = ConsoleSpanExporter()
                cls._provider.add_span_processor(SimpleSpanProcessor(console_exporter))

            # Set the global tracer provider
            trace.set_tracer_provider(cls._provider)

            # Get the tracer
            cls._tracer = trace.get_tracer(__name__)
            cls._initialized = True

            # Register shutdown handler
            atexit.register(cls.shutdown)
        elif print_on_console and not any(
                isinstance(processor.exporter, ConsoleSpanExporter)
                for processor in cls._provider.span_processors
        ):
            # Add console processor if it wasn't added before
            console_exporter = ConsoleSpanExporter()
            cls._provider.add_span_processor(SimpleSpanProcessor(console_exporter))

    @classmethod
    def shutdown(cls) -> None:
        """
        Shutdown the tracer provider properly.
        """
        if cls._provider:
            cls._provider.shutdown()
            cls._initialized = False
            cls._tracer = None
            cls._provider = None

    @classmethod
    def trace(cls, name: Optional[str] = None, *, print_on_console: bool = False) -> Callable:
        """
        Decorator for tracing methods with optional console output.

        Args:
            name: Optional name for the span. If not provided, the method name will be used.
            print_on_console: Whether to print trace information to console. Defaults to False.

        Returns:
            Callable: Decorated function with tracing.
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                cls._ensure_initialized(print_on_console)
                operation_name = name or func.__name__

                with cls._tracer.start_as_current_span(operation_name) as span:
                    try:
                        # Add attributes to the span
                        span.set_attribute("function.name", func.__name__)
                        span.set_attribute("function.args_length", len(args))
                        span.set_attribute("function.kwargs_length", len(kwargs))

                        # Execute the function
                        result = func(*args, **kwargs)

                        # Add success attributes
                        span.set_attribute("function.status", "success")
                        span.set_status(Status(StatusCode.OK))

                        return result
                    except Exception as e:
                        # Add error attributes
                        span.set_attribute("function.status", "error")
                        span.set_attribute("error.type", e.__class__.__name__)
                        span.set_attribute("error.message", str(e))
                        span.set_status(Status(StatusCode.ERROR), str(e))
                        span.record_exception(e)
                        raise

            return wrapper

        return decorator
