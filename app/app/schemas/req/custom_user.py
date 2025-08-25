from ninja import Schema


class LoginRequest(Schema):
    email: str
    password: str


class RefreshTokenRequest(Schema):
    refresh_token: str
