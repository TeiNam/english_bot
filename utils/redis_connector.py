# utils/redis_connector.py
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import redis

logger = logging.getLogger(__name__)


class RedisConnector:
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

    def _json_serial(self, obj: Any) -> str:
        """datetime 객체를 JSON으로 직렬화"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def get(self, key: str) -> Optional[Dict]:
        """캐시에서 값을 조회"""
        if not self.is_available:
            return None
        try:
            data = self._redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            return None

    def set(self, key: str, value: Dict, ttl: Optional[int] = None) -> bool:
        """캐시에 값을 저장"""
        if not self.is_available:
            return False
        try:
            self._redis.setex(
                key,
                ttl or self.ttl,
                json.dumps(value, default=self._json_serial)
            )
            return True
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """캐시에서 값을 삭제"""
        if not self.is_available:
            return False
        try:
            self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {str(e)}")
            return False

    def delete_pattern(self, pattern: str) -> bool:
        """패턴에 매칭되는 모든 키 삭제"""
        if not self.is_available:
            return False
        try:
            keys = self._redis.keys(pattern)
            if keys:
                self._redis.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Redis delete pattern error: {str(e)}")
            return False
