from __future__ import annotations

import base64
import hashlib

import bcrypt

# passlib 1.7.x is incompatible with bcrypt ≥4.1 (removed __about__, strict 72-byte limit).
# We use bcrypt directly and SHA-256-stretch the secret so it never exceeds 72 bytes.


def _stretch(plain: str) -> bytes:
    """SHA-256 + base64 so bcrypt always receives exactly 44 bytes."""
    return base64.b64encode(hashlib.sha256(plain.encode()).digest())


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return bcrypt.hashpw(_stretch(plain), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if the plain-text password matches the stored hash."""
    return bcrypt.checkpw(_stretch(plain), hashed.encode())
