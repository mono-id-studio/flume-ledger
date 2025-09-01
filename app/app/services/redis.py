from os import getenv
from redis import Redis, ConnectionPool
from redis.backoff import ExponentialBackoff
from redis.retry import Retry


class RedisService:
    host: str | None
    port: int | None
    db: int | None
    password: str | None
    pool: ConnectionPool | None
    client: Redis | None

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
        password: str | None = None,
    ):
        self.host = getenv("REDIS_HOST", "redis") if host is None else host
        self.port = int(getenv("REDIS_PORT", "6379")) if port is None else port
        self.db = int(getenv("REDIS_DB", "0")) if db is None else db
        self.password = (
            getenv("REDIS_PASSWORD") or None if password is None else password
        )
        self.pool = None
        self.client = None

    def get_url(self) -> str:
        if self.host is None or self.port is None or self.db is None:
            raise ValueError("Host, port and db are required")
        return f"redis://{':' + self.password + '@' if self.password else ''}{self.host}:{self.port}/{self.db}"

    def init_pool(
        self,
        decode_responses: bool = True,
        retry: Retry = Retry(ExponentialBackoff(), 3),
        socket_connect_timeout: int = 2,
        socket_timeout: int = 2,
    ) -> ConnectionPool:
        return ConnectionPool.from_url(
            self.get_url(),
            decode_responses=decode_responses,
            retry=retry,
            socket_connect_timeout=socket_connect_timeout,
            socket_timeout=socket_timeout,
        )

    def init(self) -> "RedisService":
        self.pool = self.init_pool()
        self.client = Redis(connection_pool=self.pool)
        return self

    def get_redis(self) -> Redis:
        return self.client if self.client else self.init().client

    def ping(self) -> bool:
        return self.get_redis().ping()

    def set(self, key: str, value: str, ttl_sec: int | None = None) -> bool:
        return self.get_redis().set(name=key, value=value, ex=ttl_sec)

    def get(self, key: str) -> str | None | bytes:
        return self.get_redis().get(key)
