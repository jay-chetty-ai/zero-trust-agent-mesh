import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.aiohttp_server import AioHttpServerInstrumentor

_INITIALIZED = False

def setup_tracing(service_name: str):
    """
    Initializes OpenTelemetry tracing with a Console Exporter.
    """
    global _INITIALIZED
    if _INITIALIZED:
        return
    _INITIALIZED = True
    # 1. Resource Attributes (Identify the service)
    resource = Resource.create({
        "service.name": service_name,
    })

    # 2. Set up Tracer Provider
    provider = TracerProvider(resource=resource)
    
    # 3. No Export for now (Logs carry the IDs)
    # We could add an OTLP exporter here later.
    
    # 4. Set Global Trace Provider
    trace.set_tracer_provider(provider)

    # 5. Instrument Logging
    # This adds trace_id and span_id to the log records
    LoggingInstrumentor().instrument(set_logging_format=False)
    
    log_format = (
        "%(asctime)s %(levelname)s [service.name=%(service_name)s] "
        "[trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] "
        "[%(name)s] %(message)s"
    )
    
    # Note: opentelemetry-instrumentation-logging uses these magic names
    # for the injected fields in the record.
    
    class ServiceNameFilter(logging.Filter):
        def __init__(self, name):
            self.service_name = name
        def filter(self, record):
            record.service_name = self.service_name
            return True

    for handler in logging.root.handlers:
        handler.addFilter(ServiceNameFilter(service_name))
        handler.setFormatter(logging.Formatter(log_format))
    
    if not logging.root.handlers:
        logging.basicConfig(level=logging.INFO, format=log_format)
        logging.root.handlers[0].addFilter(ServiceNameFilter(service_name))

    # 6. Instrument aiohttp (Server & Client)
    AioHttpServerInstrumentor().instrument()
    AioHttpClientInstrumentor().instrument()

    logging.info(f"OpenTelemetry Tracing initialized for '{service_name}'")

def get_tracer(name: str):
    return trace.get_tracer(name)
