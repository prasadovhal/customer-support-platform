from __future__ import annotations


import pytest

from app.core.exceptions import AuthenticationError
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.security.password import hash_password, verify_password


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
class TestPassword:
    def test_hash_and_verify_round_trip(self) -> None:
        plain = "MyS3cur3P@ssword!"
        hashed = hash_password(plain)
        assert hashed != plain
        assert verify_password(plain, hashed)

    def test_wrong_password_fails_verification(self) -> None:
        hashed = hash_password("correct-horse-battery-staple")
        assert not verify_password("wrong-password", hashed)

    def test_hashes_are_unique_for_same_input(self) -> None:
        plain = "same-password"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)
        # bcrypt produces a unique salt each time.
        assert hash1 != hash2
        # But both should verify against the original plain text.
        assert verify_password(plain, hash1)
        assert verify_password(plain, hash2)

    def test_empty_password_can_be_hashed_and_verified(self) -> None:
        hashed = hash_password("")
        assert verify_password("", hashed)
        assert not verify_password("not-empty", hashed)


# ---------------------------------------------------------------------------
# JWT — access token
# ---------------------------------------------------------------------------
class TestJWT:
    def test_create_and_decode_access_token(self) -> None:
        subject = "customer-uuid-001"
        scopes = ["customer:read", "customer:write"]
        token = create_access_token(
            subject=subject,
            token_type="customer",
            scopes=scopes,
            expire_minutes=15,
        )
        payload = decode_token(token)
        assert payload.sub == subject
        assert payload.type == "customer"
        assert "customer:read" in payload.scopes
        assert "customer:write" in payload.scopes

    def test_token_has_correct_issuer(self) -> None:
        token = create_access_token(
            subject="agent-001",
            token_type="agent",
            scopes=["approve:refunds"],
            expire_minutes=60,
        )
        payload = decode_token(token)
        assert payload.iss == "customer-support-api"

    def test_expired_token_raises_authentication_error(self) -> None:
        token = create_access_token(
            subject="customer-001",
            token_type="customer",
            scopes=[],
            expire_minutes=-1,  # already expired
        )
        with pytest.raises(AuthenticationError) as exc_info:
            decode_token(token)
        assert "expired" in exc_info.value.message.lower()

    def test_invalid_token_raises_authentication_error(self) -> None:
        with pytest.raises(AuthenticationError):
            decode_token("this.is.not.a.valid.jwt")

    def test_tampered_token_raises_authentication_error(self) -> None:
        token = create_access_token(
            subject="customer-001",
            token_type="customer",
            scopes=[],
            expire_minutes=15,
        )
        # Flip a character in the middle of the signature segment.
        # (Avoid the last char: base64 padding may make its low bits non-significant.)
        parts = token.split(".")
        signature = parts[2]
        mid = len(signature) // 2
        tampered_sig = signature[:mid] + ("A" if signature[mid] != "A" else "B") + signature[mid + 1 :]
        tampered_token = ".".join([parts[0], parts[1], tampered_sig])
        with pytest.raises(AuthenticationError):
            decode_token(tampered_token)

    def test_create_and_decode_refresh_token(self) -> None:
        token = create_refresh_token(subject="cust-999", token_type="customer")
        payload = decode_token(token)
        assert payload.sub == "cust-999"
        assert payload.type == "customer"
        # Refresh tokens have no scopes.
        assert payload.scopes == []
