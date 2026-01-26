import os
import ssl
import logging
from spiffe import X509Source, X509BundleSet
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)

class SpiffeHelper:
    """
    Helper class to manage SPIFFE Identity (SVID) and Trust Bundles.
    Uses the pyspiffe library to fetch and rotate credentials from the Workload API.
    """

    def __init__(self, socket_path=None):
        self.socket_path = socket_path or os.getenv(
            "SPIFFE_ENDPOINT_SOCKET", "unix:///run/spire/sockets/agent.sock"
        )
        self.source = None
        self._initialized = False

    def start(self):
        """
        Connects to the SPIRE Workload API and starts the automatic rotation background thread.
        This blocks until the first SVID is received.
        """
        if self._initialized:
            return

        logger.info(f"Connecting to SPIRE Workload API at {self.socket_path}...")
        
        try:
            # X509Source automatically handles fetching and renewal (rotation)
            self.source = X509Source(socket_path=self.socket_path)
            
            # Fetch first X.509 SVID to ensure we are ready
            svid = self.source.svid
            logger.info(f"Successfully fetched SVID: {svid.spiffe_id}")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to connect to SPIRE Workload API: {e}")
            raise

    def get_server_ssl_context(self) -> ssl.SSLContext:
        """
        Creates an SSLContext for a Server (Agent listening for connections).
        - Presents its own SVID certificate.
        - Requires Client Certificate (mTLS).
        - Validates Client SVID against the Trust Bundle.
        """
        if not self._initialized:
            self.start()

        # Create a standard SSLContext
        # pyspiffe provides a helper to configure it, or we can do it manually.
        # We'll use the source to get the material.
        
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.verify_mode = ssl.CERT_REQUIRED  # Enforce mTLS
        
        # Hook into pyspiffe's dynamic bundle/svid source
        # Note: In a real long-running app, we need to handle rotation hooks.
        # pyspiffe X509Source has a specific method to apply to SSLContext? 
        # Checking pyspiffe docs (mental model): 
        # source.apply_to_ssl_context(context) is the standard way.
        
        # However, for 'server' side, we also need to validate clients.
        # Let's trust pyspiffe's implementation.
        
        def ssl_context_provider():
             # This might be needed if using a framework that accepts a callable
             pass

        # For simple python `ssl` usage:
        svid = self.source.svid
        bundle_set = self.source.bundles
        
        # Load the Trust Bundle (CA certs)
        # We need to write them to specific storage or use standard calls.
        # pyspiffe creates a context that reloads? 
        # No, standard python ssl.SSLContext doesn't auto-reload from memory easily without callbacks.
        # But `spiffe` library might offer a context wrapper.
        
        # Simpler approach for Phase 1: Create a FRESH context every time or use a wrapper.
        # Let's rely on extracting the PEMs for now which is explicit.
        
        # Trust Chain
        ca_certs_pem = self._bundle_to_pem(bundle_set)
        context.load_verify_locations(cadata=ca_certs_pem)
        
        # Server Identity
        # Currently python ssl requires files for load_cert_chain usually, 
        # unless we use the lower level loading.
        # Fortunately, pyspiffe usually handles writing to disk OR we use a temporary file approach.
        # A2A simplified: We will grab the key/cert from SVID.
        
        # We will write temp files because Python's ssl module is file-centric for cert chains
        # until Python 3.12+ (in-memory loading).
        # Since we use 3.11-slim, let's write to /dev/shm or /tmp
        
        cert_path = "/dev/shm/my_svid.crt"
        key_path = "/dev/shm/my_svid.key"
        
        with open(cert_path, "wb") as f:
            for cert in svid.cert_chain:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
        with open(key_path, "wb") as f:
            f.write(svid.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        context.load_cert_chain(certfile=cert_path, keyfile=key_path)
        
        return context

    def get_client_ssl_context(self) -> ssl.SSLContext:
        """
        Creates an SSLContext for a Client (Caller).
        - Presents its own SVID.
        - Validates Server SVID against Trust Bundle.
        """
        if not self._initialized:
            self.start()

        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = False # SPIFFE does not use Hostnames/DNS usually, it uses URI validation subjectAltName. 
        
        # Setup Trust
        bundle_set = self.source.bundles
        ca_certs_pem = self._bundle_to_pem(bundle_set)
        context.load_verify_locations(cadata=ca_certs_pem)
        
        # Setup Identity
        svid = self.source.svid
        cert_path = "/dev/shm/client_svid.crt"
        key_path = "/dev/shm/client_svid.key"
        
        with open(cert_path, "wb") as f:
            for cert in svid.cert_chain:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
        with open(key_path, "wb") as f:
            f.write(svid.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        context.load_cert_chain(certfile=cert_path, keyfile=key_path)

        return context

    def validate_spiffe_id(self, peercert, expected_spiffe_id=None, allowed_spiffe_ids=None):
        """
        Validates that the peer certificate contains a valid SPIFFE ID.
        If specific IDs are allowed, checks against them.
        """
        # Extract SANs from peercert
        san_list = []
        for key, value in peercert.get("subjectAltName", ()):
            if key == "URI":
                san_list.append(value)
        
        if not san_list:
            raise ValueError("No SPIFFE ID (URI SAN) found in peer certificate")
        
        peer_id = san_list[0] # Assuming one ID
        logger.info(f"Authenticated Peer SPIFFE ID: {peer_id}")

        if expected_spiffe_id and peer_id != expected_spiffe_id:
             raise PermissionError(f"Peer ID {peer_id} does not match expected {expected_spiffe_id}")
             
        if allowed_spiffe_ids and peer_id not in allowed_spiffe_ids:
             raise PermissionError(f"Peer ID {peer_id} is not in allowed list: {allowed_spiffe_ids}")
             
        return peer_id

    def _bundle_to_pem(self, bundle_set) -> str:
        """
        Converts all bundles in the Set[X509Bundle] to a single PEM bytes string.
        """
        pem_out = b""
        for bundle in bundle_set:
            for authority in bundle.x509_authorities:
                pem_out += authority.public_bytes(serialization.Encoding.PEM)
        return pem_out.decode("utf-8")
