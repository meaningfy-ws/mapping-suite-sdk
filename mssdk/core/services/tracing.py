from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from functools import wraps


def setup_tracing():
    trace.set_tracer_provider(
        TracerProvider(
            resource=Resource.create({"service.name": "mapping-suite-sdk"})
        )
    )
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(ConsoleSpanExporter())
    )


tracer = trace.get_tracer(__name__)

# Decorator for tracing methods
def trace_method(name=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation_name = name or func.__name__
            with tracer.start_as_current_span(operation_name) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR), str(e))
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator