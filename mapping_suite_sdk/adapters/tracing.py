import functools

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider

MSSDK_TRACE = False
MSSDK_TRACER_PROVIDER = TracerProvider(resource=Resource(attributes={SERVICE_NAME: "mapping-suite-sdk"}))
trace.set_tracer_provider(MSSDK_TRACER_PROVIDER)


# Example of setting an exporter, like console exporter
# MSSDK_TRACER_PROVIDER.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))


def traced_routine(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if MSSDK_TRACE:
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

    return wrapper


def traced_class(cls):
    """
    Class decorator that applies tracing to all methods of a class.
    Similar to traced_routine but works on all methods of a class.
    """
    if MSSDK_TRACE:
        class_name = cls.__name__

        # Create a custom traced_routine specific for this class
        def class_traced_routine(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
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

            return wrapper

        for attr_name, attr_value in cls.__dict__.items():
            # Skip special methods and non-callable attributes
            if callable(attr_value) and not attr_name.startswith('__'):
                setattr(cls, attr_name, class_traced_routine(attr_value))

    return cls
