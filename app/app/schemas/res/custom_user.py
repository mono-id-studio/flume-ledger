from ninja import Schema


class LoginResponse(Schema):
    access_token: str
    refresh_token: str


class RefreshTokenResponse(Schema):
    access_token: str


class ProfileResponse(Schema):
    id: int
    email: str
    first_name: str
    last_name: str
    groups: list[str]
