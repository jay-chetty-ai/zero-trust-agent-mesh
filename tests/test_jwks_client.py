import asyncio
import aiohttp
import logging
from src.common.spiffe import SpiffeHelper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-jwks")

async def test_jwks():
    spiffe = SpiffeHelper()
    spiffe.start()
    
    url = "https://frontend:8080/debug/jwks"
    ssl_context = spiffe.get_client_ssl_context()
    
    logger.info(f"Calling JWKS at {url}...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=ssl_context) as resp:
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print("JWKS Data:")
                    import json
                    print(json.dumps(data, indent=2))
                else:
                    print(f"Error: {await resp.text()}")
    except Exception as e:
        print(f"Failed to call JWKS: {e}")

if __name__ == "__main__":
    asyncio.run(test_jwks())
