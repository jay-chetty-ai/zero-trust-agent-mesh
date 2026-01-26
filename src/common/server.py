import logging
import asyncio
import functools
from aiohttp import web
from src.common.spiffe import SpiffeHelper

logger = logging.getLogger(__name__)

class AgentServer:
    """
    Base class for an AI Agent Server.
    Runs an AIOHTTP service secured by SPIFFE mTLS.
    """
    
    def __init__(self, service_name, port=8080, spiffe_helper: SpiffeHelper = None):
        self.service_name = service_name
        self.port = port
        self.spiffe = spiffe_helper or SpiffeHelper()
        self.app = web.Application()
        self.routes = web.RouteTableDef()
        
        # Standard Health Check
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/debug/routes', self.debug_routes)
        
    async def health_check(self, request):
        return web.json_response({"status": "healthy", "service": self.service_name})

    async def debug_routes(self, request):
        routes_info = []
        for route in self.app.router.routes():
            routes_info.append({
                "method": route.method,
                "path": str(route.resource.get_info().get("path") or route.resource.get_info().get("formatter")),
                "handler": str(route.handler)
            })
        return web.json_response(routes_info)

    def run(self):
        """
        Starts the Async web server with mTLS.
        """
        # 1. Start SPIFFE Source (Get SVID)
        self.spiffe.start()
        
        # 2. Configure SSL Context for the Server
        # (Requires Client Certs)
        ssl_context = self.spiffe.get_server_ssl_context()
        
        # 3. Basic Middleware for Identity logging (simplified)
        # Real authz happens in specific handlers or middleware
        
        logger.info(f"Starting Secure Agent Server '{self.service_name}' on port {self.port}...")
        self.app.add_routes(self.routes)
        web.run_app(self.app, port=self.port, ssl_context=ssl_context)

    # Decorator to enforce caller identity
    def require_identity(self, allowed_ids):
        def decorator(handler):
            @functools.wraps(handler)
            async def wrapped(request):
                # Retrieve the peer cert from the transport
                transport = request.transport
                peercert = transport.get_extra_info('peercert')
                
                if not peercert:
                    # Should be impossible with ssl.CERT_REQUIRED but safety net
                    raise web.HTTPForbidden(text="No Client Certificate presented")

                try:
                    caller_id = self.spiffe.validate_spiffe_id(
                        peercert, 
                        allowed_spiffe_ids=allowed_ids
                    )
                    # Inject caller_id into request for logic to use
                    request['caller_id'] = caller_id
                except PermissionError as e:
                    logger.warning(f"Unauthorized access attempt: {e}")
                    raise web.HTTPForbidden(text=str(e))
                
                return await handler(request)
            return wrapped
        return decorator
