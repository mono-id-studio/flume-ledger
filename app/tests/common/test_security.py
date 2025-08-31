from app.common.default.security import token_to_bytes


def test_token_to_bytes():
    """
    Tests the token_to_bytes function.
    """
    token = "base64:MTIz"
    assert token_to_bytes(token) == b"123"
    token = "123"
    assert token_to_bytes(token) == b"123"
