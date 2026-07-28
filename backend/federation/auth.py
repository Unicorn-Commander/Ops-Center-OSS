"""
Federation Node Authentication — Zero Trust

Each node has a unique node_id and signs its requests with a JWT.
Receiving nodes verify the JWT signature.

Two modes (configured via FEDERATION_AUTH_MODE env var):
1. "shared_key" (default, backward compatible) — all nodes share one secret key,
   JWTs are signed with HMAC-SHA256 using the shared key
2. "node_keys" — each node has its own signing key, public keys exchanged during registration

In both modes, every request includes a JWT with:
- iss: the sending node's node_id
- sub: the target node's node_id (or "*" for broadcast)
- iat: issued at timestamp
- exp: expiration (short-lived, 60 seconds)
- jti: unique request ID (replay prevention)

This replaces the raw "X-Federation-Key" / "Authorization: Bearer" shared secret pattern.
"""

import os
import time
import uuid
import hmac
import hashlib
import json
import base64
import logging
from typing import Optional, Dict, Tuple

logger = logging.getLogger("federation.auth")


class FederationAuth:
    """Handles JWT creation and verification for node-to-node auth."""

    def __init__(self):
        self.auth_mode = os.getenv("FEDERATION_AUTH_MODE", "shared_key")
        self.shared_key = os.getenv("FEDERATION_KEY", "") or os.getenv(
            "FEDERATION_SHARED_SECRET", ""
        )
        self.node_id = os.getenv("FEDERATION_NODE_ID", "unknown")
        self.token_ttl = 60  # seconds

        # For node_keys mode: store peer public keys (populated during registration)
        self.peer_keys: Dict[str, str] = {}  # {node_id: key}

        # Replay prevention: set of recently seen JTIs
        self._seen_jtis: set = set()
        self._jti_cleanup_time = time.time()

    def create_token(self, target_node: str = "*") -> str:
        """Create a signed JWT for authenticating to a peer node."""
        now = int(time.time())
        jti = uuid.uuid4().hex[:16]

        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "iss": self.node_id,  # who is sending
            "sub": target_node,  # who it's for
            "iat": now,  # issued at
            "exp": now + self.token_ttl,  # expires
            "jti": jti,  # unique ID (replay prevention)
        }

        signing_key = self._get_signing_key()

        header_b64 = self._b64encode(json.dumps(header))
        payload_b64 = self._b64encode(json.dumps(payload))

        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            signing_key.encode(), message.encode(), hashlib.sha256
        ).digest()
        sig_b64 = self._b64encode_bytes(signature)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Verify a JWT from a peer node.

        Returns: (is_valid, payload_dict, error_message)
        """
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return False, None, "Invalid token format"

            header_b64, payload_b64, sig_b64 = parts

            # Decode payload
            payload = json.loads(self._b64decode(payload_b64))

            # Check expiration
            now = int(time.time())
            if payload.get("exp", 0) < now:
                return False, None, "Token expired"

            # Check issued-at isn't too far in the future (clock skew tolerance: 30s)
            if payload.get("iat", 0) > now + 30:
                return False, None, "Token issued in the future"

            # Replay prevention
            jti = payload.get("jti", "")
            if jti in self._seen_jtis:
                return False, None, "Token already used (replay detected)"

            # Verify signature
            issuer = payload.get("iss", "")
            signing_key = self._get_verification_key(issuer)

            message = f"{header_b64}.{payload_b64}"
            expected_sig = hmac.new(
                signing_key.encode(), message.encode(), hashlib.sha256
            ).digest()
            actual_sig = self._b64decode_bytes(sig_b64)

            if not hmac.compare_digest(expected_sig, actual_sig):
                return False, None, "Invalid signature"

            # Track JTI for replay prevention
            self._seen_jtis.add(jti)
            self._cleanup_jtis()

            return True, payload, None

        except Exception as e:
            return False, None, f"Token verification failed: {e}"

    def get_auth_headers(self, target_node: str = "*") -> Dict[str, str]:
        """Get auth headers to include in requests to a peer."""
        token = self.create_token(target_node)
        return {
            "Authorization": f"Bearer {token}",
            "X-Federation-Node": self.node_id,
        }

    def register_peer_key(self, node_id: str, key: str):
        """Register a peer's signing key (for node_keys mode)."""
        self.peer_keys[node_id] = key
        logger.info("Registered signing key for peer: %s", node_id)

    def _get_signing_key(self) -> str:
        """Get the key to sign outgoing tokens."""
        if self.auth_mode == "node_keys":
            # In node_keys mode, each node has its own key
            return os.getenv("FEDERATION_NODE_KEY", self.shared_key)
        return self.shared_key

    def _get_verification_key(self, issuer_node_id: str) -> str:
        """Get the key to verify incoming tokens from a specific node."""
        if self.auth_mode == "node_keys" and issuer_node_id in self.peer_keys:
            return self.peer_keys[issuer_node_id]
        return self.shared_key

    def _cleanup_jtis(self):
        """Periodically clean old JTIs to prevent memory growth."""
        now = time.time()
        if now - self._jti_cleanup_time > 120:  # every 2 minutes
            self._seen_jtis.clear()  # safe because tokens expire after 60s
            self._jti_cleanup_time = now

    @staticmethod
    def _b64encode(data: str) -> str:
        return base64.urlsafe_b64encode(data.encode()).rstrip(b"=").decode()

    @staticmethod
    def _b64encode_bytes(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    @staticmethod
    def _b64decode(data: str) -> str:
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data).decode()

    @staticmethod
    def _b64decode_bytes(data: str) -> bytes:
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data)


def verify_federation_request(request) -> Tuple[bool, Optional[str], Optional[str]]:
    """Verify a federation request — supports both old shared key and new JWT.

    Returns: (is_valid, node_id, error_message)
    """
    auth = get_federation_auth()

    # Try Authorization: Bearer header first (JWT or shared key)
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

        # Check if it looks like a JWT (has two dots)
        if token.count(".") == 2:
            valid, payload, error = auth.verify_token(token)
            if valid:
                return True, payload.get("iss", "unknown"), None
            return False, None, error

        # Fall back to shared key comparison (backward compatible)
        if auth.shared_key and hmac.compare_digest(token, auth.shared_key):
            node_id = request.headers.get("x-federation-node", "unknown")
            return True, node_id, None

    # Try X-Federation-Key header (old style)
    fed_key = request.headers.get("x-federation-key", "")
    if fed_key and auth.shared_key and hmac.compare_digest(fed_key, auth.shared_key):
        node_id = request.headers.get("x-federation-node", "unknown")
        return True, node_id, None

    # Try x-federation-secret header (another old style used by the router)
    fed_secret = request.headers.get("x-federation-secret", "")
    if fed_secret and auth.shared_key and hmac.compare_digest(
        fed_secret, auth.shared_key
    ):
        node_id = request.headers.get("x-federation-node", "unknown")
        return True, node_id, None

    # No federation key configured = open mode (for development)
    if not auth.shared_key:
        return True, request.headers.get("x-federation-node", "anonymous"), None

    return False, None, "No valid federation credentials provided"


# Module singleton
_auth: Optional[FederationAuth] = None


def get_federation_auth() -> FederationAuth:
    global _auth
    if _auth is None:
        _auth = FederationAuth()
    return _auth
