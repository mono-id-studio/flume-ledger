from base64 import b64decode


def token_to_bytes(token: str) -> bytes:
    if token.startswith("base64:"):
        return b64decode(token.split(":", 1)[1])
    return token.encode("utf-8")
