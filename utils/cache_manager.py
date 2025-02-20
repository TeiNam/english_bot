# utils/cache_manager.py
import json
import logging
from typing import Optional, Any

import redis

logger = logging.getLogger(__name__)


class CacheManager:
    def __init__(self, redis_url: Optional[str] = None, ttl: int = 3600):
        self.redis_url = redis_url
        self.ttl = ttl
        self._redis = None
        self._is_available = False

        if self.redis_url:
            try:
                self._redis = redis.from_url(self.redis_url)
                self._redis.ping()
                self._is_available = True
                logger.info("Redis cache initialized successfully")
            except redis.RedisError as e:
                logger.warning(f"Failed to initialize Redis cache: {str(e)}")
                self._is_available = False

    @property
    def is_available(self) -> bool:
        return self._is_available

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값을 조회"""
        if not self.is_available:
            return None

        try:
            data = self._redis.get(key)
            return json.loads(data) if data else None
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Cache get error: {str(e)}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """캐시에 값을 저장"""
        if not self.is_available:
            return False

        try:
            ttl = ttl or self.ttl
            serialized = json.dumps(value)
            self._redis.setex(key, ttl, serialized)
            return True
        except (redis.RedisError, TypeError) as e:
            logger.error(f"Cache set error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """캐시에서 값을 삭제"""
        if not self.is_available:
            return False

        try:
            self._redis.delete(key)
            return True
        except redis.RedisError as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False

    def clear_pattern(self, pattern: str) -> bool:
        """패턴에 매칭되는 모든 키 삭제"""
        if not self.is_available:
            return False

        try:
            keys = self._redis.keys(pattern)
            if keys:
                self._redis.delete(*keys)
            return True
        except redis.RedisError as e:
            logger.error(f"Cache clear pattern error: {str(e)}")
            return False
