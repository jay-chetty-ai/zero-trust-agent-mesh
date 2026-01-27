import asyncio
import aiohttp
import logging
import sys
import time
from src.common.spiffe import SpiffeHelper
from src.common.auth import JWTManager

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("attacker")

async def run_attack_simulation():
    print("\n💀 STARTING ZERO TRUST ATTACK SIMULATION 💀")
    print("==============================================")
    
    # 1. Acquire Valid Machine Identity (SPIFFE)
    # Even an attacker needs a valid SVID to get past the mTLS layer if they are 'inside' the perimeter.
    # We simulate a compromised service (e.g., the frontend) trying to do unauthorized things.
    print("\n[STEP 1] Acquiring Valid SPIFFE SVID (Compromised Service Identity)...")
    try:
        spiffe = SpiffeHelper()
        spiffe.start()
        print(f"✅ Acquired SVID: {spiffe.get_spiffe_id()}")
    except Exception as e:
        print(f"❌ Failed to get SVID: {e}")
        return

    # Target URL
    target_url = "https://researcher:8080/ask"
    
    # 2. Attack Case 1: The "Identity Stripping" Attack
    # We have mTLS (Machine Identity) but we strip the User Identity (JWT).
    # This simulates a service trying to act on its own without user delegation.
    print("\n[ATTACK 1] Sending Request WITHOUT User Context (JWT)...")
    print(f"   Target: {target_url}")
    print("   Method: POST")
    print("   Auth Header: <MISSING>")
    
    ssl_context = spiffe.get_client_ssl_context()
    payload = {"query": "What are the launch codes?", "user_id": "admin"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(target_url, json=payload, ssl=ssl_context) as resp:
                status = resp.status
                text = await resp.text()
                
                if status == 401 or status == 403:
                    print(f"🛡️  BLOCKED! Server responded with {status}.")
                    print(f"   Reason: {text}")
                    print("   >> SUCCESS: Mesh correctly rejected request without user context.")
                else:
                    print(f"❌ FAILED: Server accepted the request: {status}")
    except Exception as e:
        print(f"   Error: {e}")

    # 3. Attack Case 2: The "Imposter" Attack
    # We provide a JWT, but it's signed by US (the attacker), not the trusted Identity Provider.
    print("\n[ATTACK 2] Sending Request with FAKE (Self-Signed) JWT...")
    
    # Create a fake token
    from authlib.jose import jwt
    header = {'alg': 'RS256'}
    payload_fake = {'sub': 'admin_user', 'email': 'admin@hq.com', 'iat': int(time.time())}
    
    # We use a random key that the server DOES NOT trust
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    
    print("   Generating malicious RSA keypair...")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Sign the fake token
    fake_token = jwt.encode(header, payload_fake, private_pem).decode('utf-8')
    print(f"   Forged Token: {fake_token[:20]}...")
    
    headers = {"Authorization": f"Bearer {fake_token}"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(target_url, json=payload, ssl=ssl_context, headers=headers) as resp:
                status = resp.status
                text = await resp.text()
                
                if status == 401 or status == 403:
                    print(f"🛡️  BLOCKED! Server responded with {status}.")
                    print(f"   Reason: {text}")
                    print("   >> SUCCESS: Mesh correctly rejected forged identity.")
                else:
                    print(f"❌ FAILED: Server accepted the forged token: {status}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n==============================================")
    print("🏁 ATTACK SIMULATION COMPLETE")

if __name__ == "__main__":
    asyncio.run(run_attack_simulation())
