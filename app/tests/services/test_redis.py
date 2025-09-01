import pytest

import os
from unittest import mock
from app.services.redis import RedisService


def test_redis_instance():
    with mock.patch.dict(
        os.environ, {"REDIS_HOST": "localhost", "REDIS_PORT": "6379", "REDIS_DB": "0"}
    ):
        redis = RedisService()
        assert redis.get_url() == "redis://localhost:6379/0"


def test_redis_instance_with_password():
    with mock.patch.dict(
        os.environ,
        {
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_DB": "0",
            "REDIS_PASSWORD": "password",
        },
    ):
        redis = RedisService()
        assert redis.get_url() == "redis://:password@localhost:6379/0"


def test_redis_instance_with_some_none():
    with mock.patch.dict(
        os.environ, {"REDIS_HOST": "localhost", "REDIS_PORT": "6379", "REDIS_DB": "0"}
    ):
        redis = RedisService()
        redis.host = None
        with pytest.raises(ValueError):
            redis.get_url()

        redis.host = "localhost"
        redis.port = None
        with pytest.raises(ValueError):
            redis.get_url()

        redis.port = 6379
        redis.db = None
        with pytest.raises(ValueError):
            redis.get_url()


def test_redis_init_with_args():
    """
    Tests that RedisService initializes correctly using arguments.
    """
    with mock.patch("app.services.redis.Redis"):
        redis = RedisService(host="arg_host", port=5678, db=2)
        redis.init()
        assert redis.host == "arg_host"
        assert redis.port == 5678
        assert redis.db == 2


def test_redis_ping():
    """
    Tests the ping method for both success and failure scenarios.
    """
    with mock.patch.dict(
        os.environ, {"REDIS_HOST": "localhost", "REDIS_PORT": "6379", "REDIS_DB": "0"}
    ):
        with mock.patch("app.services.redis.Redis") as mock_redis_class:
            mock_redis_instance = mock_redis_class.return_value

            # Test success case where ping returns True
            mock_redis_instance.ping.return_value = True

            redis_success = RedisService()
            redis_success.init()
            assert redis_success.ping() is True
            mock_redis_instance.ping.assert_called_once()

            # Test failure case where ping raises an exception
            RedisService._instance = None  # Force re-initialization of the singleton
            mock_redis_instance.ping.reset_mock()
            mock_redis_instance.ping.return_value = False

            redis_fail = RedisService()
            redis_fail.init()
            assert redis_fail.ping() is False
            mock_redis_instance.ping.assert_called_once()


def test_redis_set():
    """
    Tests the set method for both success and failure scenarios.
    """
    with mock.patch.dict(
        os.environ, {"REDIS_HOST": "localhost", "REDIS_PORT": "6379", "REDIS_DB": "0"}
    ):
        with mock.patch("app.services.redis.Redis") as mock_redis_class:
            mock_redis_instance = mock_redis_class.return_value

            # Test success case where set returns True
            mock_redis_instance.set.return_value = True

            redis_success = RedisService()
            redis_success.init()
            assert redis_success.set("test_key", "test_value") is True
            mock_redis_instance.set.assert_called_once()
            mock_redis_instance.set.reset_mock()

            # Test failure case where set returns False
            mock_redis_instance.set.return_value = False

            redis_fail = RedisService()
            redis_fail.init()
            assert redis_fail.set("test_key", "test_value") is False
            mock_redis_instance.set.assert_called_once()


def test_redis_get():
    """
    Tests the get method for both success and failure scenarios.
    """
    with mock.patch.dict(
        os.environ, {"REDIS_HOST": "localhost", "REDIS_PORT": "6379", "REDIS_DB": "0"}
    ):
        with mock.patch("app.services.redis.Redis") as mock_redis_class:
            mock_redis_instance = mock_redis_class.return_value

            # Test success case where get returns a string
            mock_redis_instance.get.return_value = "test_value"

            redis_success = RedisService()
            redis_success.init()
            assert redis_success.get("test_key") == "test_value"
            mock_redis_instance.get.assert_called_once()
            mock_redis_instance.get.reset_mock()

            # Test failure case where get returns None
            mock_redis_instance.get.return_value = None

            redis_fail = RedisService()
            redis_fail.init()
            assert redis_fail.get("test_key") is None
            mock_redis_instance.get.assert_called_once()
            mock_redis_instance.get.reset_mock()

            # Test failure case where get returns bytes
            mock_redis_instance.get.return_value = b"test_value"

            redis_fail = RedisService()
            redis_fail.init()
            assert redis_fail.get("test_key") == b"test_value"
            mock_redis_instance.get.assert_called_once()
