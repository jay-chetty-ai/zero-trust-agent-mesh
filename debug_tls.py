
import logging
import ssl
import aiohttp
import asyncio
from src.common.spiffe import SpiffeHelper

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def main():
    spiffe = SpiffeHelper()
    spiffe.start()
    
    # Debug PEM
    bundle_set = spiffe.source.bundles
    pem = spiffe._bundle_to_pem(bundle_set)
    print(f"PEM Length: {len(pem)}")
    with open("bundle.pem", "w") as f:
        f.write(pem)
    print("Wrote bundle.pem")
    
    context = spiffe.get_client_ssl_context()
    
    url = "https://researcher:8080/ask"
    print(f"Connecting to {url}...")
    
    payload = {"query": "Quantum", "user_id": "test_user"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, ssl=context) as response:
                print(f"Response Status: {response.status}")
                text = await response.text()
                print(f"Response: {text}")
    except Exception as e:
        print(f"Connection Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
