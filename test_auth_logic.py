from src.common.auth import JWTManager
import json

def test_jwt_flow():
    print("Testing JWTManager...")
    
    # 1. Test Key Generation
    priv, pub = JWTManager.generate_keypair()
    assert "BEGIN PRIVATE KEY" in priv
    assert "BEGIN PUBLIC KEY" in pub
    print("✓ RSA Keypair Generation successful")

    # 2. Test Token Creation
    mgr = JWTManager(private_key_pem=priv, public_key_pem=pub)
    token = mgr.create_token("user_123", "test@example.org")
    assert token is not None
    assert len(token.split('.')) == 3
    print("✓ JWT Signing successful")

    # 3. Test JWKS
    jwks = mgr.get_jwks()
    assert "keys" in jwks
    assert jwks["keys"][0]["kid"] == "mesh-key-1"
    print("✓ JWKS Export successful")
    print(json.dumps(jwks, indent=2))

    # 4. Test Verification
    claims = mgr.verify_token(token)
    assert claims["sub"] == "user_123"
    assert claims["iss"] == "frontend.mesh.local"
    print("✓ JWT Verification successful")

if __name__ == "__main__":
    try:
        test_jwt_flow()
        print("\nALL AUTH TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)
