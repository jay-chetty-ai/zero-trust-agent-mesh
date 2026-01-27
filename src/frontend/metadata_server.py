import asyncio
import logging
import os
import json
from aiohttp import web
from src.common.spiffe import SpiffeHelper
from src.common.auth import JWTManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metadata-server")

async def run_server():
    # Initialize SPIFFE
    spiffe = SpiffeHelper()
    spiffe.start()
    
    # Initialize/Load Keys
    key_path = "/tmp/mesh_keys.json"
    if not os.path.exists(key_path):
        logger.info("Generating new Mesh RSA Keypair...")
        priv, pub = JWTManager.generate_keypair()
        with open(key_path, "w") as f:
            json.dump({"priv": priv, "pub": pub}, f)
    else:
        logger.info("Loading existing Mesh RSA Keypair...")
        with open(key_path, "r") as f:
            keys = json.load(f)
            priv, pub = keys["priv"], keys["pub"]

    jwt_manager = JWTManager(private_key_pem=priv, public_key_pem=pub)
    
    # Share the public key for the app (optional if they read the same file)
    with open("/tmp/mesh_jwks.json", "w") as f:
        json.dump(jwt_manager.get_jwks(), f)

    app = web.Application()
    
    async def handle_jwks(request):
        return web.json_response(jwt_manager.get_jwks())

    async def handle_health(request):
        return web.json_response({"status": "healthy"})

    app.router.add_get('/debug/jwks', handle_jwks)
    app.router.add_get('/health', handle_health)
    
    ssl_context = spiffe.get_server_ssl_context()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080, ssl_context=ssl_context)
    await site.start()
    
    logger.info("Metadata Server (JWKS) started on port 8080 (mTLS)")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(run_server())
