import time
import logging
from authlib.jose import jwt, jwk
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

logger = logging.getLogger(__name__)

class JWTManager:
    """
    Handles JWT Creation (Signing) and Verification.
    """
    def __init__(self, private_key_pem=None, public_key_pem=None):
        self.private_key = private_key_pem
        self.public_key = public_key_pem
        self.issuer = "frontend.mesh.local"
        self.audience = "ai-agent-mesh"

    @classmethod
    def generate_keypair(cls):
        """Generates a new RSA keypair for the Mesh."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return private_pem.decode(), public_pem.decode()

    def create_token(self, user_id, email, scope="mesh:all"):
        """Signs a 1-hour JWT for the given user."""
        if not self.private_key:
            raise ValueError("Private key required for signing")

        now = int(time.time())
        payload = {
            "iss": self.issuer,
            "sub": user_id,
            "aud": self.audience,
            "iat": now,
            "exp": now + 3600,
            "email": email,
            "scope": scope
        }
        header = {"alg": "RS256", "typ": "JWT", "kid": "mesh-key-1"}
        
        token = jwt.encode(header, payload, self.private_key)
        return token.decode() if isinstance(token, bytes) else token

    def get_jwks(self):
        """Returns the public key in JWKS format."""
        if not self.public_key:
            raise ValueError("Public key required for JWKS")
        
        # Create a JWK from the PEM
        key = jwk.dumps(self.public_key, kty='RSA')
        key['kid'] = "mesh-key-1"
        key['use'] = 'sig'
        key['alg'] = 'RS256'
        
        return {"keys": [key]}

    def verify_token(self, token, public_key_pem=None):
        """Verifies the JWT signature and claims."""
        key = public_key_pem or self.public_key
        if not key:
            raise ValueError("Public key required for verification")

        try:
            claims = jwt.decode(token, key)
            claims.validate()
            return claims
        except Exception as e:
            logger.error(f"JWT Verification failed: {e}")
            raise PermissionError(f"Invalid Token: {e}")
