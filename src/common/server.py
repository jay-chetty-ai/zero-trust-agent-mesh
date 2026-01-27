import logging
import asyncio
import functools
import aiohttp
from aiohttp import web
from src.common.spiffe import SpiffeHelper
from src.common.auth import JWTManager
from src.common.tracing import setup_tracing

logger = logging.getLogger(__name__)

class AgentServer:
    """
    Base class for an AI Agent Server.
    Runs an AIOHTTP service secured by SPIFFE mTLS.
    """
    
    def __init__(self, service_name, port=8080, spiffe_helper: SpiffeHelper = None):
        self.service_name = service_name
        self.port = port
        
        # Initialize Observability (OTEL)
        setup_tracing(service_name)
        
        self.spiffe = spiffe_helper or SpiffeHelper()
        self.app = web.Application()
        self.routes = web.RouteTableDef()
        
        # JWT Management (Human Identity)
        self.jwt_manager = JWTManager()
        self.jwks_url = "https://frontend:8080/debug/jwks"
        
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

    async def refresh_jwks(self):
        """Fetches the Public Keys from the Frontend Gateway (via mTLS)"""
        logger.info(f"Refreshing JWKS from {self.jwks_url}...")
        ssl_context = self.spiffe.get_client_ssl_context()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.jwks_url, ssl=ssl_context) as resp:
                    if resp.status == 200:
                        jwks = await resp.json()
                        # Simple logic: extract first key and convert to PEM
                        # In a multi-key setup, we'd use Kid.
                        from authlib.jose import jwk
                        public_key = jwk.loads(jwks)
                        
                        # Convert to PEM for the JWTManager
                        pem = public_key.as_pem().decode()
                        
                        self.jwt_manager.public_key = pem
                        logger.info("✓ JWKS refreshed and Public Key cached.")
                    else:
                        logger.error(f"Failed to fetch JWKS: {resp.status} {await resp.text()}")
        except Exception as e:
            logger.error(f"Error fetching JWKS: {e}")

    def run(self):
        """
        Starts the Async web server with mTLS.
        """
        # 1. Start SPIFFE Source (Get SVID)
        self.spiffe.start()
        
        # 1.1 Fetch JWKS (Initial sync)
        # We need to run this in a loop or before starting the server
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self.refresh_jwks())
        else:
            loop.run_until_complete(self.refresh_jwks())
        
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

    # New Decorator: Enforce User Context (JWT)
    def require_user_context(self, allowed_callers=None):
        """
        Decorator that requires:
        1. Valid SPIFFE Identity (mTLS) - Optional to specify which.
        2. Valid User Context (JWT) in Authorization Header.
        """
        def decorator(handler):
            # Chain the identity check first
            @self.require_identity(allowed_callers)
            @functools.wraps(handler)
            async def wrapped(request):
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    raise web.HTTPUnauthorized(text="Missing or invalid Authorization header")
                
                token = auth_header.split(" ")[1]
                
                try:
                    # Verify the token using our cached Public Key
                    user_context = self.jwt_manager.verify_token(token)
                    request['user_context'] = user_context
                    logger.info(f"Verified User Context: {user_context['sub']} ({user_context['email']})")
                except PermissionError as e:
                    logger.warning(f"User Authentication Failed: {e}")
                    raise web.HTTPUnauthorized(text=str(e))
                except Exception as e:
                    logger.error(f"Internal error during JWT verification: {e}")
                    # If we don't have a public key yet, try one more refresh
                    if not self.jwt_manager.public_key:
                        await self.refresh_jwks()
                        # Retry once
                        try:
                            user_context = self.jwt_manager.verify_token(token)
                            request['user_context'] = user_context
                        except:
                            raise web.HTTPUnauthorized(text="Identity Provider public key not available")
                    else:
                        raise web.HTTPUnauthorized(text="Session verification failed")

                return await handler(request)
            return wrapped
        return decorator

    def sign_response(self, data: dict) -> dict:
        """
        Signs the response payload using the Agent's SPIFFE SVID.
        Returns a wrapper containing the original data and a JWS signature.
        """
        from authlib.jose import JsonWebSignature
        jws = JsonWebSignature()
        import json

        # Prepare payload
        payload = json.dumps(data).encode('utf-8')
        
        # Prepare protected header with x5c (Certificate Chain)
        header = {
            "alg": self.spiffe.get_x509_algorithm(),
            "kid": self.spiffe.get_spiffe_id(),
            "x5c": self.spiffe.get_cert_chain_pems()
        }
        
        # Sign using private key object
        key = self.spiffe.get_private_key()
        signature_token = jws.serialize_compact(header, payload, key)
        
        return {
            "status": "success",
            "content": data,
            "signature": signature_token.decode() if isinstance(signature_token, bytes) else signature_token
        }
