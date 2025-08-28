from typing import Protocol, cast
from jwt import encode, decode
from datetime import datetime, timedelta, UTC


class CustomUserProtocol(Protocol):
    def generate_jwt_token(self, user_id: int) -> str: ...

    def generate_refresh_jwt_token(self, user_id: int) -> str: ...

    def verify_jwt_token(self, token: str) -> dict: ...

    def verify_refresh_jwt_token(self, token: str) -> dict: ...


class CustomUserService:
    def __init__(
        self,
        jwt_secret_key: str,
        jwt_algorithm: str,
        jwt_expiration_time: int,
        jwt_refresh_expiration_time: int,
    ):
        self.jwt_secret_key = jwt_secret_key
        self.jwt_algorithm = jwt_algorithm
        self.jwt_expiration_time = jwt_expiration_time
        self.jwt_refresh_expiration_time = jwt_refresh_expiration_time

    def generate_jwt_token(self, user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "iat": int(datetime.now(tz=UTC).timestamp()),
            "exp": int(
                (
                    datetime.now(tz=UTC) + timedelta(seconds=self.jwt_expiration_time)
                ).timestamp()
            ),
            "type": "access",
        }

        return encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)

    def generate_refresh_jwt_token(self, user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "iat": int(datetime.now(tz=UTC).timestamp()),
            "exp": int(
                (
                    datetime.now(tz=UTC)
                    + timedelta(seconds=self.jwt_refresh_expiration_time)
                ).timestamp()
            ),
            "type": "refresh",
        }

        return encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)

    def verify_jwt_token(self, token: str) -> dict:
        return cast(
            dict,
            decode(token, self.jwt_secret_key, algorithms=[self.jwt_algorithm]),
        )

    def verify_refresh_jwt_token(self, token: str) -> dict:
        return cast(
            dict,
            decode(token, self.jwt_secret_key, algorithms=[self.jwt_algorithm]),
        )
