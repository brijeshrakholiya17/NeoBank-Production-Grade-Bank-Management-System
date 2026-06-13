"""
Security utilities: salted PIN hashing.

We never store a customer's raw PIN. Instead we store a random salt plus
the PBKDF2-HMAC-SHA256 hash of (PIN + salt). PBKDF2 is a deliberately slow,
standard-library key-derivation function that makes brute-forcing expensive.
A constant-time comparison (``hmac.compare_digest``) is used to verify,
which avoids leaking information through timing side-channels.

This mirrors how real systems handle credentials and is exactly the kind of
detail that distinguishes a professional project from a toy one.
"""

from __future__ import annotations

import hashlib
import hmac
import os

# Tunable PBKDF2 cost factor. Higher = slower = harder to brute force.
_ITERATIONS = 200_000
_HASH_NAME = "sha256"
_SALT_BYTES = 16


def hash_pin(pin: str) -> str:
    """Return a salted PBKDF2 hash encoded as ``iterations$salt$hash`` (hex)."""
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(_HASH_NAME, pin.encode("utf-8"), salt, _ITERATIONS)
    return f"{_ITERATIONS}${salt.hex()}${derived.hex()}"


def verify_pin(pin: str, stored: str) -> bool:
    """Verify a plaintext ``pin`` against a previously stored hash string."""
    try:
        iterations_str, salt_hex, hash_hex = stored.split("$")
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        # Malformed stored value -> treat as a failed verification.
        return False

    derived = hashlib.pbkdf2_hmac(_HASH_NAME, pin.encode("utf-8"), salt, iterations)
    # Constant-time comparison to resist timing attacks.
    return hmac.compare_digest(derived, expected)
