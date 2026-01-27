import asyncio
import aiohttp
import json
import logging
from src.common.spiffe import SpiffeHelper
from src.common.auth import JWTManager

logging.basicConfig(level=logging.INFO)

async def run():
    spiffe = SpiffeHelper()
    spiffe.start()
    
    # Load the keys the mesh is using
    with open("/tmp/mesh_keys.json", "r") as f:
        keys = json.load(f)
        jwt_mgr = JWTManager(private_key_pem=keys["priv"], public_key_pem=keys["pub"])
    
    # Create a token for Alice
    token = jwt_mgr.create_token("user_alice", "alice@example.org")
    print(f"Generated Token: {token[:20]}...")

    # Call Researcher
    url = "https://researcher:8080/ask"
    ssl_context = spiffe.get_client_ssl_context()
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "query": "Is Zero Trust better than Perimeter Security?"
    }
    
    print(f"Calling Researcher at {url}...")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, ssl=ssl_context, headers=headers) as resp:
            print(f"Status: {resp.status}")
            data = await resp.json()
            if "content" in data:
                print("--- Signed Content ---")
                print(json.dumps(data["content"], indent=2))
                print(f"Signature Found: {data['signature'][:50]}...")
            else:
                print("Response Payload:")
                print(json.dumps(data, indent=2))

if __name__ == "__main__":
    asyncio.run(run())
