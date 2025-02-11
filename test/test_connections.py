import asyncio
from openai import AsyncOpenAI
import redis
from configs.openai_setting import get_openai_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_openai_connection():
    """OpenAI API 연결 테스트"""
    settings = get_openai_settings()
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        logger.info("OpenAI API 연결 테스트 시작...")
        # 간단한 API 호출로 연결 테스트
        response = await client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        logger.info("OpenAI API 연결 성공!")
        logger.info(f"응답: {response.choices[0].message.content}")
        return True
    except Exception as e:
        logger.error(f"OpenAI API 연결 실패: {str(e)}")
        return False


def test_redis_connection():
    """Redis 연결 테스트"""
    settings = get_openai_settings()
    if not settings.REDIS_URL:
        logger.error("Redis URL이 설정되지 않았습니다.")
        return False

    try:
        logger.info("Redis 연결 테스트 시작...")
        redis_client = redis.from_url(settings.REDIS_URL)
        # ping으로 연결 테스트
        response = redis_client.ping()
        if response:
            logger.info("Redis 연결 성공!")

            # 간단한 읽기/쓰기 테스트
            test_key = "test_connection"
            test_value = "test_successful"
            redis_client.setex(test_key, 60, test_value)  # 60초 후 만료
            read_value = redis_client.get(test_key)

            if read_value.decode('utf-8') == test_value:
                logger.info("Redis 읽기/쓰기 테스트 성공!")
            else:
                logger.error("Redis 읽기/쓰기 테스트 실패!")

            # 테스트 키 삭제
            redis_client.delete(test_key)
            return True
    except redis.RedisError as e:
        logger.error(f"Redis 연결 실패: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")
        return False


async def main():
    """모든 연결 테스트 실행"""
    logger.info("=== 연결 테스트 시작 ===")

    # OpenAI API 테스트
    openai_success = await test_openai_connection()
    logger.info(f"OpenAI API 테스트 결과: {'성공' if openai_success else '실패'}")

    # Redis 테스트
    redis_success = test_redis_connection()
    logger.info(f"Redis 테스트 결과: {'성공' if redis_success else '실패'}")

    logger.info("=== 연결 테스트 완료 ===")

    return openai_success and redis_success


if __name__ == "__main__":
    asyncio.run(main())