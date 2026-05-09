"""Shared pytest fixtures."""
import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setnx = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def mock_es():
    es = AsyncMock()
    es.ping = AsyncMock(return_value=True)
    return es
