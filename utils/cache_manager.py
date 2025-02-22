# utils/cache_manager.py
import json
import logging
from datetime import datetime
from typing import Optional, Any, Dict, List, Union

import redis
from redis.client import Pipeline
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis 캐시 관리를 위한 통합 클래스

    다양한 데이터 유형을 지원하고 성능 최적화 및 확장성을 고려한 설계
    """

    def __init__(
            self,
            redis_url: Optional[str] = None,
            ttl: int = 3600,
            connection_pool_kwargs: Optional[Dict] = None,
            reconnect_attempts: int = 3,
            reconnect_delay: int = 1
    ):
        """
        캐시 매니저 초기화

        Args:
            redis_url: Redis 연결 URL
            ttl: 기본 캐시 만료 시간(초)
            connection_pool_kwargs: Redis 연결 풀 설정
            reconnect_attempts: 연결 재시도 횟수
            reconnect_delay: 재시도 간 딜레이(초)
        """
        self.redis_url = redis_url
        self.ttl = ttl
        self._redis = None
        self._is_available = False
        self._connection_pool_kwargs = connection_pool_kwargs or {}
        self._reconnect_attempts = reconnect_attempts
        self._reconnect_delay = reconnect_delay

        if self.redis_url:
            self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Redis 연결 초기화 및 재시도 로직"""
        attempts = 0

        while attempts < self._reconnect_attempts:
            try:
                self._redis = redis.from_url(
                    self.redis_url,
                    **self._connection_pool_kwargs
                )
                self._redis.ping()
                self._is_available = True
                logger.info("Redis cache initialized successfully")
                break

            except RedisError as e:
                attempts += 1
                logger.warning(
                    f"Redis connection attempt {attempts}/{self._reconnect_attempts} "
                    f"failed: {str(e)}"
                )

                if attempts < self._reconnect_attempts:
                    import time
                    time.sleep(self._reconnect_delay)
                else:
                    logger.error("Failed to initialize Redis cache after multiple attempts")
                    self._is_available = False

    @property
    def is_available(self) -> bool:
        """Redis 연결 가능 여부"""
        return self._is_available

    @property
    def client(self) -> Optional[redis.Redis]:
        """Redis 클라이언트 인스턴스 반환"""
        return self._redis if self._is_available else None

    def _serialize(self, value: Any) -> str:
        """
        값을 JSON 문자열로 직렬화

        Args:
            value: 직렬화할 값

        Returns:
            직렬화된 JSON 문자열
        """
        return json.dumps(value, default=self._json_serializer)

    def _deserialize(self, data: Optional[bytes]) -> Optional[Any]:
        """
        바이트 데이터를 파이썬 객체로 역직렬화

        Args:
            data: 역직렬화할 바이트 데이터

        Returns:
            역직렬화된 파이썬 객체 또는 None
        """
        if data is None:
            return None

        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to deserialize data: {str(e)}")
            return None

    def _json_serializer(self, obj: Any) -> str:
        """
        기본 JSON 직렬화가 지원하지 않는 타입 처리

        Args:
            obj: 직렬화할 객체

        Returns:
            직렬화된 문자열
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값을 조회

        Args:
            key: 조회할 키

        Returns:
            저장된 값 또는 None
        """
        if not self.is_available:
            return None

        try:
            data = self._redis.get(key)
            return self._deserialize(data)
        except RedisError as e:
            logger.error(f"Cache get error for key '{key}': {str(e)}")
            return None

    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """
        여러 키의 값을 한 번에 조회

        Args:
            keys: 조회할 키 목록

        Returns:
            키-값 쌍의 딕셔너리
        """
        if not self.is_available or not keys:
            return {}

        try:
            result = self._redis.mget(keys)
            return {
                key: self._deserialize(value)
                for key, value in zip(keys, result)
                if value is not None
            }
        except RedisError as e:
            logger.error(f"Cache mget error: {str(e)}")
            return {}

    def set(
            self,
            key: str,
            value: Any,
            ttl: Optional[int] = None,
            nx: bool = False
    ) -> bool:
        """
        캐시에 값을 저장

        Args:
            key: 저장할 키
            value: 저장할 값
            ttl: 만료 시간(초), None이면 기본값 사용
            nx: True면 키가 없을 때만 저장

        Returns:
            저장 성공 여부
        """
        if not self.is_available:
            return False

        try:
            ttl_value = ttl if ttl is not None else self.ttl
            serialized = self._serialize(value)

            if nx:
                return bool(self._redis.set(key, serialized, ex=ttl_value, nx=True))
            else:
                return bool(self._redis.setex(key, ttl_value, serialized))
        except (RedisError, TypeError) as e:
            logger.error(f"Cache set error for key '{key}': {str(e)}")
            return False

    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        여러 키-값 쌍을 한 번에 저장

        Args:
            mapping: 키-값 쌍의 딕셔너리
            ttl: 만료 시간(초), None이면 기본값 사용

        Returns:
            저장 성공 여부
        """
        if not self.is_available or not mapping:
            return False

        try:
            ttl_value = ttl if ttl is not None else self.ttl

            # Pipeline 사용하여 원자적 작업 수행
            with self._redis.pipeline() as pipe:
                for key, value in mapping.items():
                    serialized = self._serialize(value)
                    pipe.setex(key, ttl_value, serialized)
                pipe.execute()
            return True
        except (RedisError, TypeError) as e:
            logger.error(f"Cache mset error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        캐시에서 값을 삭제

        Args:
            key: 삭제할 키

        Returns:
            삭제 성공 여부
        """
        if not self.is_available:
            return False

        try:
            self._redis.delete(key)
            return True
        except RedisError as e:
            logger.error(f"Cache delete error for key '{key}': {str(e)}")
            return False

    def delete_many(self, keys: List[str]) -> bool:
        """
        여러 키를 한 번에 삭제

        Args:
            keys: 삭제할 키 목록

        Returns:
            삭제 성공 여부
        """
        if not self.is_available or not keys:
            return False

        try:
            self._redis.delete(*keys)
            return True
        except RedisError as e:
            logger.error(f"Cache delete_many error: {str(e)}")
            return False

    def delete_pattern(self, pattern: str) -> bool:
        """
        패턴에 매칭되는 모든 키 삭제

        Args:
            pattern: 키 패턴(예: 'user:*')

        Returns:
            삭제 성공 여부
        """
        if not self.is_available:
            return False

        try:
            # scan_iter 사용하여 메모리 효율적으로 처리
            keys = list(self._redis.scan_iter(match=pattern))
            if keys:
                # 청크 단위로 나누어 대량의 키 처리
                chunk_size = 1000
                for i in range(0, len(keys), chunk_size):
                    chunk = keys[i:i + chunk_size]
                    self._redis.delete(*chunk)
            return True
        except RedisError as e:
            logger.error(f"Cache delete_pattern error for pattern '{pattern}': {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """
        키가 존재하는지 확인

        Args:
            key: 확인할 키

        Returns:
            키 존재 여부
        """
        if not self.is_available:
            return False

        try:
            return bool(self._redis.exists(key))
        except RedisError as e:
            logger.error(f"Cache exists error for key '{key}': {str(e)}")
            return False

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        키의 값을 증가

        Args:
            key: 증가시킬 키
            amount: 증가량

        Returns:
            증가 후 값 또는 None(실패 시)
        """
        if not self.is_available:
            return None

        try:
            return self._redis.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Cache incr error for key '{key}': {str(e)}")
            return None

    def expire(self, key: str, ttl: int) -> bool:
        """
        키의 만료 시간 설정

        Args:
            key: 대상 키
            ttl: 만료 시간(초)

        Returns:
            성공 여부
        """
        if not self.is_available:
            return False

        try:
            return bool(self._redis.expire(key, ttl))
        except RedisError as e:
            logger.error(f"Cache expire error for key '{key}': {str(e)}")
            return False

    def ttl(self, key: str) -> Optional[int]:
        """
        키의 남은 만료 시간 조회

        Args:
            key: 대상 키

        Returns:
            남은 시간(초) 또는 None(실패 시)
        """
        if not self.is_available:
            return None

        try:
            return self._redis.ttl(key)
        except RedisError as e:
            logger.error(f"Cache ttl error for key '{key}': {str(e)}")
            return None

    def pipeline(self) -> Optional[Pipeline]:
        """
        Redis 파이프라인 객체 반환

        Returns:
            Redis 파이프라인 또는 None(연결 불가 시)
        """
        if not self.is_available:
            return None

        try:
            return self._redis.pipeline()
        except RedisError as e:
            logger.error(f"Cache pipeline error: {str(e)}")
            return None

    def clear_all(self) -> bool:
        """
        모든 키 삭제 (주의: 위험한 작업)

        Returns:
            성공 여부
        """
        if not self.is_available:
            return False

        try:
            self._redis.flushdb()
            return True
        except RedisError as e:
            logger.error(f"Cache clear_all error: {str(e)}")
            return False

    def health_check(self) -> bool:
        """
        Redis 연결 상태 확인

        Returns:
            연결 정상 여부
        """
        if not self._redis:
            return False

        try:
            return bool(self._redis.ping())
        except RedisError:
            self._is_available = False
            return False