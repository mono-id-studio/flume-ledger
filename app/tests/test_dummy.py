import pytest  # noqa: F401

from app.services.custom_user import CustomUserService  # noqa: F401


def test_generate_jwt_token() -> None:
    print("=== JWT Token Generation Test ===")

    user_service: CustomUserService = CustomUserService(
        jwt_secret_key="asdrubale1",
        jwt_algorithm="HS256",
        jwt_expiration_time=10,
        jwt_refresh_expiration_time=10,
    )
    print("User service configured with algorithm: HS256, expiration: 10s")

    user_id = 1
    print(f"Generating JWT token for user ID: {user_id}")

    token = user_service.generate_jwt_token(user_id)

    assert token is not None
    assert token != ""

    print(f"Generated token: {token}")
    print(f"Token length: {len(token)} characters")

    # JWT tokens have 3 parts separated by dots
    token_parts = token.split(".")
    print(f"Token parts count: {len(token_parts)} (expected: 3 for JWT)")
    print(f"Header length: {len(token_parts[0]) if len(token_parts) > 0 else 0}")
    print(f"Payload length: {len(token_parts[1]) if len(token_parts) > 1 else 0}")
    print(f"Signature length: {len(token_parts[2]) if len(token_parts) > 2 else 0}")
    print("=== Test completed successfully ===")


def test_verify_jwt_token() -> None:
    print("=== JWT Token Verification Test ===")

    user_service: CustomUserService = CustomUserService(
        jwt_secret_key="asdrubale1",
        jwt_algorithm="HS256",
        jwt_expiration_time=10,
        jwt_refresh_expiration_time=10,
    )
    print("User service configured with algorithm: HS256, expiration: 10s")

    token = user_service.generate_jwt_token(1)
    print(f"Verifying token: {token}")

    payload = user_service.verify_jwt_token(token)
    print(f"Verified payload: {payload}")
    print("=== Test completed successfully ===")
